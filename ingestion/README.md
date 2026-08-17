# 1. Ingestion - PostgreSQL vers Bronze

## Pourquoi ?

Les données bancaires sont actuellement stockées dans PostgreSQL (OLTP). Pour les analyser à grande échelle, nous devons les ingérer dans un Data Lakehouse.

L'ingestion permet de :
- Centraliser toutes les données dans un seul endroit (MinIO)
- Conserver l'historique complet des données
- Préparer les données pour les transformations futures

## Objectif

Extraire les données de PostgreSQL et les écrire en **Bronze** (couche brute) dans le Lakehouse.

| Source | Destination | Format |
|--------|-------------|--------|
| PostgreSQL (OLTP) | MinIO / Iceberg | Parquet |

## Architecture

```text
PostgreSQL (OLTP)
    ↓ (Spark Batch)
MinIO / Iceberg
    ↓
Bronze (données brutes)
```

## Exécution

```bash
docker exec -it bank360_spark_master spark-submit \
  --master local[*] \
  --jars /opt/spark/jars/postgresql-42.6.0.jar,/opt/spark/jars/iceberg-aws-bundle-1.5.2.jar \
  /opt/spark/jobs/batch/postgres_to_bronze.py
```

## Prérequis

Le namespace Iceberg `bronze` doit exister dans le catalogue avant le premier run. À créer une fois via :

```bash
docker exec -it bank360_spark_master spark-sql \
  --master local[*] \
  --jars /opt/spark/jars/iceberg-aws-bundle-1.5.2.jar \
  --conf spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions \
  --conf spark.sql.catalog.iceberg_catalog=org.apache.iceberg.spark.SparkCatalog \
  --conf spark.sql.catalog.iceberg_catalog.type=rest \
  --conf spark.sql.catalog.iceberg_catalog.uri=http://nessie:19120/iceberg \
  --conf spark.sql.catalog.iceberg_catalog.warehouse=warehouse \
  -e "CREATE NAMESPACE IF NOT EXISTS iceberg_catalog.bronze;"
```

---

# 2. Spark - Transformation Batch (Bronze → Silver)

## Pourquoi ?

Bronze contient des données brutes qui ne sont pas exploitables directement :
- Doublons
- NULL sur des colonnes critiques
- Valeurs non conformes
- Formats non normalisés

Silver est la couche nettoyée et validée, prête pour la modélisation.

## Objectif

Lire les tables Bronze, appliquer les règles de nettoyage et de validation, puis écrire le résultat en **Silver**.

| Source | Destination | Format |
|--------|-------------|--------|
| MinIO / Iceberg (Bronze) | MinIO / Iceberg (Silver) | Parquet |

## Architecture

```text
Bronze (MinIO/Iceberg)
    ↓ (Spark)
Silver (MinIO/Iceberg)
```

## Exécution

```bash
docker exec -it bank360_spark_master spark-submit \
  --master local[*] \
  --jars /opt/spark/jars/postgresql-42.6.0.jar,/opt/spark/jars/iceberg-aws-bundle-1.5.2.jar \
  /opt/spark/jobs/batch/bronze_to_silver.py
```

## Prérequis

Le namespace Iceberg `silver` doit exister avant le premier run (même procédure que pour `bronze`, en remplaçant le nom du namespace), et les tables Bronze doivent avoir été ingérées (voir section 1).

## Points d'attention

Certaines règles de nettoyage peuvent éliminer plus de lignes que prévu (email invalide, doublons, `age >= 18`, comparaison de soldes). Le script affiche `count_before` / `count_after` / `deleted` par table : surveiller particulièrement `clients` et `comptes`, qui ont les règles de filtrage les plus strictes.

---

# 3. dbt - Modélisation Gold

## Pourquoi ?

Silver contient des données propres mais encore trop proches du modèle opérationnel (une table par entité métier). Pour l'analyse et le reporting, il faut :
- Regrouper les données autour de dimensions et de faits (modélisation en étoile)
- Pré-calculer des indicateurs métier (KPIs) réutilisables
- Documenter et tester la logique de transformation de façon versionnée

Gold est la couche de consommation, pensée pour les analystes et les outils de BI.

## Objectif

