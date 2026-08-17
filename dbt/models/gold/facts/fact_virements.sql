-- fact_virements.sql
-- Faits des virements

SELECT
    v.virement_id,
    v.compte_source_id,
    v.compte_destinataire_id,
    v.montant,
    v.devise,
    v.reference_virement,
    v.motif,
    v.date_virement,
    to_date(v.date_virement) AS date_key,
    v.statut,
    v.frais,
    v.est_international,
    v.date_creation

FROM {{ ref('stg_virements') }} AS v