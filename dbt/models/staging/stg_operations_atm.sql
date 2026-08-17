-- stg_operations_atm.sql
-- Lecture directe depuis Silver

SELECT
    operation_atm_id,
    carte_id,
    transaction_id,
    code_atm,
    type_operation,
    montant,
    devise,
    date_operation,
    statut,
    frais,
    date_creation,
    silver_date
FROM iceberg_catalog.silver.operations_atm