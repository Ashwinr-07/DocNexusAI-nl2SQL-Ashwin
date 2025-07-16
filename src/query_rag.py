#!/usr/bin/env python3
"""
RAG NL→SQL pipeline with intent→entities→RAG,
and separate debug vs. query modes.
"""
import os
import re
import warnings

from intent_agent import intent_agent
from extract_entities_agent import extract_entities
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.schema import HumanMessage

# Ignore all warnings as requested
warnings.filterwarnings("ignore")

# ── Config ────────────────────────────────────────────────────────
API_KEY      = ""
INDEX_PATH   = os.path.join(os.path.dirname(__file__), '..', 'vector_store')
FULL_SCHEMA  = os.path.join(os.path.dirname(__file__), '..', 'docs', 'schema.txt')
TOP_K        = 3
MODEL_SIMPLE = "gpt-4o"
MODEL_REASON = "o4-mini"
TEMPERATURE  = 0.0
# ────────────────────────────────────────────────────────────────────────

def load_full_schema() -> str:
    try:
        return open(FULL_SCHEMA, 'r').read()
    except FileNotFoundError:
        return ""

def extract_relevant_schema(tables: list[str]) -> str:
    lines = load_full_schema().splitlines()
    out, capture, current = [], False, None
    for line in lines:
        m = re.match(r"^TABLE:\s*(\w+)", line)
        if m:
            current = m.group(1)
            capture = current in tables
        if capture:
            out.append(line)
    return "\n".join(out)

def retrieve_examples(question: str, selected_tables: list[str]) -> str:
    emb = OpenAIEmbeddings(openai_api_key=API_KEY)
    vs  = FAISS.load_local(INDEX_PATH, emb, allow_dangerous_deserialization=True)
    retriever = vs.as_retriever(
        search_kwargs={"k": TOP_K},
        filter=lambda md: bool(set(md["tables"]) & set(selected_tables))
    )
    docs = retriever.get_relevant_documents(question)
    return "\n\n".join(d.page_content for d in docs)

def clean_sql(sql: str) -> str:
    q = sql.strip()
    for p in ["```sql","```","SQL:","Query:","A:","Answer:"]:
        if q.startswith(p):
            q = q[len(p):].strip()
    return " ".join(q.split())

def generate_sql(question: str, debug: bool = False) -> str:
    """
    Runs intent_agent → extract_entities → builds prompt → calls LLM.
    If debug=True, prints the full prompt and model choice first.
    Returns only the cleaned SQL.
    """
    # 1) Extract via intent_agent (which calls extract_entities internally)
    info = intent_agent(question)
    ent  = info["entities"]
    tables   = ent.get("tables", [])
    columns  = ent.get("columns", [])
    filters  = ent.get("filters", {})
    order_by = ent.get("order_by", [])
    limit    = ent.get("limit", None)

    if not tables:
        raise ValueError(f"No tables extracted for: '{question}'")

    # 2) Model selection
    n = len(tables)
    model = MODEL_REASON if 2 <= n <= 3 else MODEL_SIMPLE

    # 3) Build prompt pieces
    schema_snip = extract_relevant_schema(tables)
    examples    = retrieve_examples(question, tables)

    ent_block = (
        f"Extracted entities:\n"
        f"• tables: {tables}\n"
        f"• columns: {columns}\n"
        f"• filters: {filters}\n"
        f"• order_by: {order_by}\n"
        f"• limit: {limit}\n\n"
    )
    null_req = "- For each returned column, add `AND <column> IS NOT NULL` to the WHERE clause.\n\n"

    prompt = (
        f"You are a SQL-generation assistant (using {model}).\n\n"
        f"{ent_block}"
        "Relevant schema definitions:\n" + schema_snip + "\n\n"
        "Examples:\n" + examples + "\n\n"
        "User question: " + question + "\n\n"
        "Requirements:\n" + null_req +
        "Generate only the SQL query:"
    )

    # 4) Debug output
    if debug:
        print("=== Final Prompt Sent to LLM ===\n")
        print(prompt)
        print("\n=== End Prompt ===")
        print(f"\n[Using model: {model}]\n")

    # 5) LLM call
    llm = ChatOpenAI(model_name=model, temperature=TEMPERATURE, openai_api_key=API_KEY)
    resp = llm([HumanMessage(content=prompt)])
    return clean_sql(resp.content)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser("Full NL→SQL Pipeline")
    parser.add_argument("--query", type=str, help="Natural-language question → SQL")
    parser.add_argument("--debug", type=str, help="Show prompt + SQL for question")
    args = parser.parse_args()

    if args.query:
        # Only print the final SQL
        print(generate_sql(args.query, debug=False))
    elif args.debug:
        # Print prompt + model + SQL
        sql = generate_sql(args.debug, debug=True)
        print("\n--- Generated SQL ---\n", sql)
    else:
        parser.print_help()
