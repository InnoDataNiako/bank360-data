FROM python:3.9-slim

WORKDIR /app

# Installation de Great Expectations
RUN pip install --no-cache-dir \
    great-expectations==0.17.0 \
    sqlalchemy==2.0.19 \
    psycopg2-binary==2.9.7 \
    pandas==2.0.3 \
    minio==7.2.0 \
    boto3==1.28.17

# Copie des fichiers de configuration
COPY great_expectations.yml /app/great_expectations.yml

CMD ["tail", "-f", "/dev/null"]