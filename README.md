# Análisis de datos: MySQL + MongoDB + Apache Airflow (Docker)

Entorno de laboratorio con tres servicios en contenedores Docker:

| Servicio | Imagen | Para qué sirve | Acceso desde tu PC |
|---|---|---|---|
| **mysql** | `mysql:8.0` | Base transaccional (`db_movies_netflix_transact`), Data Warehouse (`dw_netflix`) y metadatos de Airflow (`airflow`) | `127.0.0.1:3310` |
| **mongodb** | `mongo:6.0` | Base documental `papeleria` (colección `inventario`) | `127.0.0.1:27017` |
| **airflow** | `apache/airflow:2.10.2` (construida localmente) | Orquestación de los procesos ETL (DAG `etl_dependencias`) | http://localhost:8080 |

> Esta guía está escrita para **Windows 10/11**. Todos los comandos se ejecutan en **PowerShell**, salvo que se indique otra cosa.

---

## 1. Requisitos previos

- Windows 10 (versión 22H2) o Windows 11, 64 bits.
- **Virtualización activada** en la BIOS/UEFI. Para comprobarlo: `Ctrl + Shift + Esc` → pestaña **Rendimiento** → **CPU** → debe decir **Virtualización: Habilitada**. Si dice *Deshabilitada*, actívala en la BIOS (suele llamarse *Intel VT-x*, *SVM Mode* o *AMD-V*).
- Al menos **8 GB de RAM** (Airflow + MySQL + MongoDB necesitan unos 4 GB libres) y **10 GB de disco** libres.
- Conexión a internet (la primera vez se descargan varias imágenes).
- **Python 3.11 o superior** (solo para los notebooks): https://www.python.org/downloads/ → durante la instalación marca **"Add python.exe to PATH"**.
- **VS Code** con las extensiones *Python* y *Jupyter* (opcional pero recomendado).

---

## 2. Instalar WSL 2

Docker Desktop usa WSL 2 como motor en Windows.

1. Abre **PowerShell como administrador** (clic derecho → *Ejecutar como administrador*).
2. Ejecuta:

   ```powershell
   wsl --install
   ```

3. **Reinicia el equipo** cuando termine.
4. Al volver, Ubuntu se abrirá y te pedirá crear un usuario y contraseña de Linux. Créalos (no se ven al escribir la contraseña) y cierra esa ventana.
5. Verifica la instalación en PowerShell:

   ```powershell
   wsl --status
   wsl --update
   wsl -l -v
   ```

   Debes ver `VERSION 2` junto a la distribución instalada.

> Si `wsl --install` indica que ya está instalado, ejecuta `wsl --update` y continúa.

---

## 3. Instalar Docker Desktop

1. Descarga **Docker Desktop for Windows** desde https://www.docker.com/products/docker-desktop/
2. Ejecuta el instalador y deja marcada la opción **"Use WSL 2 instead of Hyper-V"**.
3. Reinicia si te lo pide, abre **Docker Desktop** y acepta los términos.
4. Espera hasta que, abajo a la izquierda, aparezca el indicador verde **"Engine running"**. No continúes antes de eso.
5. Verifica en PowerShell:

   ```powershell
   docker --version
   docker compose version
   docker run --rm hello-world
   ```

   El último comando debe mostrar el mensaje *"Hello from Docker!"*.

### (Recomendado) Limitar la memoria de WSL

Por defecto WSL puede consumir mucha RAM. Crea el archivo `C:\Users\TU_USUARIO\.wslconfig` con este contenido:

```ini
[wsl2]
memory=4GB
processors=2
```

Luego aplica el cambio:

```powershell
wsl --shutdown
```

y vuelve a abrir Docker Desktop. Si Airflow se reinicia constantemente por falta de memoria, sube `memory` a `6GB`.

---

## 4. Obtener el proyecto

1. Descomprime el `.zip` del proyecto en una ruta **sin espacios ni tildes**, por ejemplo `C:\proyectos\paradigmas`.
2. Abre PowerShell dentro de esa carpeta (o usa `cd`):

   ```powershell
   cd C:\proyectos\paradigmas
   ls
   ```

   Debes ver `docker-compose.yml`, `airflow`, `mysql`, `mongodb`, `python`, etc.

---

