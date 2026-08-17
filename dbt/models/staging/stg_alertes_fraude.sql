-- stg_alertes_fraude.sql
-- Lecture directe depuis Silver

SELECT
    alerte_id,
    transaction_id,
    client_id,
    type_alerte,
    niveau_risque,
    description,
    score_risque,
    date_alerte,
    statut,
    date_resolution,
    commentaire_resolution,
    date_creation,
    date_modification,
    silver_date
FROM iceberg_catalog.silver.alertes_fraude