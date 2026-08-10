FROM apache/spark:3.5.1

USER root

# Installation des dépendances système et Python
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3-pip \
        curl \
        wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Téléchargement des JARs nécessaires
RUN wget -P /opt/spark/jars \
https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.5.2/iceberg-spark-runtime-3.5_2.12-1.5.2.jar && \
wget -P /opt/spark/jars \
https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.6/hadoop-aws-3.3.6.jar && \
wget -P /opt/spark/jars \
https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.720/aws-java-sdk-bundle-1.12.720.jar

# Dépendances Python
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Configuration Spark
COPY config/spark-defaults.conf /opt/spark/conf/spark-defaults.conf

# Répertoire de travail
WORKDIR /opt/spark

USER 185

CMD ["/opt/spark/bin/spark-class", "org.apache.spark.deploy.master.Master"]