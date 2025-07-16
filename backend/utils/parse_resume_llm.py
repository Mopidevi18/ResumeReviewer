# backend/utils/parse_resume_llm.py
import fitz
import json
import os
import re
from openai import OpenAI
from typing import List, Tuple

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def _extract_raw_text(path: str) -> str:
    doc = fitz.open(path)
    pages = [page.get_text() for page in doc]
    return "\n".join(pages)

def parse_bullets_llm(path: str) -> List[Tuple[str, str, str]]:
    raw = _extract_raw_text(path)
    prompt = f"""
You are a resume parser. From the following resume text, extract three sections: "Experience", "Internships", and "Projects". 
For each, output **ONLY** a JSON array of objects, where each object has:
  - "section": the section name,
  - "subsection": either a sub-header or `"General"`,
  - "bullet": the bullet point text.

Example output format (exactly, with no extra prose):
[
  {{ "section": "Experience", "subsection": "General", "bullet": "Built feature X..." }},
  ...
]

Resume text:
\"\"\"{raw}\"\"\"
"""
    resp = client.chat.completions.create(
      model="gpt-4o-mini",
      messages=[
        {"role": "system", "content": "You are a helpful parser that outputs bare JSON."},
        {"role": "user",   "content": prompt}
      ],
      temperature=0.0,
      max_tokens=1500
    )

    content = resp.choices[0].message.content.strip()
    # pull out the first [...] block
    m = re.search(r'(\[.*\])', content, flags=re.DOTALL)
    if not m:
        raise ValueError(f"Unable to find a JSON array in model output:\n{content!r}")
    arr_text = m.group(1)

    data = json.loads(arr_text)
    return [(item["section"], item["subsection"], item["bullet"]) for item in data]
