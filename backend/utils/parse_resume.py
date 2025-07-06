import fitz    # PyMuPDF
import re
from typing import List, Tuple

def extract_lines(path: str) -> List[str]:
    doc = fitz.open(path)
    lines = []
    for page in doc:
        js = page.get_text("dict")
        for block in js["blocks"]:
            for line in block["lines"]:
                t = "".join(span["text"] for span in line["spans"]).strip()
                if t:
                    lines.append(t)
    return lines

def parse_bullets_with_subsections(path: str) -> List[Tuple[str, str, str]]:
    """
    Returns (section, subsection, bullet) for each bullet.
    A line is a subsection if it’s in an allowed section,
    doesn’t start a bullet, and the very next line DOES start a bullet.
    """
    lines = extract_lines(path)
    ALLOWED = {"Experience", "Internships", "Projects"}
    SKIP    = {
        "Certifications",
            "Education",
            "Technical Skills",
            "Skills / Technologies",
        "Awards & Recognition",     
        }
    bullet_re = re.compile(r'^\s*(?:[•\-\*]|\d+\.)\s+(.*)$')

    section    = None
    subsection = None
    out: List[Tuple[str,str,str]] = []

    for i, ln in enumerate(lines):
        text = ln.strip()

        # skip tech stack lines
        if text.lower().startswith("tech stack"):
            continue

        # section headers
        if text in ALLOWED:
            section    = text
            subsection = None
            continue
        if text in SKIP:
            section    = None
            subsection = None
            continue

        # ignore everything outside allowed sections
        if section is None:
            continue

        # bullet?
        m = bullet_re.match(text)
        if m:
            out.append((section, subsection or "General", m.group(1).strip()))
            continue

        # continuation?
        if out and (ln.startswith((" ", "\t")) or text[:1].islower()):
            sec, sub, prev = out[-1]
            out[-1] = (sec, sub, prev + " " + text)
            continue

        # otherwise: check if next line is a bullet → treat this as a new subsection
        if i+1 < len(lines) and bullet_re.match(lines[i+1]):
            # 1) take everything before the "|" (project name)
            clean = text.split("|", 1)[0].strip()

            # 2) if clean ends in a single-letter token (like stray "W"), drop it
            parts = clean.split()
            if len(parts) > 1 and len(parts[-1]) == 1:
                parts = parts[:-1]
            subsection = " ".join(parts)
            continue

        # else: skip stray lines

    return out
