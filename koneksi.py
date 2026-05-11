import psycopg2
import streamlit as st

def get_connection():
    conn = psycopg2.connect(
        st.secrets["DATABASE_URL"]
    )
    return conn

