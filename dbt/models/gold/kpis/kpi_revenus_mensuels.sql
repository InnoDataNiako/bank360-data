-- kpi_revenus_mensuels.sql
-- Revenus mensuels (crédits)

SELECT
    DATE_TRUNC('month', date_transaction) AS mois,
    COUNT(*) AS nb_transactions,
    SUM(montant) AS total_revenus,
    AVG(montant) AS montant_moyen
FROM {{ ref('fact_transactions') }}
WHERE type_transaction = 'CREDIT'
  AND statut = 'COMPLETEE'
GROUP BY DATE_TRUNC('month', date_transaction)
ORDER BY mois DESC