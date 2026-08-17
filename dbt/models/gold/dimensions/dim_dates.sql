-- dim_dates.sql
-- Dimension calendrier pour les analyses Bank360

WITH date_range AS (

    SELECT
        explode(
            sequence(
                to_date('2020-01-01'),
                to_date('2026-12-31'),
                interval 1 day
            )
        ) AS date

),

date_dim AS (

    SELECT
        date AS date_key,
        date,

        year(date) AS annee,
        month(date) AS mois,
        day(date) AS jour,
        quarter(date) AS trimestre,
        weekofyear(date) AS semaine,

        date_format(date, 'MMMM') AS nom_mois,
        date_format(date, 'EEEE') AS nom_jour,

        dayofweek(date) AS jour_semaine,

        CASE
            WHEN dayofweek(date) IN (1, 7)
                THEN TRUE
            ELSE FALSE
        END AS est_weekend

    FROM date_range

)

SELECT *
FROM date_dim