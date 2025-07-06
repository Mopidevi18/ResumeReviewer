# backend/rag/retriever.py

import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

class Retriever:
    def __init__(self, index_path: str):
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("Missing OPENAI_API_KEY in environment")

        # initialize the embedder
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=openai_key
        )

        # load your FAISS index (trusted, local file)
        self.db = FAISS.load_local(
            index_path,
            self.embeddings,
            allow_dangerous_deserialization=True
        )


    def get_similar(
        self,
        text: str,
        k: int = 3,
        tech_filter: list[str] | None = None
    ) -> list[str]:
        # 1) Always grab a few more than k
        fetch_n = k * 5 if tech_filter else k
        docs = self.db.similarity_search(query=text, k=fetch_n)

        # 2) If no filter, just return top k
        if not tech_filter:
            return [d.page_content for d in docs[:k]]

        # 3) Otherwise filter in Python by metadata
        filtered = []
        for d in docs:
            tags = d.metadata.get("tech", [])
            if set(tech_filter).issubset(set(tags)):
                filtered.append(d)
            if len(filtered) >= k:
                break

        # 4) Fallback: if you didn’t get enough, pad with unfiltered
        if len(filtered) < k:
            filtered += docs[: (k - len(filtered))]

        return [d.page_content for d in filtered]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Smoke-test Retriever against your FAISS index"
    )
    parser.add_argument(
        "--index_path", type=str, default="data/faiss_index",
        help="Directory where your FAISS index is stored"
    )
    parser.add_argument(
        "--query", type=str, required=True,
        help="A sample bullet point to test retrieval with"
    )
    parser.add_argument(
        "--k", type=int, default=3,
        help="How many neighbors to return"
    )
    args = parser.parse_args()

    retriever = Retriever(args.index_path)

    # Example: Automatically derive tech_filter from your JD parsing logic,
    # but for smoke‐testing you can pass a literal list here:
    tech_filter = None  
    # tech_filter = ["python","rest"]

    results = retriever.get_similar(
        text=args.query,
        k=args.k,
        tech_filter=tech_filter
    )

    print(f"\nTop {args.k} matches for query:\n  “{args.query}”\n")
    for i, text in enumerate(results, 1):
        print(f"{i}. {text}\n")
