# 1. Actualizamos a una versión de Airflow más moderna y estable con Python 3.11
FROM apache/airflow:2.10.2-python3.11

# 2. Instalamos dependencias del sistema (¡Solo las estrictamente necesarias!)
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    # pkg-config y default-libmysqlclient-dev solo si en el futuro usas 'mysqlclient' (C-binding)
    pkg-config \
    default-libmysqlclient-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3. Volvemos al usuario airflow para instalar los paquetes de Python
USER airflow

# Actualizamos pip e instalamos las librerías necesarias
# Nota: Incluimos los "providers" oficiales de Airflow para MySQL y MongoDB.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    pandas \
    pymysql \
    cryptography \
    apache-airflow-providers-mysql \
    apache-airflow-providers-mongo
