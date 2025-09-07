import re, unicodedata, html
from vacancy_scraper.extractor import *
from vacancy_scraper.patterns_4_professional_role import *

def normalize_text(text:str) -> str | None:
    if text is None:
        return None
    text = html.unescape(text)
    text = unicodedata.normalize('NFKD', text).replace('\xa0', ' ')
    text = re.sub(r'\s+', ' ', text.lower()).strip()
    return text


def score_profession(name: str, desc: str, skills: list[str]) -> tuple[str, int] | None:
    n_name = normalize_text(name)
    n_desc = normalize_text(desc)

    if skills:
        list_skills = [normalize_text(s["name"]) for s in skills]
    else:
        list_skills = []
    n_skills = " ".join(list_skills).lower()

    best_prof, best_score = "", 0

    for prof, k_words in PATTERNS.items():
        score = 0
        n_prof = normalize_text(prof)

        if n_name:
            name_matches = sum(1 for pr in n_prof.lower().split() if pr in n_name)
            score += name_matches * 7

        for kw in k_words:
            if re.search(kw, n_name):
                score += 7
            if re.search(kw, n_desc):
                score += 2
            if re.search(kw, n_skills):
                score += 3

        if score > best_score:
            best_prof = prof
            best_score = score

    return (best_prof, best_score) if best_score >= 10 else ("", 0)
