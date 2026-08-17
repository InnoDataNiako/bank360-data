FROM python:3.9-slim

WORKDIR /usr/app/dbt

# Outils système nécessaires
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Installation de dbt pour Spark
RUN pip install --no-cache-dir \
    "dbt-core==1.10.22" \
    "dbt-spark[PyHive]==1.9.3"

# Configuration dbt
COPY profiles.yml /usr/app/dbt/profiles.yml
COPY dbt_project.yml /usr/app/dbt/dbt_project.yml

# Modèles dbt
COPY models/ /usr/app/dbt/models/
COPY tests/ /usr/app/dbt/tests/
COPY macros/ /usr/app/dbt/macros/
COPY seeds/ /usr/app/dbt/seeds/

CMD ["tail", "-f", "/dev/null"]