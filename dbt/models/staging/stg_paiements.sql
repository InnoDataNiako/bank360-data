-- stg_paiements.sql
-- Lecture directe depuis Silver

SELECT
    paiement_id,
    transaction_id,
    carte_id,
    beneficiaire,
    montant,
    devise,
    reference_paiement,
    date_paiement,
    statut,
    type_paiement,
    date_creation,
    silver_date
FROM iceberg_catalog.silver.paiements