import re, unicodedata, html
from vacancy_scraper.extractor import *

def normalize_text(text:str) -> str | None:
    if text is None:
        return None
    text = html.unescape(text)
    text = unicodedata.normalize('NFKD', text).replace('\xa0', ' ')
    text = re.sub(r'\s+', ' ', text.lower()).strip()
    return text

