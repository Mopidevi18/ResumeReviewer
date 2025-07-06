# generate_corpus.py
import json

INPUT = "resumes.json"
OUTPUT = "data/corpus.json"

def extract_bullets(resume):
    bullets = []
    # internships
    for intern in resume.get("internships", []):
        bullets += intern.get("bullets", [])
    # full-time experience
    for exp in resume.get("experience", []):
        bullets += exp.get("bullets", [])
    # projects
    for proj in resume.get("projects", []):
        bullets += proj.get("bullets", [])
    return bullets

def build_corpus():
    with open(INPUT, "r") as f:
        resumes = json.load(f)

    all_bullets = []
    for r in resumes:
        for b in extract_bullets(r):
            text = b.strip()
            if len(text.split()) >= 5:      # filter out fluff
                all_bullets.append({"text": text})

    # dedupe
    unique = {item["text"]: item for item in all_bullets}
    corpus = list(unique.values())

    with open(OUTPUT, "w") as f:
        json.dump(corpus, f, indent=2)
    print(f"Wrote {len(corpus)} bullets to {OUTPUT}")

if __name__ == "__main__":
    build_corpus()
