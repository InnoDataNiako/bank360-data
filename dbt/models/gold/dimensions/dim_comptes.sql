-- dim_comptes.sql
-- Dimension des comptes bancaires
-- Source : Iceberg Silver / MinIO

SELECT
    compte_id,
    client_id,
    numero_compte,
    type_compte,
    devise,
    solde,
    decouvert_autorise,
    taux_interet,
    est_actif,
    date_ouverture,
    date_fermeture,
    date_creation,
    date_modification

FROM {{ ref('stg_comptes') }}