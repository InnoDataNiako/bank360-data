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
    ↓ (Postgres / MinIO / Nessie / Spark Thrift OK)
ingestion_postgres_to_bronze (spark-submit)
    ↓
transformation_bronze_to_silver (spark-submit)
    ↓
modeling_silver_to_gold (dbt run)
```

Le DAG ne lance pas de nouveaux conteneurs : il exécute des `docker exec`
sur les conteneurs longue durée déjà en place (`bank360_spark_master`,
`bank360_dbt`), via le socket Docker monté dans le conteneur Airflow
(`/var/run/docker.sock`). Ce sont exactement les commandes validées
manuellement dans `ingestion/README.md`, rejouées automatiquement.

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
  `Dockerfile`), sans quoi les tâches `docker exec` échouent avec
  `docker: command not found`. Le socket seul ne suffit pas.
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
- **Permissions sur `/var/run/docker.sock`** : selon la configuration de
  l'hôte, l'utilisateur `airflow` du conteneur peut ne pas avoir les
  droits sur le socket monté (appartenant au groupe `docker` de l'hôte).
  Si les tâches `docker exec` échouent avec `permission denied`, il faut
  aligner le GID du groupe `docker` dans l'image Airflow sur celui de
  l'hôte, ou exécuter ces tâches spécifiques en root.
- **`modeling_silver_to_gold` n'est plus un `DummyOperator`.**
  L'intégration dbt a été validée de bout en bout (`dbt run` complet :
  staging, dimensions, faits, KPIs) - c'est la troisième tâche réelle du
  DAG dès le premier jet