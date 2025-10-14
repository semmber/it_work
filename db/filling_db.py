import psycopg2
from psycopg2 import extras
import os
from dotenv import load_dotenv
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
    with psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("HOST"),
            port=os.getenv("PORT")
        ) as conn:
        with conn.cursor as cur:
            list_for_vacancies = []
            list_for_work_format = []
            list_for_skills = []
            for vac in vacancies:
                try:
                    id_vac = int(vac[0])
                    id_profession = get_profession_id(conn, vac[1])
                    id_experience = get_experience_id(conn, vac[2])
                    salary = (vac[3] or {}).get('salary_avg')
                    date = vac[4]
                    work_format = vac[5]
                    skills = vac[6]

                    list_for_vacancies.append((id_vac, id_profession , id_experience, salary, date))
                    list_for_work_format.append((id_vac, work_format))
                    list_for_skills.append((id_vac, skills))
                except Exception as e:
                    print("Пропускаю вакансию из-за:", e)
            insert_vacancy(cur, list_for_vacancies)
            insert_skills(cur, list_for_work_format)
            insert_skills(cur, list_for_skills)



def get_profession_id(conn, name:str) -> int:
    with (conn.cursor() as cursor):
        cursor.execute("SELECT profession_id FROM profession WHERE name = %s", (name,))     # (name,) - потому что в execute передаётся кортеж, если без кортежа, то он начнёт разбивать строку на буквы
        return int(cursor.fetchall()[0][0])


def get_experience_id(conn, exp:dict) -> int:
    with (conn.cursor() as cursor):
        cursor.execute("SELECT experience_id FROM experience WHERE name = %s", (exp['name'],))
        id_ = cursor.fetchone()
        if len(id_) == 0:
            cursor.execute(
                "INSERT INTO experience (code, name) VALUES (%s, %s) "
                "ON CONFLICT (name) DO NOTHING"
                "RETURNING experience_id",
                (exp['id'], exp['name'])
            )
            id_ = cursor.fetchone()
            conn.commit()
        return int(id_[0])


def insert_vacancy(cur, list_for_vacancies:list):
    if list_for_vacancies:
        query = ("INSERT INTO vacancy (vacancy_id, profession_id, experience_id,"
                 "salary_avg, created_at) VALUES %s"
                 "ON CONFLICT (vacancy_id) DO UPDATE"
                 "SET profession_id = EXCLUDED.profession_id, "
                 "experience_id = EXCLUDED.experience_id,"
                 "salary_avg = EXCLUDED.salary_avg, "
                 "created_at = EXCLUDED.created_a")
        extras.execute_values(cur, query, list_for_vacancies, page_size=100)
    else:
        print("Список вакансий пуст")


def insert_work_format(cur, list_for_work_format:list):
    if list_for_work_format:
        pairs = []
        for rows_by_vacancy in list_for_work_format:
            work_formats = [(d.get('id'), d.get('name')) for d in rows_by_vacancy[1]
                            if d.get('id') is not None and d.get('name') is not None]     # преобразование списка словарей в список кортежей
            if work_formats:
                query = ("INSERT INTO work_format (code, name) VALUES %s "
                         "ON CONFLICT (code) DO NOTHING"
                         "RETURNING work_format_id")
                extras.execute_values(cur, query, work_formats, page_size=100)
                ids = cur.fetchall()
                pairs.extend([(rows_by_vacancy[0], id_work_format) for id_work_format in ids
                        if ids])
        query = ("INSERT INTO vacancy_work_format (vacancy_id, work_format_id) VALUES %s "
                 "ON CONFLICT (vacancy_id, work_format_id) DO NOTHING")
        extras.execute_values(cur, query, pairs, page_size=1000)
    else:
        print("Список форматов работы пуст")


def insert_skills(cur, list_for_skills:list):
    if list_for_skills:
        pairs = []
        for rows_by_vacancy in list_for_skills:
            skills = [d for d in rows_by_vacancy[1]
                        if rows_by_vacancy[1] is not None]
            if skills:
                query = ("INSERT INTO work_format (name) VALUES %s "
                         "ON CONFLICT (name) DO NOTHING"
                         "RETURNING skill_id")
                extras.execute_values(cur, query, skills, page_size=1000)
                ids = cur.fetchall()
                pairs.extend([(rows_by_vacancy[0], id_work_format) for id_work_format in ids
                        if ids])
        query = ("INSERT INTO vacancy_skill (vacancy_id, skill_id) VALUES %s "
                 "ON CONFLICT (vacancy_id, skill_id) DO NOTHING")
        extras.execute_values(cur, query, pairs, page_size=1000)
    else:
        print("Список навыков пуст")
