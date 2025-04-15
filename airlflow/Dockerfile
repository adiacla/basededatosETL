FROM apache/airflow:2.8.1-python3.11

# Etapa 1: instalar dependencias de sistema como root
USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    default-libmysqlclient-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Etapa 2: cambiar a usuario airflow para instalar paquetes Python
USER airflow

RUN pip install --no-cache-dir pandas pymysql
