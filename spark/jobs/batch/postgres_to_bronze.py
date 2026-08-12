#!/usr/bin/env python3
"""
Bank360 - Ingestion PostgreSQL vers Bronze (Iceberg)
Lit les tables PostgreSQL et les écrit en Bronze dans MinIO/Iceberg
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp

# Configuration de la base de données
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgres')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'bank360')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'bank360')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'bank360')

# Liste des tables à ingérer
TABLES = [
    'clients',
    'comptes',
    'cartes',
    'transactions',
    'credits',
    'virements',
    'paiements',
    'operations_atm',
    'mobile_banking',
    'beneficiaires',
    'alertes_fraude'
]

# URL de connexion PostgreSQL
JDBC_URL = f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Propriétés de connexion
PROPERTIES = {
    "user": POSTGRES_USER,
    "password": POSTGRES_PASSWORD,
    "driver": "org.postgresql.Driver"
}

def main():
    """Fonction principale d'ingestion"""
    
    print("=" * 60)
    print(" Bank360 - Ingestion PostgreSQL vers Bronze")
    print("=" * 60)
    
    # Initialisation de Spark avec Iceberg
    spark = SparkSession.builder \
        .appName("PostgresToBronze") \
        .config(
            "spark.sql.extensions",
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions"
        ) \
        .config(
            "spark.sql.catalog.iceberg_catalog",
            "org.apache.iceberg.spark.SparkCatalog"
        ) \
        .config(
            "spark.sql.catalog.iceberg_catalog.type",
            "hadoop"
        ) \
        .config(
            "spark.sql.catalog.iceberg_catalog.warehouse",
            "s3a://bronze/"
        ) \
        .config(
            "spark.sql.catalog.iceberg_catalog.hadoop.fs.s3a.endpoint",
            "http://minio:9000"
        ) \
        .config(
            "spark.sql.catalog.iceberg_catalog.hadoop.fs.s3a.access.key",
            os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        ) \
        .config(
            "spark.sql.catalog.iceberg_catalog.hadoop.fs.s3a.secret.key",
            os.getenv("MINIO_SECRET_KEY", "minioadmin")
        ) \
        .config(
            "spark.sql.catalog.iceberg_catalog.hadoop.fs.s3a.path.style.access",
            "true"
        ) \
        .config(
            "spark.sql.catalog.iceberg_catalog.hadoop.fs.s3a.connection.ssl.enabled",
            "false"
        ) \
        .getOrCreate()
        
    print(f" Spark initialisé avec Iceberg")
    print(f" Destination: MinIO / Bronze")
    print(f" Tables à ingérer: {len(TABLES)}")
    
    for table_name in TABLES:
        try:
            print(f"\n Ingestion de la table: {table_name}")
            
            # Lecture depuis PostgreSQL
            df = spark.read \
                .format("jdbc") \
                .option("url", JDBC_URL) \
                .option("dbtable", f"bank360.{table_name}") \
                .option("user", PROPERTIES["user"]) \
                .option("password", PROPERTIES["password"]) \
                .option("driver", PROPERTIES["driver"]) \
                .load()
            
            # Ajouter une colonne de date d'ingestion
            df = df.withColumn("ingestion_date", current_timestamp())
            
            # Compter les lignes
            count = df.count()
            print(f"    {count} lignes lues depuis PostgreSQL")
            
            # Écrire en Bronze (Iceberg)
            df.writeTo(f"iceberg_catalog.{table_name}").createOrReplace()
            
            print(f"    Table {table_name} ingérée en Bronze")
            
        except Exception as e:
            print(f"    Erreur pour la table {table_name}: {e}")
    
    print("\n" + "=" * 60)
    print(" Ingestion terminée avec succès !")
    print("=" * 60)
    
    spark.stop()

if __name__ == "__main__":
    main()