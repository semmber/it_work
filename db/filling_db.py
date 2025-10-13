import json
import psycopg2
import os
from dotenv import load_dotenv
from vacancy_scraper.extractor import data_extractor
from vacancy_scraper.scrapers import get_professional_role_ids, get_vacancies
from vacancy_scraper.extractor import data_extractor

load_dotenv()

headers = {
    "User-Agent": "it_work_project/0.1 (contact: sillabika@gmail.com)"
}

def filling_db():
    role_ids = get_professional_role_ids(headers, int(os.getenv("CATEGORY_ID")))
    json_vac = get_vacancies(role_ids, int(os.getenv("AREA_ID")), headers)
    vacancies = data_extractor(json_vac, headers)
    for vac in vacancies:
        try:
            conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("HOST"),
                port=os.getenv("PORT")
            )
            id_vac = vac[0]
            id_profession = get_profession_id(conn, vac[1])
            id_experience = get_experience_id(conn, vac[2])

            query = ("INSERT INTO vacancy (vacancy_id, profession_id, experience_id,"
                     "salary_avg, created_at) VALUES (%s, %s, %s, %s, %s)", (...))
            with (conn.cursor() as cur):
                pass
            conn.close()
        except Exception as e:
            print(e)

def get_profession_id(conn, name:str):
    with (conn.cursor() as cursor):
        cursor.execute("SELECT profession_id FROM profession WHERE name = %s", (name,))     # (name,) - потому что в execute передаётся кортеж, если без кортежа, то он начнёт разбивать строку на буквы
        return int(cursor.fetchall()[0][0])


def get_experience_id(conn, exp:dict):
    with (conn.cursor() as cursor):
        cursor.execute("SELECT experience_id FROM experience WHERE name = %s", (exp['name'],))
        id_ = cursor.fetchall()
        if len(id_) == 0:
            cursor.execute("INSERT INTO experience (code, name) VALUES (%s, %s)", (exp['id'], exp['name']))
            conn.commit()
            cursor.execute("SELECT experience_id FROM experience WHERE name = %s", (exp['name'],))
            id_ = cursor.fetchall()
        return int(id_[0][0])







    #
    # with (conn.cursor() as cur):
    #     val = 'INSERT INTO profession (name) VALUES '
    #     for prof in p.PATTERNS.keys():
    #         val += f"('{prof}'),\n"
    #     val = val[:-2] + ';'
    #     cur.execute(val)
    # conn.commit()
    # conn.close()