## 5. Revisar el Dockerfile de Airflow

El archivo `airflow\Dockerfile` **debe quedar exactamente así** (usa el *constraints* oficial de Airflow para evitar conflictos de versiones y `build-essential` para compilar el driver de MySQL). Si el tuyo es distinto, reemplázalo:

```dockerfile
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
```

---

## 6. Configurar las variables de entorno

Docker Compose solo lee un archivo llamado exactamente **`.env`** (no `_env`, no `.env.txt`). Créalo a partir del ejemplo:

```powershell
Copy-Item .env.example .env
notepad .env
```

Contenido por defecto:

```ini
MYSQL_ROOT_PASSWORD=root
AIRFLOW_ADMIN_USER=admin
AIRFLOW_ADMIN_PASSWORD=admin
AIRFLOW_ADMIN_FIRSTNAME=Tu
AIRFLOW_ADMIN_LASTNAME=Nombre
AIRFLOW_ADMIN_EMAIL=tu_correo@dominio.com
```

| Variable | Descripción |
|---|---|
| `MYSQL_ROOT_PASSWORD` | Contraseña del usuario `root` de MySQL |
| `AIRFLOW_ADMIN_USER` / `AIRFLOW_ADMIN_PASSWORD` | Usuario y clave para entrar a la web de Airflow |
| `AIRFLOW_ADMIN_FIRSTNAME`, `AIRFLOW_ADMIN_LASTNAME`, `AIRFLOW_ADMIN_EMAIL` | Datos del administrador de Airflow |

**Importante:**

- Los notebooks `python/etl_MYSQL.ipynb` tienen la conexión escrita con la clave **`root`** (`mysql+pymysql://root:root@127.0.0.1:3310/...`). Si cambias `MYSQL_ROOT_PASSWORD`, también debes cambiarla en esas líneas de los notebooks.
- No uses el carácter `$` en las contraseñas: Docker Compose lo interpreta como una variable.
- Nunca subas el archivo `.env` a Git.
- **Las credenciales se aplican solo la primera vez** que se crean los volúmenes. Si las cambias después, debes hacer un reinicio completo (ver sección 10.5).

---

## 7. Construir y levantar todo (primera vez)

Desde la carpeta del proyecto:

```powershell
docker compose up -d --build
```

- La **primera vez tarda entre 5 y 15 minutos**: descarga `mysql`, `mongo` y `airflow`, y construye la imagen de Airflow.
- `-d` ejecuta los contenedores en segundo plano.

Sigue el arranque de Airflow en vivo:

```powershell
docker compose logs -f airflow
```

Cuando veas que el webserver ya está escuchando en el puerto 8080 (mensajes de *gunicorn* / *Listening at*), presiona `Ctrl + C` (esto **no** detiene los contenedores, solo deja de mostrar el log).

> Airflow espera a que MySQL esté *healthy*, y MySQL tarda ~1 minuto la primera vez porque ejecuta los scripts SQL de carga. Es normal ver reintentos de conexión durante ese tiempo.

---

## 8. Verificar que todo funciona

### 8.1 Estado de los contenedores

```powershell
docker compose ps
```

Debes ver tres servicios en estado `running`, y `mysql` como `healthy`.

### 8.2 MySQL

```powershell
docker compose exec mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "SHOW DATABASES;"'
```

Deben aparecer: `airflow`, `db_movies_netflix_transact` y `dw_netflix`.

Conexión desde herramientas externas (DBeaver, Workbench, notebooks):

| Dato | Valor |
|---|---|
| Host | `127.0.0.1` |
| Puerto | `3310` |
| Usuario | `root` |
| Contraseña | la de `MYSQL_ROOT_PASSWORD` |

### 8.3 MongoDB

```powershell
docker compose exec mongodb mongosh papeleria --eval "db.inventario.countDocuments()"
```

Debe devolver un número mayor que 0. Cadena de conexión: `mongodb://localhost:27017`.

### 8.4 Airflow

1. Abre http://localhost:8080
2. Ingresa con `AIRFLOW_ADMIN_USER` / `AIRFLOW_ADMIN_PASSWORD` de tu `.env`.
3. Comprueba la versión desde consola:

   ```powershell
   docker compose exec airflow airflow version
   ```

   Debe responder `2.10.2`.

