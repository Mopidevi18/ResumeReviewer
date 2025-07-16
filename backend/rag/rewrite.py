# backend/rag/rewrite.py

import os
from openai import OpenAI
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Rewriter:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY in environment")
        self.client = OpenAI(api_key=api_key)

    def rewrite(
        self,
        original: str,
        examples: List[str],
        job_description: str,
        do_rewrite: bool,
        issues: List[str] = None
    ) -> str:
        if not do_rewrite:
            return original

        # build an extra instruction if we have specific issues
        issue_instr = ""
        if issues:
            # map our internal issue keys to friendly text
            friendly = {
                "missing a clear action verb": "start with a strong action verb",
                "no quantifiable metric":       "include a quantifiable metric",
                "no relevant technology mentioned": "call out a relevant technology"
            }
            fixes = [ friendly.get(i, i) for i in issues ]
            issue_instr = (
                " Please also address these issues: " +
                ", ".join(fixes) + "."
            )

        system_msg = (
            "You are an expert resume coach. ONLY rewrite using the "
            "original bullet and the retrieved examples. Do NOT invent "
            "any new responsibilities, technologies, or metrics."
            f"{issue_instr}"
        )
        user_content = f"""Job description: "{job_description}"

        Original bullet:
        "{original}"

        Retrieved examples:
        """
        for ex in examples:
            user_content += f"- {ex}\n"

        user_content += """
         Rewrite the original bullet to be concise, metrics-driven, and aligned
         with the job description. If you would change fewer than two words,
         just return the original bullet verbatim.
         """

        resp = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": user_content},
            ],
            temperature=0.0,
            max_tokens=100,
        )
        return resp.choices[0].message.content.strip()

    def suggest_metric(self, original: str, job_description: str) -> str:
        system_msg = (
            "You are a resume coach. Given the bullet point and the job description, "
            "suggest exactly one realistic, concise metric phrase "
            "(e.g. 'increased page load speed by 25%') that fits this responsibility. "
            "Do NOT rewrite any other part."
        )
        user_msg = (
            f"Job description:\n{job_description}\n\n"
            f"Bullet:\n\"{original}\"\n\nMetric:"
        )
        resp = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.0,
            max_tokens=20,
        )
        return resp.choices[0].message.content.strip().strip('"')
