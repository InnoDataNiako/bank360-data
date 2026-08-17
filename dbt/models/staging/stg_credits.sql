-- stg_credits.sql
-- Lecture directe depuis Silver

SELECT
    credit_id,
    client_id,
    type_credit,
    montant,
    taux_interet,
    duree_mois,
    mensualite,
    solde_restant,
    statut,
    date_debut,
    date_fin,
    date_prochain_paiement,
    montant_paye,
    date_creation,
    date_modification,
    silver_date
FROM iceberg_catalog.silver.credits