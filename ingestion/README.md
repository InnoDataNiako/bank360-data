# Ingestion - PostgreSQL vers Bronze

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