import psycopg

def get_connection():
    conn = psycopg.connect(
        host="localhost",
        database="db_rekomendasi_dosen",
        user="postgres",
        password="12345",
        port="5432"
    )
    return conn