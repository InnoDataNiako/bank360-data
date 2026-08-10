FROM python:3.9-slim

WORKDIR /usr/app

# Installation des dépendances système
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Installation de dbt
RUN pip install --no-cache-dir \
    dbt-core==1.5.0 \
    dbt-postgres==1.5.0

# Copie des fichiers de configuration
COPY profiles.yml /root/.dbt/profiles.yml
COPY dbt_project.yml /usr/app/dbt_project.yml

# Copie des modèles
COPY models/ /usr/app/models/
COPY tests/ /usr/app/tests/
COPY macros/ /usr/app/macros/
COPY seeds/ /usr/app/seeds/

CMD ["dbt", "run"]