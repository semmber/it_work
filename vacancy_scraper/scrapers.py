import requests
import json
import time


def get_professional_role_ids(headers:dict, category_id:int) -> list:
    roles = requests.get("https://api.hh.ru/professional_roles", headers=headers).json()
    role_ids = []
    for cat in roles["categories"]:
        if int(cat["id"]) == category_id:
            role_ids = [role["id"] for role in cat["roles"]]
            break
    return role_ids

def get_vacancies(role_ids:list, area_id:int, headers:dict) -> dict:
    params = {
        "area": area_id,
        "per_page": 15,
        "page": 0,
        "professional_role": role_ids,
    }
    time.sleep(0.25)
    response = requests.get("https://api.hh.ru/vacancies", params=params, headers=headers).json()
    time.sleep(0.25)
    return response