Transformer les données Silver en modèles Gold à travers deux niveaux :
- **Staging** (vues) : une vue par table Silver, point d'entrée unique pour les modèles Gold
- **Gold** (tables) : dimensions, faits et KPIs, calculés par dbt

| Source | Destination | Format |
|--------|-------------|--------|
| MinIO / Iceberg (Silver) | MinIO / Iceberg (Gold) | Parquet |

## Architecture

```text
Silver (MinIO/Iceberg)
    ↓ (dbt staging - vues)
Staging (default.stg_*)
    ↓ (dbt gold - tables)
Gold (default_gold)
    ├── Dimensions (dim_clients, dim_comptes, dim_dates)
    ├── Faits (fact_transactions, fact_paiements, fact_virements)
    └── KPIs (kpi_alertes_fraude, kpi_croissance_clients, kpi_revenus_mensuels)
```

## Exécution

```bash
docker exec -it bank360_dbt dbt run
```

dbt se connecte au Spark Thrift Server (port 10000), qui expose le catalogue Iceberg via Nessie. Les modèles sont matérialisés en vues (staging) ou en tables (gold), selon la configuration `dbt_project.yml`.

## Vérification

```bash
docker exec -it bank360_spark_thrift beeline -u "jdbc:hive2://localhost:10000" -e "
SELECT 'dim_clients' AS t, COUNT(*) AS n FROM default_gold.dim_clients
UNION ALL SELECT 'dim_comptes', COUNT(*) FROM default_gold.dim_comptes
UNION ALL SELECT 'fact_transactions', COUNT(*) FROM default_gold.fact_transactions
UNION ALL SELECT 'fact_paiements', COUNT(*) FROM default_gold.fact_paiements
UNION ALL SELECT 'fact_virements', COUNT(*) FROM default_gold.fact_virements
UNION ALL SELECT 'kpi_alertes_fraude', COUNT(*) FROM default_gold.kpi_alertes_fraude
UNION ALL SELECT 'kpi_croissance_clients', COUNT(*) FROM default_gold.kpi_croissance_clients
UNION ALL SELECT 'kpi_revenus_mensuels', COUNT(*) FROM default_gold.kpi_revenus_mensuels;
"
```

## Prérequis

Avant le premier `dbt run`, les namespaces Iceberg `bronze` et `silver` doivent exister dans le catalogue, et les données Silver doivent avoir été ingérées par le job Spark correspondant (voir section 2).

## Points d'attention

- **Jars S3 sur driver ET workers** : le jar `iceberg-aws-bundle` (SDK AWS v2, requis par `S3FileIO`) doit être présent à la fois sur le driver (`spark-thrift`) et sur les workers (`spark-worker`). Une absence côté worker ne casse que les modèles Gold qui déclenchent une exécution distribuée (tables), pas les vues staging qui s'exécutent sur le driver.
- **Enregistrement du Thrift Server auprès du Spark Master** : le Spark Thrift Server est une application Spark de longue durée, connectée à `spark://spark-master:7077`. Si le Master ou le réseau Docker redémarre, le Thrift Server peut rester "up" en apparence (port 10000 ouvert, connexions JDBC acceptées) mais avoir perdu son enregistrement en tant qu'application active auprès du Master. Dans ce cas, les requêtes distribuées (tables Gold) restent bloquées silencieusement, sans erreur explicite, alors que les vues staging (exécutées localement sur le driver) continuent de fonctionner.
  - Diagnostic : vérifier `http://localhost:8081/json/` (champ `activeapps` — doit contenir `Thrift JDBC/ODBC Server`) et `docker stats` (CPU proche de 0% sur `spark-thrift`/`spark-worker` pendant qu'une requête est censée tourner = signe de blocage).
  - Fix : `docker restart bank360_spark_thrift`.
- **Réseau Docker** : si plusieurs réseaux Docker existent sur le projet (`_default` et `_bank360-network` par exemple) suite à des recréations de conteneurs, des services peuvent se retrouver isolés les uns des autres malgré un `docker ps` qui semble normal. Vérifier avec `docker inspect <container> --format '{{range $net, $conf := .NetworkSettings.Networks}}{{$net}}: {{$conf.Aliases}} {{end}}'` que tous les services partagent le même réseau **avec un alias DNS correctement enregistré** (`docker network connect --alias <nom_service> <reseau> <conteneur>` si besoin).