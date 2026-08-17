#!/usr/bin/env python3
"""
Bank360 - Construction des expectation suites Great Expectations

Pourquoi ce script existe
--------------------------
spark/jobs/batch/bronze_to_silver.py applique déjà des règles de
nettoyage (email non nul, age >= 18, montant > 0, etc.) mais les
filtre *silencieusement* : les lignes rejetées disparaissent, avec
juste un compteur "count_before / count_after / deleted" dans les
logs. On ne sait jamais QUELLES lignes ont été rejetées, ni si le
taux de rejet dérive dans le temps (ex. de 2% à 40% de doublons
d'un coup, signe probable d'un bug côté génération de données).

Ce script définit les mêmes règles métier comme expectations
Great Expectations, appliquées sur PostgreSQL - la source, avant
Spark. Objectif : avoir une mesure explicite et historisée de la
qualité des données à la source, complémentaire (pas redondante)
du filtrage Spark qui reste la protection en dernier recours pour
Silver.

Usage
-----
docker exec bank360_great_expectations python build_expectations.py
"""

import great_expectations as ge
from great_expectations.core.batch import BatchRequest

CONTEXT_ROOT_DIR = "/app/great_expectations"

# ----------------------------------------------------------------
# Règles par table
# ----------------------------------------------------------------


TABLE_EXPECTATIONS = {
    "clients": [
        ("expect_column_values_to_not_be_null", {"column": "client_id"}),
        ("expect_column_values_to_be_unique", {"column": "client_id"}),
        ("expect_column_values_to_not_be_null", {"column": "email"}),
        ("expect_column_values_to_be_unique", {"column": "email"}),
        ("expect_column_values_to_not_be_null", {"column": "prenom"}),
        ("expect_column_values_to_not_be_null", {"column": "nom"}),
    ],
    "comptes": [
        ("expect_column_values_to_not_be_null", {"column": "compte_id"}),
        ("expect_column_values_to_be_unique", {"column": "compte_id"}),
        ("expect_column_values_to_not_be_null", {"column": "numero_compte"}),
        ("expect_column_values_to_be_unique", {"column": "numero_compte"}),
        ("expect_column_values_to_not_be_null", {"column": "client_id"}),
        # Note : la règle "solde >= -decouvert_autorise" compare deux
        # colonnes entre elles - Great Expectations 0.17 ne l'exprime
        # pas nativement en une expectation simple. Elle reste gérée
        # côté Spark (clean_comptes). Ici on vérifie au moins que les
        # deux colonnes existent et sont renseignées.
        ("expect_column_values_to_not_be_null", {"column": "solde"}),
        ("expect_column_values_to_not_be_null", {"column": "decouvert_autorise"}),
    ],
    "cartes": [
        ("expect_column_values_to_not_be_null", {"column": "carte_id"}),
        ("expect_column_values_to_be_unique", {"column": "carte_id"}),
        ("expect_column_values_to_not_be_null", {"column": "numero_carte"}),
        ("expect_column_values_to_be_unique", {"column": "numero_carte"}),
        ("expect_column_values_to_not_be_null", {"column": "date_expiration"}),
    ],
    "transactions": [
        ("expect_column_values_to_not_be_null", {"column": "transaction_id"}),
        ("expect_column_values_to_be_unique", {"column": "transaction_id"}),
        (
            "expect_column_values_to_be_between",
            {"column": "montant", "min_value": 0, "strict_min": True},
        ),
        (
            "expect_column_values_to_be_in_set",
            {
                "column": "canal",
                "value_set": ["ATM", "MOBILE", "WEB", "AGENCE", "VIREMENT"],
                "mostly": 0.9,
            },
        ),
        ("expect_column_values_to_be_unique", {"column": "reference", "mostly": 0.99}),
    ],
    "paiements": [
        ("expect_column_values_to_not_be_null", {"column": "paiement_id"}),
        (
            "expect_column_values_to_be_between",
            {"column": "montant", "min_value": 0, "strict_min": True},
        ),
        (
            "expect_column_values_to_be_unique",
            {"column": "reference_paiement", "mostly": 0.99},
        ),
    ],
    "virements": [
        ("expect_column_values_to_not_be_null", {"column": "virement_id"}),
        (
            "expect_column_values_to_be_between",
            {"column": "montant", "min_value": 0, "strict_min": True},
        ),
        (
            "expect_column_values_to_be_unique",
            {"column": "reference_virement", "mostly": 0.99},
        ),
    ],
    "credits": [
        ("expect_column_values_to_not_be_null", {"column": "credit_id"}),
        (
            "expect_column_values_to_be_between",
            {"column": "montant", "min_value": 0, "strict_min": True},
        ),
        ("expect_column_values_to_not_be_null", {"column": "client_id"}),
    ],
    "agences": [
        ("expect_column_values_to_not_be_null", {"column": "agence_id"}),
        ("expect_column_values_to_not_be_null", {"column": "code_agence"}),
        ("expect_column_values_to_be_unique", {"column": "code_agence"}),
    ],
    "employes": [
        ("expect_column_values_to_not_be_null", {"column": "employe_id"}),
        ("expect_column_values_to_not_be_null", {"column": "email"}),
        ("expect_column_values_to_be_unique", {"column": "email"}),
    ],
    "operations_atm": [
        ("expect_column_values_to_not_be_null", {"column": "operation_atm_id"}),
        (
            "expect_column_values_to_be_between",
            {"column": "montant", "min_value": 0, "strict_min": True, "mostly": 0.95},
        ),
    ],
    "mobile_banking": [
        ("expect_column_values_to_not_be_null", {"column": "mobile_id"}),
        (
            "expect_column_values_to_be_unique",
            {"column": "reference_operation", "mostly": 0.99},
        ),
    ],
    "devises": [
        ("expect_column_values_to_not_be_null", {"column": "devise_id"}),
        ("expect_column_values_to_not_be_null", {"column": "code_devise"}),
        ("expect_column_values_to_be_unique", {"column": "code_devise"}),
    ],
    "taux_change": [
        ("expect_column_values_to_not_be_null", {"column": "taux_change_id"}),
        (
            "expect_column_values_to_be_between",
            {"column": "taux", "min_value": 0, "strict_min": True},
        ),
        (
            "expect_compound_columns_to_be_unique",
            {"column_list": ["devise_source", "devise_cible", "date_taux"]},
        ),
    ],
    "beneficiaires": [
        ("expect_column_values_to_not_be_null", {"column": "beneficiaire_id"}),
        ("expect_column_values_to_not_be_null", {"column": "numero_compte"}),
        ("expect_column_values_to_not_be_null", {"column": "client_id"}),
    ],
    "alertes_fraude": [
        ("expect_column_values_to_not_be_null", {"column": "alerte_id"}),
        (
            "expect_column_values_to_be_in_set",
            {
                "column": "niveau_risque",
                "value_set": ["FAIBLE", "MOYEN", "ELEVE", "CRITIQUE"],
            },
        ),
    ],
}


