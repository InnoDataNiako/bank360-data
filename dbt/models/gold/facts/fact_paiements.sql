-- fact_paiements.sql
-- Faits des paiements par carte

SELECT
    p.paiement_id,
    p.carte_id,
    p.beneficiaire,
    p.montant,
    p.devise,
    p.reference_paiement,
    p.date_paiement,
    to_date(p.date_paiement) AS date_key,
    p.statut,
    p.type_paiement,
    p.date_creation

FROM {{ ref('stg_paiements') }} AS p