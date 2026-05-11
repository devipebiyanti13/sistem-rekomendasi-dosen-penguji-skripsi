import psycopg2

def get_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="db_rekomendasi_dosen",
        user="postgres",
        password="12345",
        port="5432"
    )
    return conn