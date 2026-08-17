-- stg_comptes.sql
-- Lecture directe depuis Silver

SELECT
    compte_id,
    client_id,
    numero_compte,
    type_compte,
    devise,
    solde,
    decouvert_autorise,
    taux_interet,
    est_actif,
    date_ouverture,
    date_fermeture,
    date_creation,
    date_modification,
    silver_date

FROM iceberg_catalog.silver.comptes