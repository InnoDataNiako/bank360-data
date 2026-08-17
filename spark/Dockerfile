# FROM apache/spark:3.5.1

# USER root

# # ============================================================
# # Installation des dépendances système et Python
# # ============================================================

# RUN apt-get update && \
# apt-get install -y --no-install-recommends \
# python3-pip \
# curl \
# wget && \
# apt-get clean && \
# rm -rf /var/lib/apt/lists/*

# # ============================================================
# # JARs nécessaires
# # ============================================================

# # Apache Iceberg pour Spark 3.5 / Scala 2.12
# RUN wget -P /opt/spark/jars \
# https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.5.2/iceberg-spark-runtime-3.5_2.12-1.5.2.jar

# # Hadoop AWS aligné avec Hadoop 3.3.4
# RUN wget -P /opt/spark/jars \
# https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar

# # AWS SDK utilisé avec Hadoop AWS 3.3.4
# RUN wget -P /opt/spark/jars \
# https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar

# # Iceberg AWS bundle (SDK v2) - requis pour S3FileIO
# RUN wget -P /opt/spark/jars \
# https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-aws-bundle/1.5.2/iceberg-aws-bundle-1.5.2.jar

# # ============================================================
# # Dépendances Python
# # ============================================================

# COPY requirements.txt /tmp/requirements.txt

# RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# # ============================================================
# # Configuration Spark
# # ============================================================

# COPY config/spark-defaults.conf /opt/spark/conf/spark-defaults.conf

# # ============================================================
# # Répertoire de travail
# # ============================================================

# WORKDIR /opt/spark

# USER 185




FROM apache/spark:3.5.1

USER root

# ============================================================
# Installation des dépendances système et Python
# ============================================================

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3-pip \
    curl \
    wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ============================================================
# Nettoyage des jars AWS SDK v2 embarqués dans l'image de base
# (en conflit avec le SDK v2 interne d'iceberg-aws-bundle)
# ============================================================

RUN rm -f /opt/spark/jars/aws-sdk-core-*.jar \
           /opt/spark/jars/aws-sdk-s3-*.jar \
           /opt/spark/jars/aws-sdk-sts-*.jar \
           /opt/spark/jars/aws-sdk-utils-*.jar

# ============================================================
# JARs nécessaires
# ============================================================

RUN wget -P /opt/spark/jars \
    https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.5.2/iceberg-spark-runtime-3.5_2.12-1.5.2.jar

RUN wget -P /opt/spark/jars \
    https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar

RUN wget -P /opt/spark/jars \
    https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar

RUN wget -P /opt/spark/jars \
    https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-aws-bundle/1.5.2/iceberg-aws-bundle-1.5.2.jar

# ============================================================
# Dépendances Python
# ============================================================

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# ============================================================
# Configuration Spark
# ============================================================

COPY config/spark-defaults.conf /opt/spark/conf/spark-defaults.conf

WORKDIR /opt/spark
USER 185