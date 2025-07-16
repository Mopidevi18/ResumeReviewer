# backend/utils/matcher.py

import re
from typing import List, Set
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
# optionally for embeddings:
from sentence_transformers import SentenceTransformer
# backend/utils/matcher.py
from sklearn.metrics.pairwise import cosine_similarity
from backend.utils.skill_extraction import KNOWN_TECH
import numpy as np
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

lemmatizer = WordNetLemmatizer()


# make sure this model is defined once at module‐scope

model = SentenceTransformer('all-MiniLM-L6-v2')

def parse_job_description(jd: str):
    """
    Return (skill_set, resp_set, full_text).
    - skill_set: intersection of KNOWN_TECH in jd
    - resp_set: set of 'What You’ll Do' lines, lowercased
    - full_text: jd itself
    """
    text = jd.lower()

    # 1) skills
    skills = {kw for kw in KNOWN_TECH if re.search(rf"\b{re.escape(kw)}\b", text)}

    # 2) responsibilities
    raw_reps = extract_responsibilities(jd)
    resps    = {r.lower() for r in raw_reps}

    return skills, resps, jd

def parse_resume_text(resume_bullets: List[str]):
    """
    Given your bullet list, return (skill_set, resp_set, full_text).
    """
    joined = "\n".join(resume_bullets).lower()
    skills = {kw for kw in KNOWN_TECH if re.search(rf"\b{re.escape(kw)}\b", joined)}
    # resp_set = bullet text themselves
    resps = {b.strip().lower() for b in resume_bullets}
    return skills, resps, joined


def resp_block_score(jd_reps: List[str], resume_bullets: List[str]) -> float:
    """Embed JD responsibilities block vs. entire resume bullets block."""
    if not jd_reps or not resume_bullets:
        return 0.0
    jd_block    = " ".join(jd_reps)
    resume_text = " ".join(resume_bullets)
    jd_emb, res_emb = model.encode([jd_block, resume_text], convert_to_tensor=False)
    return float(cosine_similarity(jd_emb.reshape(1,-1), res_emb.reshape(1,-1))[0,0])


def verb_overlap(jd_reps: List[str], bullets: List[str]) -> float:
    """
    Simple lemmatized token overlap without NLTK.  We just lowercase
    everything and split on non-word characters.
    """
    # flatten into one string each
    jd_text   = " ".join(jd_reps).lower()
    res_text  = " ".join(bullets).lower()

    # extract “words” (letters/numbers/underscore)
    tokens_jd  = set(re.findall(r"\b\w+\b", jd_text))
    tokens_res = set(re.findall(r"\b\w+\b", res_text))

    if not tokens_jd:
        return 0.0

    # simple Jaccard
    return len(tokens_jd & tokens_res) / len(tokens_jd)

def extract_responsibilities(text: str) -> List[str]:
    """
    Pull out the lines under “What You’ll Do” (or “Core Responsibilities”),
    handling both straight and curly apostrophes, and stop when you hit
    a blank line or the next ALL-CAPS section header.
    """
    lines    = text.splitlines()
    out      = []
    in_block = False

    # allow both ’ (U+2019) and ' (U+0027)
    start_rx = re.compile(r'^(what you[’\']ll do|core responsibilities)', re.IGNORECASE)
    stop_rx  = re.compile(r'^[A-Z][A-Za-z &’\'\-]*(?:\:)?$')

    for ln in lines:
        stripped = ln.strip()
        if not in_block:
            if start_rx.match(stripped):
                in_block = True
            continue

        # if we’ve entered the block, exit on blank or new section header
        if not stripped or stop_rx.match(stripped):
            break

        # strip leading bullets or dashes
        bulleted = stripped.lstrip('•–-0123456789. ')
        out.append(bulleted)

    return out



def semantic_resp_score(jd_reps, resume_bullets) -> float:
    """
    For each JD responsibility sentence, compute its embedding
    similarity to every resume bullet.  Take the max similarity
    for each JD line, then average those maxima.
    Returns a float in [0,1].
    """
    # convert from set -> list so we can index
    jd_list  = list(jd_reps)
    res_list = list(resume_bullets)

    if not jd_list or not res_list:
        return 0.0

    # encode both lists
    jd_embeds  = model.encode(jd_list,  convert_to_tensor=False)
    res_embeds = model.encode(res_list, convert_to_tensor=False)

    # jd_embeds and res_embeds are numpy arrays of shape (N, D) and (M, D)
    scores = []
    for jde in jd_embeds:
        sims = cosine_similarity(jde.reshape(1, -1), res_embeds)[0]
        scores.append(sims.max())

    return float(np.mean(scores))



def jaccard(a: Set, b: Set) -> float:
    if not b:
        return 0.0
    return len(a & b) / len(b)

def tfidf_cosine(a: str, b: str) -> float:
    vec = TfidfVectorizer().fit([a,b])
    m = cosine_similarity(vec.transform([a]), vec.transform([b]))[0,0]
    return float(m)

# optional: semantic
model = SentenceTransformer('all-MiniLM-L6-v2')
def embed_cosine(a: str, b: str):
    va, vb = model.encode([a, b])
    return float(cosine_similarity([va],[vb])[0,0])
