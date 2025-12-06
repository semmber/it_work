import streamlit as st
import os
from dotenv import load_dotenv
import psycopg2, pandas as pd

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("HOST"),
    port=os.getenv("PORT")
)

query = """
    SELECT
            created_at::date AS date,
            COUNT(*) AS vacancies_count
        FROM vacancy
        GROUP BY created_at::date
        ORDER BY date;
    """

df = pd.read_sql_query(query, conn)
conn.close()

st.subheader("Сырые данные")
st.write(df.head())

st.subheader("График количества вакансий по дням")
st.line_chart(df, x="date", y="vacancies_count")