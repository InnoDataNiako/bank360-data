FROM apache/airflow:2.7.3-python3.10

USER root

# ============================================================
# Système : Java + Docker CLI
# ============================================================
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    curl \
    ca-certificates \
    gnupg \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && chmod a+r /etc/apt/keyrings/docker.gpg \
    && . /etc/os-release \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# Java
# ============================================================
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Vérification Java au build
RUN java -version

# ============================================================
# Airflow
# ============================================================
USER airflow

# Dépendances Python
COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir --default-timeout=300 \
    -i https://pypi.org/simple \
    -r /requirements.txt

# Scripts personnalisés
COPY scripts/ /opt/airflow/scripts/

RUN chmod +x /opt/airflow/scripts/*.sh 2>/dev/null || true