---

## 9. Ejecutar el ETL en Airflow

1. En http://localhost:8080 busca el DAG **`etl_dependencias`**.
2. Actívalo con el interruptor de la izquierda (*Unpause*).
3. Pulsa el botón ▶ (**Trigger DAG**).
4. Entra al DAG → pestaña **Graph** para ver las tareas: `mostrar_fecha_hora` → (`etl_transacciones` y `etl_dw`) → `combinar_datos`. Todas deben terminar en verde.
5. Los resultados se guardan en la carpeta `mysql\data` de tu PC:
   - `etl_award.csv`
   - `etl_transacciones.csv`
   - `etl_combinado.csv`

Si una tarea falla (rojo): clic en la tarea → **Logs**. También puedes verlo con:

```powershell
docker compose logs airflow --tail 100
```

---

## 10. Comandos para administrar el entorno

### 10.1 Ver el estado y los logs

```powershell
docker compose ps                         # estado de los servicios
docker compose logs -f airflow            # log en vivo de Airflow (Ctrl+C para salir)
docker compose logs mysql --tail 50       # últimas 50 líneas de MySQL
docker compose logs mongodb --tail 50     # últimas 50 líneas de MongoDB
docker stats                              # uso de CPU y RAM (Ctrl+C para salir)
```

### 10.2 Detener y volver a iniciar (sin perder datos)

```powershell
docker compose stop                       # detiene los contenedores (los conserva)
docker compose start                      # los vuelve a iniciar
docker compose restart airflow            # reinicia solo un servicio
```

### 10.3 Apagar y eliminar contenedores (los datos se conservan)

```powershell
docker compose down                       # elimina contenedores y red; conserva volúmenes
docker compose up -d                      # los crea de nuevo; los datos siguen ahí
```

### 10.4 Reconstruir la imagen de Airflow (después de cambiar el Dockerfile)

```powershell
docker compose build --no-cache airflow
docker compose up -d
```

### 10.5 Borrar TODO y empezar de cero

> **Atención:** esto elimina las bases de datos (MySQL y MongoDB) y todo lo que hayas guardado en ellas. Los scripts SQL y `papeleria.js` se vuelven a cargar desde cero.

```powershell
# 1) Eliminar contenedores, volúmenes (datos), imágenes construidas y contenedores huérfanos
docker compose down -v --rmi all --remove-orphans

# 2) Limpiar la caché de construcción
docker builder prune -af

# 3) Borrar logs viejos de Airflow y CSV generados por el ETL
Remove-Item -Recurse -Force .\airflow\logs\* -ErrorAction SilentlyContinue
Remove-Item .\mysql\data\etl_*.csv -ErrorAction SilentlyContinue

# 4) Volver a levantar todo
docker compose up -d --build
```

### 10.6 Entrar a un contenedor

```powershell
docker compose exec airflow bash                                       # terminal dentro de Airflow (escribe exit para salir)
docker compose exec mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' # consola MySQL (escribe exit para salir)
docker compose exec mongodb mongosh papeleria                          # consola MongoDB (escribe exit para salir)
```

### 10.7 Limpieza general de Docker (libera espacio en disco)

```powershell
docker system df                          # cuánto espacio usa Docker
docker system prune -a                    # elimina imágenes, contenedores y redes sin uso (pide confirmación)
docker volume ls                          # lista volúmenes
```

> `docker system prune -a` afecta a **todos** tus proyectos Docker, no solo a este. Úsalo con cuidado.

---

## 11. Notebooks de Python (opcional)

Los notebooks de `python\` y `mongodb\` se conectan a las bases desde tu PC (no desde Docker), por lo que **los contenedores deben estar levantados**.

1. Crea y activa un entorno virtual en la carpeta del proyecto:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   Si PowerShell bloquea el script, ejecuta una vez:

   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   ```

2. Instala las dependencias:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. El notebook `python\etl.ipynb` lee un archivo `.env` ubicado **en su misma carpeta**. Cópialo desde `mongodb`:

   ```powershell
   Copy-Item mongodb\.env python\.env
   ```

4. Abre el notebook en VS Code y selecciona como kernel el entorno `.venv`.

Parámetros usados por los notebooks:

