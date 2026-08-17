#!/usr/bin/env python3

"""
Bank360 - Transformation Bronze → Silver

Lit les tables Iceberg depuis le namespace Bronze,
applique les règles de nettoyage et écrit les données
nettoyées dans le namespace Silver.
"""

import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    current_date,
    current_timestamp,
    floor,
    lit,
    months_between,
    when,
)


# ============================================================
# CONFIGURATION
# ============================================================

WAREHOUSE = os.getenv(
    "MINIO_WAREHOUSE",
    "s3a://warehouse/"
)

MINIO_ENDPOINT = os.getenv(
    "MINIO_ENDPOINT",
    "http://minio:9000"
)

MINIO_ACCESS_KEY = os.getenv(
    "MINIO_ACCESS_KEY",
    "minioadmin"
)

MINIO_SECRET_KEY = os.getenv(
    "MINIO_SECRET_KEY",
    "minioadmin"
)


# ============================================================
# TABLES BRONZE → SILVER
# ============================================================

TABLES = [
    "agences",
    "alertes_fraude",
    "beneficiaires",
    "cartes",
    "clients",
    "comptes",
    "credits",
    "devises",
    "employes",
    "mobile_banking",
    "operations_atm",
    "paiements",
    "taux_change",
    "transactions",
    "virements",
]


# ============================================================
# REGLES DE NETTOYAGE
# ============================================================

def clean_clients(df):
    """
    Nettoyage de la table clients.
    """

    return (
        df
        .filter(col("email").isNotNull())
        .filter(col("prenom").isNotNull())
        .filter(col("nom").isNotNull())
        .dropDuplicates(["email"])
        .withColumn(
            "age",
            when(
                col("date_naissance").isNotNull(),
                floor(
                    months_between(
                        current_date(),
                        col("date_naissance")
                    ) / 12
                )
            ).otherwise(lit(None))
        )
        .filter(col("age").isNotNull())
        .filter(col("age") >= 18)
    )


def clean_comptes(df):
    """
    Nettoyage de la table comptes.
    """

    return (
        df
        .filter(col("numero_compte").isNotNull())
        .filter(col("client_id").isNotNull())
        .filter(
            col("solde") >= -col("decouvert_autorise")
        )
        .dropDuplicates(["numero_compte"])
    )


def clean_transactions(df):
    """
    Nettoyage de la table transactions.
    """

    valid_canaux = [
        "ATM",
        "MOBILE",
        "WEB",
        "AGENCE",
        "VIREMENT",
    ]

    return (
        df
        .filter(col("montant") > 0)
        .filter(
            col("date_transaction") >= "2020-01-01"
        )
        .filter(
            col("canal").isin(valid_canaux)
        )
        .dropDuplicates(["reference"])
    )


def clean_cartes(df):
    """
    Nettoyage de la table cartes.
    """

    return (
        df
        .filter(
            col("date_expiration") >= current_date()
        )
        .filter(
            col("numero_carte").isNotNull()
        )
        .dropDuplicates(["numero_carte"])
    )


def clean_credits(df):
    """
    Nettoyage de la table credits.
    """

    df_clean = df.dropDuplicates()

    if "montant" in df.columns:
        df_clean = df_clean.filter(
            col("montant") > 0
        )

    return df_clean


def clean_virements(df):
    """
    Nettoyage de la table virements.
    """

    df_clean = df.dropDuplicates()

    if "montant" in df.columns:
        df_clean = df_clean.filter(
            col("montant") > 0
        )

    return df_clean


def clean_paiements(df):
    """
    Nettoyage de la table paiements.
    """

    df_clean = df.dropDuplicates()

    if "montant" in df.columns:
        df_clean = df_clean.filter(
            col("montant") > 0
        )

    return df_clean


def clean_operations_atm(df):
    """
    Nettoyage des opérations ATM.
    """

    df_clean = df.dropDuplicates()

    if "montant" in df.columns:
        df_clean = df_clean.filter(
            col("montant") > 0
        )

    return df_clean


def clean_mobile_banking(df):
    """
    Nettoyage des opérations Mobile Banking.
    """

    return df.dropDuplicates()


def clean_beneficiaires(df):
    """
    Nettoyage des bénéficiaires.
    """

    return df.dropDuplicates()


def clean_alertes_fraude(df):
    """
    Nettoyage des alertes fraude.
    """

    return df.dropDuplicates()


def clean_agences(df):
    """
    Nettoyage des agences.
    """

    return df.dropDuplicates()


