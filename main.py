from vacancy_scraper.scrapers import get_professional_role_ids, get_vacancies
from vacancy_scraper.extractor import data_extractor
import vacancy_scraper.patterns_4_professional_role as p
from db.filling_db import filling_db
import json
import psycopg2

filling_db()