| Notebook | Conexión |
|---|---|
| `python\etl_MYSQL.ipynb` | `mysql+pymysql://root:root@127.0.0.1:3310/<base>` |
| `python\etl.ipynb`, `mongodb\etl.ipynb` | `MONGO_URI=mongodb://localhost:27017`, `DB_NAME=papeleria`, `COLLECTION=inventario` |

---

## 12. Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `error during connect` / `Cannot connect to the Docker daemon` | Docker Desktop no está abierto o aún arranca | Abre Docker Desktop y espera a **Engine running** |
| `docker: command not found` | Docker no instalado o PowerShell abierto antes de instalarlo | Cierra y abre PowerShell; revisa la sección 3 |
| `airflow: command not found` en el log | Imagen construida con el Dockerfile antiguo o en caché | Revisa la sección 5 y ejecuta `docker compose down -v --rmi all` y luego `docker compose up -d --build` |
| `port is already allocated` / `address already in use` | Otro programa usa el puerto 3310, 27017 u 8080 | Cierra ese programa o cambia el puerto izquierdo en `docker-compose.yml` (ej. `"3311:3306"`) y repite `docker compose up -d` |
| Airflow no deja entrar con mi usuario/clave | El usuario se crea solo la primera vez; cambiar el `.env` después no lo actualiza | Reinicio completo (sección 10.5) o `docker compose exec airflow airflow users reset-password -u TU_USUARIO` |
| Las bases `db_movies_netflix_transact` o `dw_netflix` no existen | Los scripts SQL solo corren cuando el volumen está vacío | Reinicio completo (sección 10.5) |
| `mysql` no llega a `healthy` | Aún está inicializando o la clave del `.env` cambió con datos ya creados | Espera 1–2 minutos; si persiste, `docker compose logs mysql` y reinicio completo |
| `airflow` reiniciándose en bucle | Falta de memoria o MySQL aún no listo | Sube la memoria en `.wslconfig` (sección 3) y revisa `docker compose logs airflow --tail 100` |
| `mongodb` reiniciándose en bucle | CPU sin instrucciones AVX (equipos muy antiguos o algunas VM) | En `docker-compose.yml` cambia `mongo:6.0` por `mongo:4.4` |
| Los notebooks fallan con `Access denied` | Contraseña distinta a `root` | Ajusta la clave en las conexiones del notebook (sección 6) |
| `etl.ipynb` falla por `MONGO_URI` vacío | Falta el `.env` junto al notebook | `Copy-Item mongodb\.env python\.env` |
| Error al descargar imágenes | Sin internet o proxy/firewall institucional | Prueba otra red o configura el proxy en Docker Desktop → Settings → Resources → Proxies |

---

## 13. Resumen rápido

```powershell
# Primera vez
Copy-Item .env.example .env
docker compose up -d --build

# Uso diario
docker compose start            # encender
docker compose stop             # apagar (conserva datos)

# Ver qué pasa
docker compose ps
docker compose logs -f airflow

# Empezar de cero (borra datos)
docker compose down -v --rmi all --remove-orphans
docker builder prune -af
docker compose up -d --build
```

| Qué | Dónde |
|---|---|
| Airflow | http://localhost:8080 |
| MySQL | `127.0.0.1:3310` (usuario `root`) |
| MongoDB | `mongodb://localhost:27017` |

---

## 14. Estructura del proyecto

```text
.
├── docker-compose.yml        # Define los 3 servicios
├── .env.example              # Plantilla de variables (copiar a .env)
├── requirements.txt          # Dependencias de Python para los notebooks
├── airflow/
│   ├── Dockerfile            # Imagen de Airflow con providers MySQL/Mongo
│   ├── dags/etl_DAG.py       # DAG "etl_dependencias"
│   ├── logs/                 # Logs de Airflow (se generan solos)
│   └── plugins/
├── mysql/
│   ├── 0-create-airflow-db.sql
│   ├── db_movies_neflix_transact.sql
│   ├── data_warehouse_netflix.sql
│   └── data/                 # CSV de entrada y salida del ETL (montado en /data)
├── mongodb/
│   ├── papeleria.js          # Carga inicial de datos
│   ├── etl.ipynb
│   └── .env                  # Parámetros de conexión para el notebook
└── python/
    ├── etl.ipynb
    └── etl_MYSQL.ipynb
```
