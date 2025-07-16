# src/build_rag_index.py
#!/usr/bin/env python3
"""
Builds a FAISS vector store from your YAML examples for RAG.
"""
import os
import glob
import yaml

from langchain.schema import Document
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS

# ── Config ────────────────────────────────────────────────────────
API_KEY    = ""
INDEX_PATH = os.path.join(os.path.dirname(__file__), '..', 'vector_store')
DOCS_GLOB  = os.path.join(os.path.dirname(__file__), '..', 'docs', 'examples', 'validated', 'ex*.yaml')
# ─────────────────────────────────────────────────────────────────

def build_vector_store(docs_glob: str = DOCS_GLOB, store_path: str = INDEX_PATH):
    docs = []
    for fn in glob.glob(docs_glob):
        with open(fn) as f:
            ex = yaml.safe_load(f)
        docs.append(
            Document(
                page_content=f"Q: {ex['question']}\nSQL: {ex['sql']}",
                metadata={"tables": ex.get("tables", [])},
                id=str(ex["id"])
            )
        )

    embeddings = OpenAIEmbeddings(openai_api_key=API_KEY)
    vs = FAISS.from_documents(docs, embeddings)
    os.makedirs(store_path, exist_ok=True)
    vs.save_local(store_path)
    print(f"✅ Vector store built at {store_path}")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser("Build RAG FAISS index")
    p.add_argument(
        "--docs",
        default=DOCS_GLOB,
        help="Path glob to your example YAML files"
    )
    p.add_argument(
        "--out",
        default=INDEX_PATH,
        help="Directory to save FAISS index"
    )
    args = p.parse_args()
    build_vector_store(docs_glob=args.docs, store_path=args.out)
