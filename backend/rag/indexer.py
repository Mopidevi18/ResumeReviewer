# backend/rag/indexer.py
import os
import json
from dotenv import load_dotenv

# load .env into os.environ
load_dotenv()

from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS

def build_index(corpus_path: str, index_path: str):
    # grab the key from environment
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError("Missing OPENAI_API_KEY in environment")

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large",
        openai_api_key=openai_key
    )

    with open(corpus_path) as f:
        data = json.load(f)  # expects [{"text": "..."}, ...]
    texts = [item['text'] for item in data]

    db = FAISS.from_texts(texts, embeddings)
    db.save_local(index_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build FAISS index from JSON corpus")
    parser.add_argument("--corpus_path", required=True, help="Path to corpus.json")
    parser.add_argument("--index_path", required=True, help="Directory to save FAISS index")
    args = parser.parse_args()

    build_index(args.corpus_path, args.index_path)
