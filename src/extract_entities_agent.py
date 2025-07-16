#!/usr/bin/env python3
# Requirements:
# pip install openai>=1.0.0
import json
import re
import openai

# ── Hardcoded OpenAI API key ─────────────────────────────────────────────────
OPENAI_API_KEY = ""

# Initialize the OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ── Dataset definitions for grounding ────────────────────────────────────────
DATASET_DEFINITIONS = """
ICD-10: International Classification of Diseases (diagnostic codes)
CPT: Current Procedural Terminology (procedure/service codes)
HCP: Healthcare Professional
HCO: Healthcare Organization
Claim: billed interaction record
Patient: individual receiving treatment
Procedure: medical operation/service
Drug: pharmaceutical product
Therapy Area: medical specialty
KOL: Key Opinion Leader
Trial: clinical study
"""

def extract_entities(question: str, intent: str, schema_summary: str) -> dict:
    """
    Uses one GPT-4o-mini call to extract:
    - tables: list of table names
    - columns: list of columns
    - filters: {col: {op, value}}
    - order_by: [{column, dir}]
    - limit: int
    """
    prompt = f"""
You are an assistant that extracts structured query components.
Definitions:
{DATASET_DEFINITIONS}
Schema:
{schema_summary}
Intent: {intent}
Question: {question}
Extract JSON with keys: tables, columns, filters, order_by, limit.
"""
    
    # NEW v1.0+ interface:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Extract tables, columns, filters, order_by, limit."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    
    # Fix: Use attribute access instead of dictionary subscripting
    text = response.choices[0].message.content.strip()
    
    # strip ```json``` fences
    m = re.match(r"^```(?:json)?([\s\S]*?)```$", text)
    if m:
        text = m.group(1)
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise ValueError(f"Could not parse JSON: {text}")

# Interactive test
if __name__ == "__main__":
    import os, argparse
    SCHEMA_PATH = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', 'docs', 'schema.txt')
    )
    schema = ""
    try:
        schema = open(SCHEMA_PATH).read()
    except:
        pass
    
    question = input("Enter your SQL-like question: ")
    result = extract_entities(question, intent="unknown", schema_summary=schema)
    print(json.dumps(result, indent=2))
