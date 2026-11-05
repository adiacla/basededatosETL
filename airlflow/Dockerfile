FROM apache/airflow:2.10.2-python3.11
 
# Dependencias del sistema (build-essential es necesario para compilar mysqlclient)
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    default-libmysqlclient-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
 
# Paquetes de Python con el constraints oficial de Airflow
# (evita que pip cambie la version de Airflow o rompa sus dependencias)
USER airflow
ARG AIRFLOW_VERSION=2.10.2
ARG PYTHON_VERSION=3.11
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" \
    pandas \
    pymysql \
    cryptography \
    apache-airflow-providers-mysql \
    apache-airflow-providers-mongo \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"