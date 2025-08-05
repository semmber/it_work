import requests
import json
import time

def data_extractor(vacancies:dict, headers:dict):
    for vac in vacancies["items"]:
        print(vac["name"])
        id_vac = vac["id"]
        skills = []
        full_vac = requests.get(f"https://api.hh.ru/vacancies/{id_vac}", headers=headers).json()
        print(extract_key_skills(full_vac))
        print(extract_salary(full_vac))
        print(extractor_work_hours(vac))
        print()
        time.sleep(0.25)
    return


def extract_key_skills(vacancy:dict) -> list | None:
    if vacancy["key_skills"] is None:
        return None
    skills = [skill["name"] for skill in vacancy["key_skills"]]
    return skills


def extract_salary(vacancy:dict) -> int | None:
    if vacancy["salary"] is None:
        return None
    salary_from = vacancy["salary"]["from"]
    salary_to = vacancy["salary"]["from"]
    if salary_from and salary_to:
        return int((salary_from + salary_to) / 2)
    elif salary_from:
        return salary_from
    elif salary_to:
        return salary_to
    else:
        return None


def extract_professional_role(vacancy:dict) -> str | None:
    if vacancy["professional_roles"] is None:
        return None
    return vacancy["professional_roles"]["name"]


def extractor_work_format(vacancy:dict) -> list | None:
    if vacancy["work_format"] is None:
        return None
    formats = [wf["name"] for wf in vacancy["work_format"]]
    return formats


def extractor_work_hours(vacancy:dict):
    if vacancy["working_hours"] is None:
        return None
    return vacancy["working_hours"]