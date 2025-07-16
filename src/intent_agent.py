# src/intent_agent.py
#!/usr/bin/env python3
# Requirements:
#   pip install openai langchain-openai

import os
import argparse
import json
from enum import Enum
from typing import Dict, Any

from extract_entities_agent import extract_entities
# from table_agent import select_tables_columns   # Pipeline option, currently disabled

SCHEMA_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'docs', 'schema.txt')
)

class Intent(Enum):
    LIST        = "list"
    AGGREGATE   = "aggregate"
    TIME_SERIES = "timeseries"

def normalize(text: str) -> str:
    return text.lower().strip()

def classify_intent(text: str) -> Intent:
    if any(w in text for w in ["sum","average","total","top","max","min"]):
        return Intent.AGGREGATE
    if any(w in text for w in ["trend","over time","per month","per year"]):
        return Intent.TIME_SERIES
    return Intent.LIST

def load_schema_summary() -> str:
    try:
        return open(SCHEMA_PATH).read()
    except:
        return ""

def intent_agent(question: str) -> Dict[str, Any]:
    """
    All queries use the Extract‑Entities Agent.
    (Table Agent is available as a pipeline option but currently disabled.)
    """
    norm    = normalize(question)
    intent  = classify_intent(norm)
    schema  = load_schema_summary()

    entities = extract_entities(norm, intent.value, schema)

    return {
        "original":   question,
        "normalized": norm,
        "intent":     intent.value,
        "entities":   entities
    }

def main():
    parser = argparse.ArgumentParser("NL→SQL Intent Agent")
    parser.add_argument('question', nargs='+', help='Natural language question')
    args = parser.parse_args()
    q = ' '.join(args.question)
    output = intent_agent(q)
    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()
