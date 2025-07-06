#!/usr/bin/env python3
import os
import json
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

# 0. Load .env (optional) so you can keep your key in a .env file
load_dotenv()

# 1. Read your API key from the OPENAI_API_KEY env var
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not set. Add it to your environment or a .env file.")

# 2. Initialize the client with your key
client = OpenAI(api_key=api_key)

print("Generating resumes…")

# 3. Build the messages
system_msg = {
    "role": "system",
    "content": "You are a helpful assistant that outputs only valid JSON."
}
user_msg = {
    "role": "user",
    "content": """
Generate 20 anonymized Software Engineer resumes as a JSON array, each conforming exactly to this schema:
{
  "personal_info": { "name": "", "phone": ""},
  "seniority": "",      // "junior", "mid", or "senior"
  "education": [{ "degree": "", "major": "", "school": "", "location": "", "dates": "" }],
  "technical_skills": [""],
  "experience": [{ "title": "", "company": "", "location": "", "dates": "", "bullets": [""] }],
  "internships": [{ "title": "", "company": "", "location": "", "dates": "", "bullets": [""] }],
  "projects": [{ "name": "", "technologies": [""], "description": "" }],
  "leadership_awards": [""]
}
- 5 junior (0–2 yrs), 10 mid (3–5 yrs), 5 senior (6+ yrs)
- Set `"seniority"` appropriately for each resume.
- For **every** “bullets” array:
  1. Start with a past-tense action verb (the **task**).
  2. Where appropriate, include a **result**—either quantitative (“by 25%”) or a **clear outcome** (“to improve code quality”).
  3. Keep bullets to **8–15 words**.
  4. **Generate 3–5 bullets** per role.
"""
}

# 4. Call the API
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[system_msg, user_msg],
    temperature=0.7,
    max_tokens=12000
)
content = resp.choices[0].message.content

# DEBUG: print what we got
print("Raw model output:")
print(content)


# ——— STRIP CODE FENCES ———
# If the model wrapped its JSON in ```…``` remove those lines
lines = content.splitlines()
if lines and lines[0].startswith("```"):
   # drop first fence line
   lines = lines[1:]
if lines and lines[-1].startswith("```"):
   # drop last fence line
   lines = lines[:-1]
content = "\n".join(lines).strip()

assert content.lstrip().startswith("["), "Expected JSON array after stripping fences"

# 5. Parse and save JSON
try:
    resumes = json.loads(content)
except json.JSONDecodeError as err:
    print("JSON parse error:", err)
    print("Content was:", content[:500])
    raise

with open("resumes.json", "w") as f_json:
    json.dump(resumes, f_json, indent=2)


# 6. Flatten to CSV (include both experience and internships)
exp_df = pd.json_normalize(
    resumes,
    record_path=["experience"],
    meta=[
      ["personal_info", "name"],
      "seniority",
      ["education"],
      ["technical_skills"],
      ["projects"],
      ["leadership_awards"]
    ],
    errors="ignore"
)

int_df = pd.json_normalize(
    resumes,
    record_path=["internships"],
    meta=[
      ["personal_info", "name"],
      "seniority",
      ["education"],
      ["technical_skills"],
      ["projects"],
      ["leadership_awards"]
    ],
    errors="ignore"
)

# Combine both into one DataFrame
df = pd.concat([exp_df, int_df], ignore_index=True)
df.to_csv("resumes.csv", index=False)


print("Saved resumes.json and resumes.csv")

