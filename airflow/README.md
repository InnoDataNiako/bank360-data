# 4. Airflow - Orchestration du pipeline

## Pourquoi ?

Les trois étapes précédentes (ingestion, transformation Spark, modélisation
dbt) ont été validées manuellement, une par une. En production, elles
doivent s'enchaîner automatiquement, dans le bon ordre, avec une visibilité
claire sur ce qui a réussi ou échoué - sans intervention humaine à 2h du
matin.

Airflow orchestre ce déroulement et donne un historique d'exécution
consultable, plutôt que des commandes lancées à la main dont on ne garde
pas de trace.

## Objectif

Automatiser l'enchaînement quotidien : vérification de l'environnement,
ingestion Bronze, transformation Silver, modélisation Gold.

## Architecture

```text
healthcheck_environment
    | (Postgres / MinIO / Nessie / Spark Thrift OK)
ingestion_postgres_to_bronze (SparkSubmitOperator)
    |
transformation_bronze_to_silver (SparkSubmitOperator)
    |
modeling_silver_to_gold (BashOperator -> docker exec bank360_dbt dbt run)
```

Les deux tâches Spark (`ingestion_postgres_to_bronze`,
`transformation_bronze_to_silver`) utilisent `SparkSubmitOperator` avec la
connexion Airflow `spark_default` (`spark://spark-master:7077`) : un vrai
`spark-submit` réseau depuis le conteneur Airflow vers le cluster Spark,
pas un `docker exec`.

Seule la dernière tâche, `modeling_silver_to_gold`, exécute un `docker exec
bank360_dbt dbt run` sur le conteneur `bank360_dbt` déjà en place, via le
socket Docker monté dans le conteneur Airflow (`/var/run/docker.sock`).

## Exécution

Le DAG `bank360_pipeline` tourne tous les jours à 2h du matin
(`schedule_interval="0 2 * * *"`), ou peut être déclenché manuellement
depuis l'UI (`http://localhost:8083`) ou en CLI :

```bash
docker exec -it bank360_airflow_scheduler airflow dags trigger bank360_pipeline
```

## Prérequis

- Les services `airflow-webserver` et `airflow-scheduler` doivent être
  démarrés (`docker compose up -d airflow-init airflow-webserver
  airflow-scheduler`) - à vérifier, ils ne le sont pas forcément par
  défaut au premier `docker compose up`.
- Le client Docker CLI doit être installé dans l'image Airflow (ajouté au
  `Dockerfile`), sans quoi la tâche `modeling_silver_to_gold` (seule tâche
  faisant du `docker exec`) échoue avec `docker: command not found`. Le
  socket seul ne suffit pas.
- **Le jar runtime Iceberg-Spark doit être présent dans `spark/jars/`** :
  `iceberg-spark-runtime-3.5_2.12-1.5.2.jar` (version alignée sur
  `iceberg-aws-bundle-1.5.2.jar`, déjà présent). Ce jar fournit la classe
  `org.apache.iceberg.spark.SparkCatalog` référencée dans
  `SPARK_JARS` du DAG. `iceberg-aws-bundle` seul ne suffit pas : il ne
  couvre que l'intégration S3, pas le catalogue Iceberg lui-même. Sans ce
  jar, `transformation_bronze_to_silver` plante immédiatement avec
  `ClassNotFoundException: org.apache.iceberg.spark.SparkCatalog`, avant
  de traiter la moindre table. Comme `spark/jars/` est monté en bind mount
  (`./spark/jars:/opt/spark/jars`), il suffit de placer le fichier dans ce
  dossier local pour qu'il soit visible dans tous les conteneurs.
- Les namespaces Iceberg `bronze` et `silver` doivent déjà exister (voir
  `ingestion/README.md`, sections 1 et 2) avant le premier run du DAG.

## Points d'attention

