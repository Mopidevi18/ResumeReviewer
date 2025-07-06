# backend/main.py

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from backend.rag.retriever import Retriever
from backend.rag.rewrite   import Rewriter
from backend.utils.parse_resume       import parse_bullets_with_subsections
from backend.utils.skill_extraction   import extract_tech_keywords
from backend.utils.assessor           import assess_bullet_strength

import os
import tempfile

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
    job_description: str   = Form(...)
):
    # 1) Save uploaded PDF to a temp file
    content  = await resume.read()
    tmp_path = os.path.join(tempfile.gettempdir(), resume.filename)
    with open(tmp_path, "wb") as f:
        f.write(content)

    # 2) Parse into (section, subsection, bullet)
    triples = parse_bullets_with_subsections(tmp_path)
    os.remove(tmp_path)

    # 3) Extract tech‐filter from JD
    tech_filter = extract_tech_keywords(job_description)

    # 4) Loop and conditionally rewrite
    results = []
    for section, subsection, original in triples:
        # 4a) Assess bullet strength
        is_strong, issues = assess_bullet_strength(original)

        if is_strong:
            # skip RAG+rewrite
            rewritten  = original
            did_rewrite = False
        else:
            # retrieve relevant snippets
            examples = retriever.get_similar(
                text=original,
                k=3,
                tech_filter=tech_filter
            )
            # rewrite under guardrails
            rewritten  = rewriter.rewrite(
                original,
                examples,
                job_description,
                do_rewrite=True
            )
            did_rewrite = True

        results.append({
            "section":    section,
            "subsection": subsection,
            "original":   original,
            "issues":     issues,
            "rewritten":  rewritten,
            "rewrote":    did_rewrite,
        })

    return {"results": results}
