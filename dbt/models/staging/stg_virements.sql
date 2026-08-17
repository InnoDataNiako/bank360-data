-- stg_virements.sql
-- Lecture directe depuis Silver

SELECT
    virement_id,
    compte_source_id,
    compte_destinataire_id,
    transaction_id,
    montant,
    devise,
    reference_virement,
    motif,
    date_virement,
    date_execution,
    statut,
    frais,
    est_international,
    date_creation,
    silver_date
FROM iceberg_catalog.silver.virements