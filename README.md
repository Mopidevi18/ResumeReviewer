# ResumeReviewer

An **AI-powered web application** that automates resume bullet refinement using **LLMs**, **RAG**, and **FAISS** vector search.

---

## 🚀 Project Overview

ResumeReviewer helps job seekers transform vague bullet points into targeted, metric-driven statements that align with a specific job description.

- **Parse** PDF resumes into structured sections and bullets via a parsing LLM.
- **Detect issues** in each bullet (missing action verbs, metrics, or key skills) using an LLM and heuristic fallbacks.
- **Retrieve examples** from a curated corpus with FAISS-powered RAG for semantic similarity.
- **Rewrite bullets** with an LLM guided by retrieved examples and job requirements.
- **Serve** results in a Streamlit front end, backed by FastAPI.

---

## 🔧 Key Technologies

- **FastAPI** – REST API backend  
- **Streamlit** – Interactive web UI  
- **PyMuPDF (fitz)** – PDF text extraction  
- **OpenAI GPT-4o-mini** – Parsing, issue detection, rewriting  
- **FAISS** (via LangChain) – Approximate nearest-neighbor search  
- **Pydantic** – Data validation and typing  

---

## Usage

1. **Upload** your resume PDF.  
2. **Paste** the job description you're targeting.  
3. Click **Review** to see:
   - ✅ **Already Strong** bullets  
   - ⚠️ **Needs Work** bullets with explanations & AI rewrites  





