-- fact_transactions.sql
-- Faits des transactions bancaires

SELECT
    t.transaction_id,
    t.compte_id,
    c.client_id,
    t.type_transaction,
    t.montant,
    t.devise,
    t.date_transaction,
    to_date(t.date_transaction) AS date_key,
    t.description,
    t.canal,
    t.statut,
    t.reference,
    t.est_suspecte,
    t.frais,
    t.date_creation AS ingestion_date

FROM {{ ref('stg_transactions') }} AS t

LEFT JOIN {{ ref('stg_comptes') }} AS c
    ON t.compte_id = c.compte_id