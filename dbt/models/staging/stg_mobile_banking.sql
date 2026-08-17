-- stg_mobile_banking.sql
-- Lecture directe depuis Silver

SELECT
    mobile_id,
    client_id,
    compte_id,
    transaction_id,
    num_telephone,
    type_operation,
    montant,
    devise,
    reference_operation,
    date_operation,
    statut,
    frais,
    date_creation,
    silver_date

FROM iceberg_catalog.silver.mobile_banking