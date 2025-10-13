from vacancy_scraper.scrapers import get_professional_role_ids, get_vacancies
from vacancy_scraper.extractor import data_extractor
import vacancy_scraper.patterns_4_professional_role as p
import json
import psycopg2


# Тож самое с .env
# Или сделай в будущем, чтобы фронт передавал какие вакансии по регионам нужно подтягивать
category_id = 11    # Информационные технологии
area_id = 2     # Санкт-Петербург

headers = {
    "User-Agent": "it_work_project/0.1 (contact: sillabika@gmail.com)"
}




# try:
#     conn = psycopg2.connect(
#             dbname="it_work",
#             user="postgres",
#             password="2308",
#             host="localhost",
#             port="5432"
#         )
#     with (conn.cursor() as cur):
#         val = 'INSERT INTO profession (name) VALUES '
#         for prof in p.PATTERNS.keys():
#             val += f"('{prof}'),\n"
#         val = val[:-2] + ';'
#         cur.execute(val)
#     conn.commit()
#     conn.close()
# except Exception as e:
#     print(e)


role_ids = get_professional_role_ids(headers, category_id)
json_vac = get_vacancies(role_ids, area_id, headers)
vacancies = json.dumps(json_vac, indent=4, ensure_ascii=False)
data_extractor(json_vac, headers)

