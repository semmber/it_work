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


def score_profession(name: str, desc: str, skills:list[str]) -> str | None:
    n_name, n_desc = normalize_text(name), normalize_text(desc)
    n_skills = [s["name"].lower().strip() for s in (skills or [])]
    best_prof, best_score = "", 0
    for prof, k_words in PATTERNS.items():
        score = 0
        for pr in prof.lower().strip():
            if pr in n_name:
                score += 7
        # if n_name == prof.lower():
        #     score += 5
        for kw in k_words:
            if kw in n_desc:
                score += 2
            if kw in n_skills:
                score += 3
        if score > best_score:
            best_score = score
            best_prof = prof
    return best_prof
