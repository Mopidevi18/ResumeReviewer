# test_rewrite.py
import os
from backend.rag.retriever import Retriever
from backend.rag.rewrite   import Rewriter

print("Loading components...")
# 1) Load your components
retriever = Retriever(index_path="data/faiss_index")
rewriter  = Rewriter()

# 2) Define a sample bullet and JD
sample_bullet = "Worked on Python scripts to process data"
job_description = (
    "Looking for a Software Engineer with experience "
    "building data pipelines in Python, AWS, and automation"
)

# 3) Retrieve examples
examples = retriever.get_similar(sample_bullet, k=3)
print("Retrieved examples:")
for ex in examples:
    print(" •", ex)

# 4) Rewrite
new_bullet = rewriter.rewrite(
    original=sample_bullet,
    examples=examples,
    job_description=job_description
)
print("\nRewritten bullet:")
print(" >", new_bullet)
