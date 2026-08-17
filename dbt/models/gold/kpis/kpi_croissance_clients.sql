-- kpi_croissance_clients.sql
-- Croissance du nombre de clients par mois

SELECT
    DATE_TRUNC('month', date_inscription) AS mois,
    COUNT(*) AS nb_nouveaux_clients
FROM {{ ref('dim_clients') }}
GROUP BY DATE_TRUNC('month', date_inscription)
ORDER BY mois DESC