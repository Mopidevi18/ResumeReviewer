# backend/utils/parse_resume.py

import fitz    # PyMuPDF
import re
from typing import List, Tuple
from backend.utils.skill_extraction import KNOWN_TECH

def extract_lines(path: str) -> List[str]:
    """
    Pulls out every non-empty line of text from the PDF, in order.
    """
    doc = fitz.open(path)
    lines: List[str] = []
    for page in doc:
        js = page.get_text("dict")
        for block in js["blocks"]:
            for line in block["lines"]:
                t = "".join(span["text"] for span in line["spans"]).strip()
                if t:
                    lines.append(t)
    return lines

# backend/utils/parse_resume.py

def extract_resume_technologies(path: str) -> List[str]:
    """
    Returns only those tokens under the 'Technical Skills' section
    that match your KNOWN_TECH whitelist.
    """
    lines = extract_lines(path)
    techs = []
    in_skills = False

    # bullet-line detector
    bullet_re = re.compile(r'^\s*(?:[•\-\*]|\d+\.)\s+')

    for ln in lines:
        txt = ln.strip()

        # 1) enter skills section
        if re.match(r'^(technical\s+skills|skills\s*/\s*technologies)\b', txt, re.IGNORECASE):
            in_skills = True
            continue

        # 2) leave on blank or all-caps new heading
        if in_skills and (not txt or txt.isupper()):
            break

        if in_skills:
            # skip any bullet lines
            if bullet_re.match(txt):
                continue

            # split out candidates
            for part in re.split(r'[,\|/]', txt):
                p = part.strip()
                key = p.lower()
                # only keep if in your curated list
                
                if key in KNOWN_TECH:
                    techs.append(key)

    # dedupe and preserve order
    seen = set()
    result = []
    for t in techs:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result

def parse_bullets_with_subsections(path: str) -> List[Tuple[str, str, str]]:
    """
    Returns (section, subsection, bullet) for each bullet.
    A line is flagged as a subsection if it’s in an allowed section,
    doesn’t start a bullet, but the very next line DOES start a bullet.
    """
    lines = extract_lines(path)
    ALLOWED = {"Experience", "Internships", "Projects"}
    SKIP    = {"Certifications", "Education", "Technical Skills",
               "Skills / Technologies", "Awards & Recognition"}

    bullet_re = re.compile(r'^\s*(?:[•\-\*]|\d+\.)\s+(.*)$')
    section    = None
    subsection = None
    out: List[Tuple[str,str,str]] = []

    for i, ln in enumerate(lines):
        text = ln.strip()

        # skip any stray tech‐stack labels
        if text.lower().startswith("tech stack"):
            continue

        # detect section headers
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

        # continuation of current bullet?
        if out and (ln.startswith((" ", "\t")) or text[:1].islower()):
            sec, sub, prev = out[-1]
            out[-1] = (sec, sub, prev + " " + text)
            continue

        # otherwise maybe a new subsection title if next line is a bullet
        if i+1 < len(lines) and bullet_re.match(lines[i+1]):
            clean = text.split("|", 1)[0].strip()
            parts = clean.split()
            # drop stray single-letter tokens like "W"
            if len(parts) > 1 and len(parts[-1]) == 1:
                parts = parts[:-1]
            subsection = " ".join(parts)
            continue

        # else: skip

    return out
