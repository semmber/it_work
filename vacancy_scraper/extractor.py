import requests
import time
from vacancy_scraper.classifier_of_profession import score_profession

def data_extractor(vacancies:dict, headers:dict):
    data = []
    for vac in vacancies["items"]:
        id_vac = vac["id"]
        full_vac = requests.get(f"https://api.hh.ru/vacancies/{id_vac}", headers=headers).json()
        profession = score_profession(full_vac["name"], full_vac["description"], extract_key_skills(full_vac))
        if profession[0] != '':
            dt = []
            dt.extend([id_vac, profession[0], extract_experience(vac),
                         extract_salary(full_vac), extract_date(full_vac),
                         extract_work_format(full_vac), extract_key_skills(full_vac)])
            data.append(dt)
        time.sleep(0.25)
    print(data)
    return data


def extract_key_skills(vacancy:dict) -> list | None:
    if vacancy["key_skills"] is None:
        return None
    return [v["name"] for v in vacancy["key_skills"]]


def extract_salary(vacancy:dict) -> dict | None:
    salary = vacancy.get("salary")
    if salary is None or int(salary.get("from") or 0) < 28750:    # минимальная зарплата в спб + будет только в рублях
        return None
    salary_from = salary.get("from")
    salary_to = salary.get("to")
    if salary_from and salary_to:
        salary_avg = int((salary_from + salary_to) / 2)
        return {"salary_avg":salary_avg}
    elif salary_from:
        return {"salary_avg":salary_from}
    elif salary_to:
        return {"salary_avg":salary_to}
    else:
        return None


def extract_work_format(vacancy:dict) -> list | None:
    if vacancy["work_format"] is None:
        return None
    formats = [{"id":wf["id"], "name":wf["name"].replace("\xa0", " ")} for wf in vacancy["work_format"]]
    return formats


def extract_experience(vacancy:dict) -> dict | None:
    if vacancy["experience"] is None:
        return None
    return vacancy["experience"]


def extract_date(vacancy:dict) -> str | None:
    if vacancy["published_at"] is None:
        return None
    return vacancy["published_at"]
