-- stg_clients.sql
-- Lecture directe depuis Silver

SELECT
    client_id,
    prenom,
    nom,
    email,
    telephone,
    adresse,
    ville,
    pays,
    date_naissance,
    date_inscription,
    est_premium,
    est_actif,
    dernier_connexion,
    date_creation,
    date_modification,
    silver_date

FROM iceberg_catalog.silver.clients