# backend/main.py

import re
import os
import tempfile
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
    triples = parse_bullets_with_subsections(tmp_path)

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
        is_strong, issues = assess_bullet_strength(original)

        # B) tech‐mention check
        has_any_tech = any(
            re.search(rf"\b{re.escape(t)}\b", original, re.IGNORECASE)
            for t in master_techs
        )
        if not has_any_tech:
            issues.append("no relevant technology mentioned")
            is_strong = False

        # dedupe
        issues = list(dict.fromkeys(issues))

        # C) decide rewrite path
        if is_strong:
            rewritten, rewrote = original, False

        else:
            # 1) structural fix: missing verb → always full RAG rewrite
            if "missing a clear action verb" in issues:
                examples  = retriever.get_similar(
                    original, k=3, tech_filter=jd_techs
                )
                rewritten = rewriter.rewrite(
                    original, examples, job_description, do_rewrite=True
                )
                rewrote   = True

            # 2) exactly both metric+tech missing → double hint
            elif set(issues) == {"no quantifiable metric", "no relevant technology mentioned"}:
                metric_hint = rewriter.suggest_metric(original, job_description)
                # pick first JD tech if available, else resume tech
                tech_hint   = (jd_techs + resume_techs)[0] if (jd_techs or resume_techs) else "[add relevant technology]"
                rewritten   = f"{original} — {metric_hint} — implemented using {tech_hint}"
                rewrote     = True

            # 3) only metric missing → single metric hint
            elif "no quantifiable metric" in issues:
                metric_hint = rewriter.suggest_metric(original, job_description)
                rewritten   = f"{original} — {metric_hint}"
                rewrote     = True

            # 4) only tech missing → single tech hint
            elif "no relevant technology mentioned" in issues:
                tech_hint  = (jd_techs + resume_techs)[0] if (jd_techs or resume_techs) else "[add relevant technology]"
                rewritten  = f"{original} — implemented using {tech_hint}"
                rewrote    = True

            # 5) anything else (e.g. odd combos) → full RAG
            else:
                examples  = retriever.get_similar(
                    original, k=3, tech_filter=jd_techs
                )
                rewritten = rewriter.rewrite(
                    original, examples, job_description, do_rewrite=True
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
