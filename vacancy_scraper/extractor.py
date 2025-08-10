import requests
import json
import time

def data_extractor(vacancies:dict, headers:dict):
    for vac in vacancies["items"]:
        print(vac["name"])
        id_vac = vac["id"]
        full_vac = requests.get(f"https://api.hh.ru/vacancies/{id_vac}", headers=headers).json()
        print(json.dumps(full_vac, indent=4, ensure_ascii=False))
        print(extract_key_skills(full_vac))
        print(extract_salary(full_vac))
        print(extract_professional_role(full_vac))
        print(extractor_work_format(vac))
        print(extractor_work_hours(vac))
        print(extractor_experience(vac))
        print()
        time.sleep(0.25)
    return


def extract_key_skills(vacancy:dict) -> list | None:
    if vacancy["key_skills"] is None:
        return None
    skills = [skill["name"] for skill in vacancy["key_skills"]]
    return vacancy["key_skills"]


def extract_salary(vacancy:dict) -> dict | None:
    if vacancy["salary"] is None:
        return None
    salary_from = int(vacancy["salary"]["from"])
    salary_to = vacancy["salary"]["to"] if vacancy["salary"]["to"] is not None else 0
    if salary_from and salary_to:
        salary_avg = int((salary_from + salary_to) / 2)
        return {"salary_from":salary_from, "salary_to":salary_to, "salary_avg":salary_avg}
    elif salary_from:
        return {"salary_from":salary_from}
    elif salary_to:
        return {"salary_to":salary_to}
    else:
        return None


def extract_professional_role(vacancy:dict) -> list | None:
    if vacancy["professional_roles"] is None:
        return None
    return [pr for pr in vacancy["professional_roles"]]


def extractor_work_format(vacancy:dict) -> list | None:
    if vacancy["work_format"] is None:
        return None
    formats = [{"id":wf["id"], "name":wf["name"].replace("\xa0", " ")} for wf in vacancy["work_format"]]
    return formats


def extractor_work_hours(vacancy:dict) -> list | None:
    if vacancy["working_hours"] is None:
        return None
    list_hours = [i["id"] for i in vacancy["working_hours"]]
    return list_hours


def extractor_experience(vacancy:dict) -> dict | None:
    if vacancy["experience"] is None:
        return None
    return vacancy["experience"]

