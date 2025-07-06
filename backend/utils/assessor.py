# backend/utils/assessor.py

import re
from typing import Tuple, List

# a small set of strong action verbs
ACTION_VERBS = {
    "developed","engineered","built","implemented","designed","launched",
    "streamlined","optimized","led","managed","architected","deployed",
    "automated","enhanced","reduced","increased","improved","consolidated"
}

# metrics: % or X min/hr/days/k etc.
# metrics: numeric or frequency words
# metrics: any number or percent OR frequency words
METRIC_RE = re.compile(
    r'''
      \b
      (?: 
        \d{1,3}(?:,\d{3})*(?:\.\d+)?%?    # 1,234 or 2145 or 75% or 3.5
      |
        daily|weekly|monthly|quarterly|yearly
      )
      \b
    ''',
    re.IGNORECASE | re.VERBOSE
)

# If the bullet contains any of these outcome‐verbs, treat it as “quantified”
QUALITATIVE_OUTCOMES = {
   "reduce","reducing","reduced",
    "optimize","optimizing","optimized",
    "improve","improving","improved",
    "save","saving","saved",
    "cut","cutting","cut"
}

def assess_bullet_strength(bullet: str) -> Tuple[bool, List[str]]:
    """
    Returns (is_strong, list_of_issues). 
    A bullet is strong if it:
    1) starts with a known action verb
    2) contains at least one quantifiable metric
    """
    issues: List[str] = []

    # 1) check action verb
    first = bullet.split()[0].lower().rstrip('.,') if bullet.split() else ""
    if not (first in ACTION_VERBS or first.endswith("ed")):
        issues.append("missing a clear action verb")

    # 2) check metrics
    has_numeric = bool(METRIC_RE.search(bullet))
    has_qualitative = any(w in bullet.lower() for w in QUALITATIVE_OUTCOMES)
    if not (has_numeric or has_qualitative):
        issues.append("no quantifiable metric")

    is_strong = len(issues) == 0
    return is_strong, issues
