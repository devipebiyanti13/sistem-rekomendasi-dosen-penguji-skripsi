import psycopg2
import streamlit as st

def get_connection():
    conn = psycopg2.connect(
        st.secrets["postgresql://neondb_owner:npg_Rp8IWxtwn7gU@ep-twilight-base-ao1uwnfy-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"]
    )
    return conn

