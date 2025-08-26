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


def score_profession(name: str, desc: str, skills:list[str]) -> tuple[str, int] | None:
    n_name, n_desc = normalize_text(name), normalize_text(desc)
    list_skills = [s["name"].lower().strip() for s in (skills or [])]
    n_skills = ", ".join(list_skills)
    best_prof, best_score = "", 0
    for prof, k_words in PATTERNS.items():
        score = 0
        for pr in prof.lower().split():
            if pr in n_name:
                score += 7
        for kw in k_words:
            if bool(re.search(kw, n_name)):
                score += 7
            if bool(re.search(kw, n_desc)):
                score += 2
            if bool(re.search(kw, n_skills)):
                score += 3
        if score > best_score:
            best_score = score
            best_prof = prof
    if best_score < 7: return "", 0
    return best_prof, best_score
