# backend/main.py

import re
import os
import tempfile
import json
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from backend.rag.retriever import Retriever
from backend.rag.rewrite   import Rewriter
from backend.utils.parse_resume       import (
    parse_bullets_with_subsections,
    extract_resume_technologies,
)
from backend.utils.skill_extraction   import extract_tech_keywords, KNOWN_TECH
from backend.utils.assessor           import assess_bullet_strength
from backend.utils.matcher            import parse_job_description, parse_resume_text, jaccard, tfidf_cosine, embed_cosine,semantic_resp_score,resp_block_score,verb_overlap
from backend.utils.parse_resume_llm import parse_bullets_llm
from starlette.concurrency import run_in_threadpool

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ask GPT to label each bullet for three missing-X issues
def detect_issues_llm(bullet: str, jd: str) -> dict:
    system = """
        You are a resume coach.  You’ll get a single bullet point and a job description.

        1) A “clear action verb” means a strong past-tense or present-tense verb at the very start of the bullet (e.g. Developed, Implemented, Led, Designed, Streamlined).

        2) A “quantification” is any numeric metric or count: percentages (30%), absolutes (10 users, $5K), time savings (reduced by 2 hours), ratios (5× faster), etc.

        3) A “technology mention” is any programming language, framework, tool, platform, database, or commercial software.  This includes (but is not limited to):
        – Languages & runtimes: Python, Java, C++, JavaScript, C#
        – Databases: SQL (MySQL, PostgreSQL, Oracle), NoSQL (MongoDB, Redis)
        – Frameworks & libraries: React, Angular, Django, Flask
        – Infrastructure: Docker, Kubernetes, AWS, Azure, GCP
        – CI/CD & tooling: Jenkins, Git, Terraform, Control-M, ServiceNow

        Return *exactly* this JSON schema (no extra keys, no prose):

        {
        "missing_action_verb": <true|false>,
        "missing_metric":      <true|false>,
        "missing_technology":  <true|false>
        }
        """
    user = f"""
        Job Description:
        {jd}

        Bullet:
        "{bullet}"

        JSON:
        """

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system", "content":system.strip()},
            {"role":"user",   "content":user.strip()},
        ],
        temperature=0.0,
        max_tokens=64,
    )
    text = resp.choices[0].message.content.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print("[detect_issues_llm] bad JSON:", text)
        # fallback to local logic
        _, local_issues = assess_bullet_strength(bullet)
        return {
            "missing_action_verb": "missing a clear action verb" in local_issues,
            "missing_metric":      "no quantifiable metric"    in local_issues,
            "missing_technology":  "no relevant technology mentioned" in local_issues,
        }


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

retriever = Retriever(index_path="data/faiss_index")
rewriter  = Rewriter()


@app.post("/match_score")
async def match_score(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    # 1) read resume, extract bullets
    content = await resume.read()
    tmp = os.path.join(tempfile.gettempdir(), resume.filename)
    with open(tmp,"wb") as f: f.write(content)
    bullets = [b for _,_,b in parse_bullets_with_subsections(tmp)]
    os.remove(tmp)

    # 2) parse resume skills/text and JD skills/text
    res_skills, res_reps, res_text = parse_resume_text(bullets)
    jd_skills, jd_reps,   jd_text   = parse_job_description(job_description)
    print(">>> jd_reps:", jd_reps)
    res_bullets = bullets  # from parse_bullets_with_subsections
    resp_score = resp_block_score(jd_reps, res_bullets)
    # resp_score = semantic_resp_score(jd_reps, res_bullets)
    # now jd_reps actually has the “What You’ll Do” lines
    skill_score = jaccard(res_skills, jd_skills)
    # resp_score  = jaccard(res_reps, jd_reps)
    tfidf_score = tfidf_cosine(res_text, jd_text)
    embed_score = embed_cosine(res_text, jd_text)
    print(">>> embed_score:", embed_score)
    print(">>> resp_score:", resp_score)
    print(">>> skill_score:", skill_score)
    verb_score = verb_overlap(jd_reps, bullets)
    print(">>> verb_score:", verb_score)
    overall    = 0.35 * skill_score + 0.35 * resp_score + 0.2 * embed_score + 0.1 * verb_score
    # overall = 0.4 * skill_score + 0.4 * resp_score + 0.2 * embed_score

    return {
        "skill_match_pct": round(skill_score * 100, 1),
        "resp_match_pct":  round(resp_score  * 100, 1),
        "semantic_pct":    round(tfidf_score * 100, 1),
        "overall_pct":     round(overall     * 100, 1),
    }

@app.post("/review")
async def review(
    resume: UploadFile = File(...),
    job_description: str   = Form(...),
):
    # 1) Save PDF to temp
    content  = await resume.read()
    tmp_path = os.path.join(tempfile.gettempdir(), resume.filename)
    with open(tmp_path, "wb") as f:
        f.write(content)

    # 2) Parse bullets + sections
    triples = parse_bullets_llm(tmp_path)
    # triples = await run_in_threadpool(parse_bullets_llm, tmp_path)
    print(">>> triples:", triples)
    # 3) Pull out candidate’s own tech‐stack, then delete file
    resume_techs = extract_resume_technologies(tmp_path)
    os.remove(tmp_path)

    # 4) Extract JD’s desired stack
    jd_techs = extract_tech_keywords(job_description)

    # 5) Build a master list of tech terms to look for
    master_techs = set(resume_techs) | set(KNOWN_TECH)

    results = []
    for section, subsection, original in triples:
        # A) strength assessment (verb + metric)
        # is_strong, issues = assess_bullet_strength(original)
        # A) use LLM to detect exactly which pieces are missing
        flags = detect_issues_llm(original, job_description)
        print(">>> flags:", flags)
        issues = []
        if flags.get("missing_action_verb"):
            issues.append("missing a clear action verb")
        if flags.get("missing_metric"):
            issues.append("no quantifiable metric")
        if flags.get("missing_technology"):
            issues.append("no relevant technology mentioned")
        is_strong = len(issues) == 0

        # # B) tech‐mention check
        # has_any_tech = any(
        #     re.search(rf"\b{re.escape(t)}\b", original, re.IGNORECASE)
        #     for t in master_techs
        # )
        # if not has_any_tech:
        #     issues.append("no relevant technology mentioned")
        #     is_strong = False

        # # dedupe
        # issues = list(dict.fromkeys(issues))

        # C) decide rewrite path
        if is_strong:
            rewritten, rewrote = original, False
        else:
            # full RAG rewrite for any bullet with any issue
            examples  = retriever.get_similar(
                original, k=3, tech_filter=jd_techs
            )
            rewritten = rewriter.rewrite(
                original, examples, job_description, do_rewrite=True, issues=issues
            )
            rewrote   = True

        results.append({
            "section":    section,
            "subsection": subsection,
            "original":   original,
            "issues":     issues,
            "rewritten":  rewritten,
            "rewrote":    rewrote,
        })

    return {"results": results}
