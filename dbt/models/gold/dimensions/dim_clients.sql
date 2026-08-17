-- dim_clients.sql
-- Dimension des clients
-- Source : Iceberg Silver / MinIO

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
    date_modification

FROM {{ ref('stg_clients') }}