from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import pymysql

# Conexión MySQL (desde dentro del contenedor Airflow)
def get_connection():
    return pymysql.connect(
        host='host.docker.internal',
        port=3310,
        user='root',
        password='root',
        database='db_movies_netflix_transact'
    )

# Tarea 1: ETL de tabla de películas
def etl_transacciones():
    movies_award=pd.read_csv("/data/Awards_movie.csv")
    movies_award["movieID"]=movies_award["movieID"].astype('int')
    movies_award.rename(columns={"Aware":"Award"}, inplace=True)
    movies_award.to_csv('/data/etl_award.csv', index=False)
    

# Tarea 2: ETL del DW
def etl_dw():
    conn = get_connection()
    query = """
    SELECT 
        movie.movieID as movieID, movie.movieTitle as title, movie.releaseDate as releaseDate, 
        gender.name as gender , person.name as participantName, participant.participantRole as roleparticipant 
    FROM movie 
    INNER JOIN participant 
    ON movie.movieID=participant.movieID
    INNER JOIN person
    ON person.personID = participant.personID
    INNER JOIN movie_gender 
    ON movie.movieID = movie_gender.movieID
    INNER JOIN gender 
    ON movie_gender.genderID = gender.genderID
    """

    movies_data=pd.read_sql(query, con=conn) 
    movies_data["movieID"]=movies_data["movieID"].astype('int')
    movies_data.to_csv('/data/etl_transacciones.csv', index=False)
    conn.close()
    
    

# Tarea 3: combinación de resultados (solo depende de tarea_2)
def combinar_etl():
    df1 = pd.read_csv('/data/etl_transacciones.csv')
    df2 = pd.read_csv('/data/etl_award.csv')
    df_final = pd.concat([df1, df2], axis=1)
    df_final.to_csv('/data/etl_combinado.csv', index=False)

# Definición del DAG
with DAG(
    dag_id="etl_dependencias",
    description="ETL por etapas con dependencias en Airflow",
    start_date=datetime(2024, 4, 1),
    schedule_interval="0 0 * * *",  # se ejecuta todos los días a las 00:00
    catchup=False,
    tags=["ETL", "Airflow", "MySQL"]
) as dag:


    mostrar_fecha_hora = BashOperator(
        task_id="mostrar_fecha_hora",
        bash_command="echo 'Hora actual:' && date"
    )

    tarea_1 = PythonOperator(
        task_id="etl_transacciones",
        python_callable=etl_transacciones
    )

    tarea_2 = PythonOperator(
        task_id="etl_dw",
        python_callable=etl_dw
    )

    tarea_3 = PythonOperator(
        task_id="combinar_datos",
        python_callable=combinar_etl
    )

    # Dependencias
    mostrar_fecha_hora >> [tarea_1, tarea_2]
    tarea_1 >> tarea_3
    tarea_2 >> tarea_3
