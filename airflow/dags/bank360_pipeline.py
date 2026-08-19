"""
DAG bank360_pipeline
=====================

Pipeline batch quotidien : PostgreSQL -> Bronze -> Silver -> Gold (dbt).


Étapes réelles (dbt run a été validé de bout en bout - ce n'est plus un
DummyOperator/placeholder) :
  1. healthcheck_environment       : vérifie Postgres, MinIO, Nessie,
                                      et l'enregistrement du Thrift
                                      Server auprès du Spark Master.
  2. ingestion_postgres_to_bronze  : spark-submit postgres_to_bronze.py
  3. transformation_bronze_to_silver : spark-submit bronze_to_silver.py
  4. modeling_silver_to_gold       : dbt run (staging + gold + KPIs)

Toutes les tâches Spark/dbt sont lancées via `docker exec` sur les
conteneurs longue durée existants (bank360_spark_master, bank360_dbt),
au travers du socket Docker monté dans le conteneur Airflow. C'est la
reproduction exacte des commandes déjà validées manuellement
(voir ingestion/README.md) - pas une nouvelle mécanique.
"""

from datetime import datetime, timedelta

import requests
from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

HTTP_TIMEOUT_SECONDS = 10

# Jars nécessaires aux jobs Spark (cf. ingestion/README.md)
SPARK_JARS = (
    "/opt/spark/jars/postgresql-42.6.0.jar,"
    "/opt/spark/jars/iceberg-aws-bundle-1.5.2.jar"
)


def _check_postgres(errors: list[str]) -> None:
    try:
        hook = PostgresHook(postgres_conn_id="postgres_default")
        conn = hook.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
    except Exception as exc:  
        errors.append(f"Postgres (bank360) injoignable : {exc}")


def _check_minio(errors: list[str]) -> None:
    try:
        resp = requests.get(
            "http://minio:9000/minio/health/live", timeout=HTTP_TIMEOUT_SECONDS
        )
        if resp.status_code != 200:
            errors.append(f"MinIO répond mais statut inattendu : {resp.status_code}")
    except requests.RequestException as exc:
        errors.append(f"MinIO injoignable : {exc}")


def _check_nessie(errors: list[str]) -> None:
    try:
        resp = requests.get(
            "http://nessie:19120/api/v2/config", timeout=HTTP_TIMEOUT_SECONDS
        )
        if resp.status_code >= 500:
            errors.append(f"Nessie répond mais en erreur serveur : {resp.status_code}")
    except requests.RequestException as exc:
        errors.append(f"Nessie injoignable : {exc}")


def _check_spark_thrift_registered(errors: list[str]) -> None:
    """
    Vérifie que le Thrift Server est bien enregistré comme application
    active auprès du Spark Master.
    """
    try:
        resp = requests.get(
            "http://spark-master:8081/json/", timeout=HTTP_TIMEOUT_SECONDS
        )
        resp.raise_for_status()
        payload = resp.json()
        active_apps = payload.get("activeapps", [])
        names = [app.get("name", "") for app in active_apps]
        if not any("thrift" in name.lower() for name in names):
            errors.append(
                "Spark Thrift Server non enregistré comme application active "
                f"auprès du Master (activeapps actuelles : {names or 'aucune'}). "
                "Le port 10000 peut malgré tout répondre : fix connu -> "
                "'docker restart bank360_spark_thrift'."
            )
    except requests.RequestException as exc:
        errors.append(f"Spark Master injoignable (http://spark-master:8081) : {exc}")


def healthcheck_environment(**_context) -> None:
    errors: list[str] = []
    _check_postgres(errors)
    _check_minio(errors)
    _check_nessie(errors)
    _check_spark_thrift_registered(errors)

    if errors:
        details = "\n  - ".join(errors)
        raise AirflowException(
            "Healthcheck échoué, pipeline interrompu avant l'ingestion "
            f"pour éviter une cascade d'échecs :\n  - {details}"
        )

default_args = {
    "owner": "data-eng",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="bank360_pipeline",
    description="Pipeline bank360 : healthcheck -> Bronze -> Silver -> Gold (dbt)",
    default_args=default_args,
    schedule_interval="0 2 * * *",
    start_date=datetime(2026, 8, 1),
    catchup=False,
    max_active_runs=1,
    tags=["bank360", "batch", "lakehouse"],
) as dag:

    healthcheck = PythonOperator(
        task_id="healthcheck_environment",
        python_callable=healthcheck_environment,
    )

    #  Utilisation de SparkSubmitOperator au lieu de docker exec
    ingestion_postgres_to_bronze = SparkSubmitOperator(
        task_id="ingestion_postgres_to_bronze",
        application="/opt/spark/jobs/batch/postgres_to_bronze.py",
        conn_id="spark_default",
        jars=SPARK_JARS,
        verbose=True,
)

    transformation_bronze_to_silver = SparkSubmitOperator(
        task_id="transformation_bronze_to_silver",
        application="/opt/spark/jobs/batch/bronze_to_silver.py",
        conn_id="spark_default",
        jars=SPARK_JARS,
        verbose=True,
)


    # dbt run
    modeling_silver_to_gold = BashOperator(
        task_id="modeling_silver_to_gold",
        bash_command="docker exec bank360_dbt dbt run",
        dag=dag
    )

    healthcheck >> ingestion_postgres_to_bronze >> transformation_bronze_to_silver >> modeling_silver_to_gold