-- stg_transactions.sql
-- Lecture directe depuis Silver

SELECT
    transaction_id,
    compte_id,
    type_transaction,
    montant,
    devise,
    date_transaction,
    description,
    canal,
    statut,
    reference,
    est_suspecte,
    frais,
    date_creation,
    silver_date
FROM iceberg_catalog.silver.transactions