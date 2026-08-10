FROM apache/airflow:2.7.3-python3.10

USER root

# Installation des dépendances système (légères)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Dépendances Python (MINIMALES)
# On garde seulement ce dont Airflow a vraiment besoin
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir --default-timeout=300 \
    -i https://pypi.org/simple \
    -r /requirements.txt

# Scripts personnalisés
COPY scripts/ /opt/airflow/scripts/
RUN chmod +x /opt/airflow/scripts/*.sh 2>/dev/null || true