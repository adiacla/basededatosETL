# Guía de Instalación y Talleres Prácticos: ETL con MySQL, MongoDB y Apache Airflow

Este repositorio contiene los recursos, scripts y configuraciones necesarios para llevar a cabo los talleres prácticos de la asignatura **Nuevos Paradigmas de Bases de Datos**. El objetivo de estos talleres es aprender a extraer, transformar y cargar (ETL) datos usando entornos relacionales (MySQL), no relacionales (MongoDB) y un orquestador de flujos de trabajo profesional (Apache Airflow) de manera integrada con **Visual Studio Code**.

---

## 💻 Requisitos del Sistema e Instalación de Herramientas (En Windows 11)

Antes de clonar el repositorio y levantar el entorno, cada estudiante debe instalar obligatoriamente las siguientes herramientas en su sistema operativo:

### 1. Docker Desktop
Docker nos permite ejecutar servidores preconfigurados (MySQL, MongoDB, Airflow) sin necesidad de lidiar con engorrosas instalaciones manuales en Windows.
* **Instalación:** Descarga e instala [Docker Desktop para Windows](https://www.docker.com/products/docker-desktop/).
* **Importante:** Durante la instalación, asegúrate de activar la casilla de integración con **WSL 2 (Windows Subsystem for Linux)**. Una vez instalado, reinicia tu computadora y asegúrate de abrir la aplicación Docker Desktop para que el servicio esté activo.

### 2. Python 3.11
Los scripts de extracción, transformación y las herramientas de Jupyter requieren de Python instalado en el sistema host para interactuar con los servidores de Docker.
* **Instalación:** Descarga la versión específica de [Python 3.11](https://www.python.org/downloads/) (o superior).
* **Importante:** Al iniciar el instalador de Windows, **marca obligatoriamente la casilla "Add python.exe to PATH"** antes de presionar *Install Now*. Esto nos permitirá ejecutar comandos desde la terminal de VS Code.

### 3. Visual Studio Code (VS Code) y Extensiones
Será nuestro entorno de desarrollo unificado para editar y ejecutar scripts (`.py`) y cuadernos de Jupyter (`.ipynb`).
* **Instalación:** Descarga e instala [Visual Studio Code](https://code.visualstudio.com/).
* **Extensiones Obligatorias (Instalar desde el panel de Extensiones en VS Code):**
  * **Python** (de Microsoft)
  * **Jupyter** (de Microsoft)
  * **Docker** (de Microsoft - opcional pero recomendado)

---

## 🗺️ Arquitectura del Entorno de Trabajo

Una vez que tengas las herramientas instaladas, Docker Compose se encargará de levantar y coordinar los tres servidores de manera preinstalada y listos para su consumo:


```

```
              ┌─────────────────────────────────────────────────────────┐
              │                 SISTEMA HOST (Windows 11)               │
              │                                                         │

```

┌───────────┐   │   ┌─────────────────────────────────────────────────┐   │
│  Visual   │   │   │            DOCKER COMPOSE ORCHESTRATION         │   │
│  Studio   │   │   │                                                 │   │
│   Code    │───┼──>│ ┌──────────────┐ ┌──────────────┐ ┌───────────┐ │   │
│           │   │   │ │    mysql     │ │   mongodb    │ │  airflow  │ │   │
│ 🖥️ Editor │   │   │ │  Port: 3310  │ │ Port: 27017  │ │Port: 8080 │ │   │
│  y Python │   │   │ │ (MySQL 8.0)  │ │ (Mongo 6.0)  │ │ (Py 3.11) │ │   │
└───────────┘   │   │ └──────┬───────┘ └──────┬───────┘ └─────┬─────┘ │   │
│   └────────┼────────────────┼───────────────┼───────┘   │
│            ▼                ▼               ▼           │
│     ┌────────────┐   ┌────────────┐   ┌───────────┐     │
│     │ Volúmenes  │   │ Volúmenes  │   │ Volúmenes │     │
│     │ Persistente│   │ Persistente│   │ dags, logs│     │
│     └────────────┘   └────────────┘   └───────────┘     │
└─────────────────────────────────────────────────────────┘

```

---

## 📁 Estructura del Proyecto

Organiza tu directorio de trabajo local con la siguiente estructura de archivos:

```text
├── airflow/
│   ├── Dockerfile             # Configuración de la imagen personalizada de Airflow
│   ├── dags/                  # Carpeta donde guardarás el DAG (ej. etl_dag.py)
│   ├── logs/                  # Registro de ejecuciones (generado por Airflow)
│   └── plugins/               # Extensiones para Airflow
├── mysql/
│   ├── 0-create-airflow-db.sql
│   ├── db_movies_neflix_transact.sql
│   ├── data_warehouse_netflix.sql
│   ├── datos/                 # Datos fuente adicionales (ej. Awards_movie.csv)
│   └── data/                  # Carpeta de persistencia mapeada para MySQL
├── mongodb/
│   ├── .env                   # Variables de entorno específicas de MongoDB
│   └── etl.ipynb              # Notebook del taller de MongoDB
├── docker-compose.yml         # Configuración de orquestación de Docker
└── requirements.txt           # Librerías Python necesarias para tu entorno local

```

---

## ⚙️ Inicialización del Entorno

### 1. Construir y Levantar los Contenedores

Abre una terminal (PowerShell, Git Bash o la integrada en VS Code) en la carpeta raíz de tu proyecto y ejecuta:

```bash
# Paso 1: Construir la imagen personalizada de Airflow con soporte para Python 3.11 sin caché
docker-compose build --no-cache

# Paso 2: Levantar todos los contenedores en segundo plano (detached mode)
docker-compose up -d

```

### 2. Verificar que los Servicios estén Corriendo

Para verificar que los contenedores se levantaron correctamente y revisar sus puertos asociados, ejecuta:

```bash
docker ps

```

Deberás ver en ejecución:

* `mysql:8.0` (Puerto de acceso externo: `3310`)
* `mongo:6.0` (Puerto de acceso externo: `27017`)
* `airflow` (Puerto de acceso externo: `8080`)

---

## 📝 TALLER 1: ETL Pipeline usando Python, MySQL y Airflow

### Objetivos:

* Conectarse a una base de datos relacional MySQL desde Python.
* Extraer y transformar datos de películas e integrar un archivo CSV externo (`Awards_movie.csv`).
* Automatizar el flujo completo mediante tareas programadas (DAG) en Airflow.

### Pasos Prácticos:

1. **Verificar la Base de Datos:** Conéctate al contenedor MySQL de Docker desde la terminal integrada de VS Code para verificar tus bases de datos importadas:
```bash
docker exec -it <nombre_del_contenedor_mysql_o_ID> bash
mysql -u root -p  # Contraseña: root
SHOW DATABASES;

```


2. **Ejecutar el Desarrollo en VS Code:** Abre y ejecuta paso a paso el archivo Jupyter Notebook `etl_MYSQL.ipynb` en tu máquina local conectándote a `127.0.0.1:3310`.
3. **Automatización:** Coloca tu archivo final de DAG (`etl_dag.py`) dentro de la carpeta local `./airflow/dags/`.
4. **Ejecutar en Airflow:**
* Abre tu navegador e ingresa a [http://localhost:8080](https://www.google.com/search?q=http://localhost:8080) (Usuario: `admin` / Clave: `admin`).
* Activa tu DAG `etl_dependencias` y lánzalo manualmente.
* Confirma que el archivo final integrado se genere correctamente en tus volúmenes compartidos de datos.



---

## 📝 TALLER 2: ETL con MongoDB y Python

### Objetivos:

* Conectarse a una base de datos NoSQL (MongoDB) utilizando `pymongo` y `pandas`.
* Extraer documentos de prueba, transformarlos utilizando DataFrames y cargar el informe final en formato estructurado.

### Pasos Prácticos:

1. **Cargar el Dataset de Prueba (`papeleria.js`):**
Descarga e inserta la base de datos de ejemplo dentro del contenedor de MongoDB ejecutando estos comandos en tu terminal:
```bash
docker exec -it <nombre_contenedor_mongodb> bash
apt update && apt install -y wget
cd /tmp && wget [https://raw.githubusercontent.com/adiacla/bigdata/refs/heads/master/papeleria.js](https://raw.githubusercontent.com/adiacla/bigdata/refs/heads/master/papeleria.js)
mongosh /tmp/papeleria.js

```


2. **Crear el archivo de Variables de Entorno (`.env`):**
Crea un archivo llamado `.env` dentro de la carpeta `./mongodb/` con los siguientes datos:
```env
MONGO_URI=mongodb://localhost:27017
DB_NAME=papeleria
COLLECTION=inventario

```


3. **Instalar Dependencias de Python Locales:**
Para poder ejecutar notebooks de Jupyter de manera local en VS Code, instala en tu terminal de Windows las librerías necesarias:
```bash
pip install ipykernel pymongo pandas python-dotenv

```


4. **Ejecutar el Notebook:**
Abre el archivo `./mongodb/etl.ipynb` en VS Code, selecciona tu entorno de Python (Kernel) e inicia la ejecución celda por celda para extraer los datos de MongoDB, calcular los campos necesarios (`precio_total`), agruparlos por ciudad y exportar tu archivo `productos.csv`.

---

## 🛑 Detener el Proyecto de manera Segura

Cuando termines tus prácticas de desarrollo, puedes apagar todos los servidores de manera segura sin perder el trabajo acumulado gracias a los volúmenes persistentes configurados en Docker:

```bash
docker-compose down

```

*Nota: Si por algún motivo quieres borrar por completo toda la información almacenada en MySQL y MongoDB para reiniciar el taller desde cero, ejecuta `docker-compose down -v`.*

---

*Taller desarrollado para fines educativos y de entrenamiento en Nuevos Paradigmas de Bases de Datos.*

```

```
