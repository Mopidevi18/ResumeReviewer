import os
from openai import OpenAI
from typing import List
from dotenv import load_dotenv
import re

load_dotenv()

class Rewriter:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY in environment")
        self.client = OpenAI(api_key=api_key)

    def rewrite(self, original: str, examples: List[str], job_description: str) -> str:
        # 1. Build messages
        system_msg = (
            "You are an expert resume coach. "
            "You rewrite bullet points to be concise, impactful, and metrics-driven."
        )
        user_content = f"""
Original bullet: "{original}"

Job description: "{job_description}"

Examples from top resumes:
"""
        for ex in examples:
            user_content += f"- {ex}\n"
        user_content += """
Rewrite the original bullet into a single concise, metrics-driven sentence.
"""

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_content},
        ]

        # 2. Call the API
        resp = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=100
        )

        # 3. Return the rewritten bullet
        raw = resp.choices[0].message.content.strip()
        # Strip any leading bullets, dashes or numbers if the model still added one
        cleaned = re.sub(r'^[\-\•\d\.\s]+', '', raw)
        return cleaned