def clean_devises(df):
    """
    Nettoyage des devises.
    """

    return df.dropDuplicates()


def clean_employes(df):
    """
    Nettoyage des employés.
    """

    return df.dropDuplicates()


def clean_taux_change(df):
    """
    Nettoyage des taux de change.
    """

    df_clean = df.dropDuplicates()

    if "taux" in df.columns:
        df_clean = df_clean.filter(
            col("taux") > 0
        )

    return df_clean


# ============================================================
# MAPPING DES REGLES DE NETTOYAGE
# ============================================================

CLEANERS = {
    "agences": clean_agences,
    "alertes_fraude": clean_alertes_fraude,
    "beneficiaires": clean_beneficiaires,
    "cartes": clean_cartes,
    "clients": clean_clients,
    "comptes": clean_comptes,
    "credits": clean_credits,
    "devises": clean_devises,
    "employes": clean_employes,
    "mobile_banking": clean_mobile_banking,
    "operations_atm": clean_operations_atm,
    "paiements": clean_paiements,
    "taux_change": clean_taux_change,
    "transactions": clean_transactions,
    "virements": clean_virements,
}


# ============================================================
# SPARK SESSION
# ============================================================


def create_spark_session():
    spark = (
        SparkSession.builder
        .appName("Bank360-BronzeToSilver")
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
        .config("spark.sql.catalog.iceberg_catalog", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.iceberg_catalog.type", "rest")
        .config("spark.sql.catalog.iceberg_catalog.uri", "http://nessie:19120/iceberg")
        .config("spark.sql.catalog.iceberg_catalog.warehouse", "warehouse")
        .getOrCreate()
    )

    # Créer le namespace silver s'il n'existe pas — idempotent
    spark.sql("CREATE NAMESPACE IF NOT EXISTS iceberg_catalog.silver")

    return spark

# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(" BANK360 - BRONZE → SILVER")
    print("=" * 70)

    print()
    print(f"Warehouse : {WAREHOUSE}")
    print("Source    : iceberg_catalog.bronze")
    print("Target    : iceberg_catalog.silver")
    print(f"Tables    : {len(TABLES)}")
    print()

    # --------------------------------------------------------
    # Initialisation Spark
    # --------------------------------------------------------

    spark = create_spark_session()

    print("Spark initialisé avec Iceberg.")
    print()

    success_count = 0
    error_count = 0

    # --------------------------------------------------------
    # Traitement des tables
    # --------------------------------------------------------

    for table_name in TABLES:

        print("-" * 70)
        print(f"Traitement : {table_name}")

        try:

            # ------------------------------------------------
            # Lecture Bronze
            # ------------------------------------------------

            bronze_table = (
                f"iceberg_catalog.bronze.{table_name}"
            )

            silver_table = (
                f"iceberg_catalog.silver.{table_name}"
            )

            df = spark.table(bronze_table)

            count_before = df.count()

            print(
                f"  Bronze : {count_before} lignes"
            )

            # ------------------------------------------------
            # Nettoyage
            # ------------------------------------------------

            cleaner = CLEANERS.get(
                table_name
            )

            if cleaner is not None:

                df_clean = cleaner(df)

            else:

                df_clean = df.dropDuplicates()

            # ------------------------------------------------
            # Statistiques
            # ------------------------------------------------

            count_after = df_clean.count()

            deleted = (
                count_before - count_after
            )

            print(
                f"  Supprimées : {deleted} lignes"
            )

            print(
                f"  Silver : {count_after} lignes"
            )

            # ------------------------------------------------
            # Ajout metadata
            # ------------------------------------------------

            df_final = (
                df_clean
                .withColumn(
                    "silver_date",
                    current_timestamp()
                )
            )

            # ------------------------------------------------
            # Ecriture Silver
            # ------------------------------------------------

            (
                df_final.writeTo(silver_table)
                .createOrReplace()
            )

            print(
                f"  ✓ {table_name} écrite en Silver"
            )

            success_count += 1

        except Exception as e:

            error_count += 1

            print(
                f"  ✗ Erreur pour {table_name}"
            )

            print(
                f"    {str(e)}"
            )

    # --------------------------------------------------------
    # Résumé
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print(" BRONZE → SILVER TERMINÉ")
    print("=" * 70)

    print(
        f"Tables réussies : {success_count}/{len(TABLES)}"
    )

    print(
        f"Tables en erreur : {error_count}/{len(TABLES)}"
    )

    print("=" * 70)

    spark.stop()


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    main()
