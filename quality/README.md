# 5. Great Expectations - Qualité des données à la source

## Pourquoi ?

`spark/jobs/batch/bronze_to_silver.py` applique déjà des règles de
nettoyage (email non nul, `age >= 18`, `montant > 0`, doublons
supprimés...) mais les filtre **silencieusement** : les lignes
rejetées disparaissent de Silver, avec seulement un compteur
`count_before / count_after / deleted` dans les logs Spark. On ne
sait jamais précisément quelles lignes ont été rejetées, ni si le
taux de rejet dérive dans le temps (par exemple 2% de doublons un
jour, 40% le lendemain - signe probable d'un bug côté génération de
données, invisible tant qu'on ne regarde que Silver).

Great Expectations applique les mêmes règles métier directement sur
PostgreSQL, **avant** l'ingestion Spark. Objectif : avoir une mesure
explicite et historisée de la qualité des données à la source,
complémentaire du filtrage Spark - pas redondante avec lui. Le
filtrage Spark reste la protection en dernier recours pour Silver ;
Great Expectations sert à détecter une dérive de qualité à la
source avant même que Spark n'ait besoin de filtrer autant.

## Objectif

Définir et exécuter, pour les 15 tables sources, des règles de
qualité miroir de celles déjà codées dans `bronze_to_silver.py`
(complétude, unicité, plages de valeurs), et conserver un historique
des résultats de validation.

## Architecture

```text
PostgreSQL (bank360.*)
    ↓ (Great Expectations - 15 expectation suites)
Validation Results (uncommitted/validations/)
    ↓
Data Docs (uncommitted/data_docs/ - rapport HTML consultable)
```

## Exécution

Première exécution : construire les 15 expectation suites (idempotent,
peut être relancé sans risque) :

```bash
docker exec -it bank360_great_expectations python build_expectations.py
```

Puis lancer la validation complète (checkpoint) :

```bash
docker exec -it bank360_great_expectations great_expectations checkpoint run bank360_source_quality_checkpoint
```

## Prérequis

- Le service `postgres` doit être `healthy` et contenir des données
  (généralement déjà le cas si `ingestion_postgres_to_bronze` a
  fonctionné au moins une fois).
- La configuration `great_expectations.yml` déclare 15 assets
  (une table PostgreSQL = un asset). Toute nouvelle table ajoutée au
  schéma (`scripts/init/init_postgres.sql`) doit être déclarée ici
  ET ajoutée à `TABLE_EXPECTATIONS` dans `build_expectations.py`,
  sans quoi elle ne sera simplement pas contrôlée - silencieusement.