def build_suite(context, table_name, rules):
    suite_name = f"{table_name}_suite"
    context.add_or_update_expectation_suite(suite_name)

    batch_request = BatchRequest(
        datasource_name="postgres",
        data_connector_name="default",
        data_asset_name=table_name,
    )

    validator = context.get_validator(
        batch_request=batch_request,
        expectation_suite_name=suite_name,
    )

    for method_name, kwargs in rules:
        getattr(validator, method_name)(**kwargs)

    # discard_failed_expectations=False : on définit la règle métier
    # telle qu'elle doit être, peu importe si les données actuelles
    # la respectent déjà ou non - ce n'est pas un apprentissage à
    # partir des données présentes.
    validator.save_expectation_suite(discard_failed_expectations=False)
    print(f"  ✓ {suite_name} ({len(rules)} règles)")


def main():
    print("=" * 70)
    print(" BANK360 - CONSTRUCTION DES EXPECTATION SUITES")
    print("=" * 70)
    print()

    context = ge.get_context(context_root_dir=CONTEXT_ROOT_DIR)

    for table_name, rules in TABLE_EXPECTATIONS.items():
        build_suite(context, table_name, rules)

    print()
    print(f"{len(TABLE_EXPECTATIONS)} suites créées.")
    print("=" * 70)


if __name__ == "__main__":
    main()