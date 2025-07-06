# backend/main.py

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from backend.rag.retriever import Retriever
from backend.rag.rewrite   import Rewriter
from backend.utils.parse_resume import parse_bullets_with_subsections
from backend.utils.skill_extraction import extract_tech_keywords

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
    job_description: str = Form(...),
):
    # 1) Write the upload to a temp PDF file
    content  = await resume.read()
    tmp_path = os.path.join(tempfile.gettempdir(), resume.filename)
    with open(tmp_path, "wb") as f:
        f.write(content)

    # 2) Parse into (section, subsection, bullet) triples
    try:
        triples = parse_bullets_with_subsections(tmp_path)
    finally:
        os.remove(tmp_path)

    # 3) Extract tech-keywords from the JD
    tech_filter = extract_tech_keywords(job_description)

    # 4) For each bullet: retrieve examples via FAISS + rewrite via LLM
    results = []
    for section, subsection, original in triples:
        try:
            examples  = retriever.get_similar(original, k=3, tech_filter=tech_filter)
            rewritten = rewriter.rewrite(original, examples, job_description)
        except Exception:
            # fallback in case of any error
            rewritten = original

        results.append({
            "section":    section,
            "subsection": subsection,
            "original":   original,
            "rewritten":  rewritten,
        })

    return {"results": results}
