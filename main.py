from vacancy_scraper.scrapers import get_professional_role_ids, get_vacancies
from vacancy_scraper.extractor import data_extractor
import json


category_id = 11    # Информационные технологии
area_id = 2     # Санкт-Петербург

headers = {
    "User-Agent": "it_work_project/0.1 (contact: sillabika@gmail.com)"
}


role_ids = get_professional_role_ids(headers, category_id)
json_vac = get_vacancies(role_ids, area_id, headers)
vacancies = json.dumps(json_vac, indent=4, ensure_ascii=False)
data_extractor(json_vac, headers)
# print(vacancies)

