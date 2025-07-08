# backend/utils/assessor.py

import re
from typing import Tuple, List

ACTION_VERBS = {
    "developed","engineered","built","implemented","designed","launched",
    "streamlined","optimized","led","managed","architected","deployed",
    "automated","enhanced","reduced","increased","improved","consolidated"
}

# Only numbers (with optional commas/decimals) and optional %.
METRIC_RE = re.compile(
    r'''
      \b
      \d{1,3}(?:,\d{3})*(?:\.\d+)?%?
      \b
    ''',
    re.VERBOSE
)

def assess_bullet_strength(bullet: str) -> Tuple[bool, List[str]]:
    """
    Returns (is_strong, list_of_issues).
    A bullet is strong if it:
      1) starts with a known action verb
      2) contains at least one explicit numeric metric (e.g. 75%, 2,145, 3.5)
    """
    issues: List[str] = []

    # 1) Check action verb
    cleaned = re.sub(r'^(Successfully|Quickly|Easily|Effectively)\s+', '',
                     bullet, flags=re.IGNORECASE)
    first = cleaned.split()[0].lower().rstrip('.,') if cleaned.split() else ""
    if not (first in ACTION_VERBS or first.endswith("ed")):
        issues.append("missing a clear action verb")

    # 2) Check for hard metric
    if not METRIC_RE.search(bullet):
        issues.append("no quantifiable metric")

    return (len(issues) == 0), issues
