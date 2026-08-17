-- stg_beneficiaires.sql
-- Lecture directe depuis Silver

SELECT
    beneficiaire_id,
    client_id,
    prenom,
    nom,
    numero_compte,
    banque,
    code_banque,
    pays,
    email,
    telephone,
    est_actif,
    date_creation,
    date_modification,
    silver_date
FROM iceberg_catalog.silver.beneficiaires