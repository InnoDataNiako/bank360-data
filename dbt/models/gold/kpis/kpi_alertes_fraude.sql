-- kpi_alertes_fraude.sql
-- Nombre d'alertes de fraude par type, niveau de risque et jour

SELECT
    type_alerte,
    niveau_risque,
    COUNT(*) AS nb_alertes,
    TO_DATE(date_alerte) AS jour
FROM {{ ref('stg_alertes_fraude') }}
GROUP BY
    type_alerte,
    niveau_risque,
    TO_DATE(date_alerte)