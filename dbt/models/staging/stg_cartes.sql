-- stg_cartes.sql
-- Lecture directe depuis Silver

SELECT
    carte_id,
    compte_id,
    numero_carte,
    type_carte,
    nom_porteur,
    date_expiration,
    cvv,
    code_pin,
    est_active,
    limite_quotidienne,
    limite_mensuelle,
    est_internationale,
    date_creation,
    date_modification,
    silver_date
FROM iceberg_catalog.silver.cartes