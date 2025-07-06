# backend/utils/skill_extraction.py
import re

# maintain your own curated list of tech keywords
KNOWN_TECH = [
    "python","java","c#","c++","javascript","node","react","angular",
    "rest","api","docker","kubernetes","aws","azure","gcp","terraform",
    "ci/cd","jenkins","git","sql","nosql","spark","airflow"
]

def extract_tech_keywords(text: str) -> list[str]:
    text = text.lower()
    found = set()
    for kw in KNOWN_TECH:
        # simple word-boundary match
        if re.search(rf"\b{re.escape(kw)}\b", text):
            found.add(kw)
    return list(found)


