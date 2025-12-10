import streamlit as st
import os
from dotenv import load_dotenv
import psycopg2, pandas as pd
from db import repositories as r

vacancies = r.get_all_vacancies()  # list[dict]
df = pd.DataFrame(vacancies)

st.subheader("Сырые данные")
st.write(df.head())

st.subheader("Линейный график")
st.line_chart(df, x="salary_avg", y="profession_id")