- **La tâche `healthcheck_environment` est volontairement la première du
  DAG, pas une option.** Vu la fragilité déjà rencontrée (réseau Docker
  désynchronisé, Thrift Server déconnecté du Master sans erreur explicite,
  jars manquants selon le conteneur), laisser le DAG foncer directement
  dans l'ingestion revient à découvrir la panne plusieurs tâches plus
  tard, avec un message d'erreur peu clair. Le healthcheck vérifie
  spécifiquement que le Thrift Server est **enregistré comme application
  active auprès du Spark Master** (`http://spark-master:8081/json/`,
  champ `activeapps`) - un simple test "le port 10000 répond" ne suffit
  pas, puisque c'est justement le cas de panne observé où le port reste
  ouvert alors que l'app n'est plus reconnue.

- **Permissions sur `/var/run/docker.sock`.** L'utilisateur `airflow` du
  conteneur (uid 50000, groupe `root`) n'a par défaut pas les droits sur
  le socket monté, qui appartient au groupe Docker de l'hôte (GID variable
  selon la machine, ex. `984`). Symptôme : la tâche `modeling_silver_to_gold`
  échoue avec `permission denied while trying to connect to the docker API
  at unix:///var/run/docker.sock`.

  Fix validé : ajouter le GID du groupe `docker` de l'hôte dans
  `group_add` de `x-airflow-common` (docker-compose.yml) :

  ```yaml
  x-airflow-common: &airflow-common
    # ...
    group_add:
      - "984"   # getent group docker sur l'hôte pour obtenir le vrai GID
  ```

  Puis `docker compose up -d --force-recreate airflow-scheduler
  airflow-webserver`. Le GID étant spécifique à chaque machine, préférer à
  terme une variable d'environnement (`${DOCKER_GID}` dans `.env`) plutôt
  qu'une valeur en dur, pour que le repo reste portable entre postes.

- **`LOCATION_ALREADY_EXISTS` sur les tables Gold (`default_gold.db.*`).**
  Si le run dbt (`modeling_silver_to_gold`) est interrompu en plein
  `CREATE TABLE AS SELECT` (crash, kill, plantage réseau), le fichier
  Parquet reste sur S3/MinIO à l'emplacement `s3a://warehouse/default_gold.db/<table>/`
  mais l'entrée correspondante n'existe plus (ou plus jamais existé) dans
  le metastore Hive de Spark. Au run suivant, dbt tente un nouveau `CREATE
  TABLE` sur un emplacement déjà occupé et Spark refuse :

  ```
  [LOCATION_ALREADY_EXISTS] Cannot name the managed table as
  spark_catalog.default_gold.<table>, as its associated location
  's3a://warehouse/default_gold.db/<table>' already exists.
  ```

  Seules les tables `table` sont concernées (les `view`, comme les
  modèles `stg_*`, n'ont pas de stockage physique et ne sont jamais
  affectées).

  Fix : purger le(s) dossier(s) orphelin(s) dans MinIO avant de relancer,
  via un conteneur `mc` jetable sur le réseau du projet :

  ```bash
  docker run --rm --entrypoint sh \
    --network bank360-data-platform_bank360-network \
    minio/mc:latest -c "
  mc alias set local http://minio:9000 minioadmin minioadmin &&
  mc rm --recursive --force local/warehouse/default_gold.db/<table>/
  "
  ```

  Pour repartir sur une base saine sans cibler table par table, vider tout
  `default_gold.db/` d'un coup (dbt recrée l'intégralité du schéma à
  chaque `dbt run` complet) :

  ```bash
  docker run --rm --entrypoint sh \
    --network bank360-data-platform_bank360-network \
    minio/mc:latest -c "
  mc alias set local http://minio:9000 minioadmin minioadmin &&
  mc rm --recursive --force local/warehouse/default_gold.db/
  "
  ```

  Amélioration possible pour éviter ce nettoyage manuel de façon
  définitive : migrer les modèles Gold vers des tables Iceberg (matériau
  déjà utilisé pour Bronze/Silver) plutôt que des tables managées Hive
  classiques - un `DROP TABLE IF EXISTS` sur une table Iceberg gère
  proprement le cycle de vie catalogue + stockage, contrairement au
  comportement observé ici.

- **`modeling_silver_to_gold` n'est plus un `DummyOperator`.**
  L'intégration dbt a été validée de bout en bout (`dbt run` complet :
  staging, dimensions, faits, KPIs, `PASS=20 WARN=0 ERROR=0`) - c'est la
  quatrième tâche réelle du DAG dès le premier jet.