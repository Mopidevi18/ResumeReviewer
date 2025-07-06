# backend/rag/rewrite.py

import os
from openai import OpenAI
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Rewriter:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY in environment")
        self.client = OpenAI(api_key=api_key)

    def rewrite(self,
                original: str,
                examples: List[str],
                job_description: str,
                do_rewrite: bool
               ) -> str:
        # If the bullet is already strong, just echo it
        if not do_rewrite:
            return original

        # Build a strict prompt
        system_msg = (
            "You are an expert resume coach. ONLY rewrite using the "
            "original bullet and the retrieved examples. Do NOT invent "
            "any new responsibilities, technologies, or metrics."
        )

        user_content = f"""
            Job description: "{job_description}"

            Original bullet:
            "{original}"

            Retrieved examples:
            """
        for ex in examples:
            user_content += f"- {ex}\n"

        user_content += """
            Rewrite the original bullet to be concise, metrics‐driven, and aligned 
            with the job description.  If you would change fewer than two words, 
            just return the original bullet verbatim.
            """

        resp = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": user_content},
            ],
            temperature=0.0,    # minimize creativity
            max_tokens=100
        )
        return resp.choices[0].message.content.strip()
