#!/usr/bin/env python3
"""
Full NL→SQL→Execution→Insights Pipeline Agent
Usage:
 # Just run the NL→SQL and execute:
 python src/pipeline_agent.py --nl "List top 5 providers by total_claim_charge in 2023"
 # Run and also generate insights:
 python src/pipeline_agent.py \
 --nl "List top 5 providers by total_claim_charge in 2023" \
 --insight
"""
import os
import re
import sys
import csv
import psycopg2
from openai import OpenAI
from tabulate import tabulate
# Import your SQL-generation function
from query_rag import generate_sql

# ── Configuration ───────────────────────────────────────────────────
# Postgres connection
PGHOST = os.getenv("PGHOST", "127.0.0.1")
PGPORT = int(os.getenv("PGPORT", 5433))
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "aryan2008")
DB_NAME = os.getenv("DB_NAME", "health_data_db")

# OpenAI
OPENAI_API_KEY = "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"
client = OpenAI(api_key=OPENAI_API_KEY)

# ── Helpers ─────────────────────────────────────────────────────────
def clean_sql_for_execution(sql: str) -> str:
    """Strip trailing backticks, code fences, ensure ends without semicolon."""
    q = sql.strip()
    # remove markdown fences
    q = re.sub(r"^```(?:sql)?|```$", "", q, flags=re.MULTILINE)
    # if ends with semicolon, keep it for psql or not? psycopg2 accepts semicolon, but safe to strip
    if q.endswith(";"):
        q = q[:-1]
    return q

def execute_sql(sql: str):
    """Run the SQL and return (columns, rows)."""
    conn = psycopg2.connect(
        host=PGHOST, port=PGPORT, user=PGUSER, password=PGPASSWORD, dbname=DB_NAME
    )
    cur = conn.cursor()
    cur.execute(sql)
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return cols, rows

def rows_to_csv(cols, rows) -> str:
    """Convert query results to CSV text (with header)."""
    output = [cols]
    for row in rows:
        output.append([("" if v is None else v) for v in row])
    # write to string
    lines = []
    for r in output:
        lines.append(",".join(map(str, r)))
    return "\n".join(lines)

def generate_insights(nl: str, cols, rows) -> str:
    """
    Call gpt-4o-mini to produce insights:
      - If ≤ 5 rows: send full CSV and ask for 3 bullet‑point insights.
      - If > 5 rows: send only the first row, ask what type of record it is.
    """
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Helper to format a single row as CSV
    def single_row_csv(headers, row):
        return ",".join(headers) + "\n" + ",".join(str(v) for v in row)

    if len(rows) <= 5:
        csv_data = rows_to_csv(cols, rows)
        prompt = f"""
You are a data analyst assistant.
User question:
{nl}

Here are the query results in CSV (header first):
{csv_data}

Please provide exactly 3 concise bullet-point insights based on these results.
"""
    else:
        # Only the first row to ground the insight
        first_csv = single_row_csv(cols, rows[0])
        prompt = f"""
You are a data analyst assistant.
User question:
{nl}

The query returned {len(rows)} rows; here is the first row (header + values) in CSV:
{first_csv}

Please describe in one or two sentences what this row represents and why it might be the top result.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Generate data insights."},
            {"role": "user",   "content": prompt}
        ],
        temperature=0
    )
    return response.choices[0].message.content.strip()


# ── Main ────────────────────────────────────────────────────────────
def main():
    import argparse
    p = argparse.ArgumentParser("Pipeline Agent: NL→SQL→Exec→Insights")
    p.add_argument("--nl", type=str, required=True, help="Natural-language question")
    p.add_argument("--insight", action="store_true", help="Also generate LLM insights")
    args = p.parse_args()
    
    nl = args.nl.strip()
    
    # 1) Generate SQL
    sql = generate_sql(nl, debug=False)
    sql_exec = clean_sql_for_execution(sql)
    
    # 2) Execute and display results
    cols, rows = execute_sql(sql_exec)
    if not rows:
        print("No results returned.")
    else:
        print(tabulate(rows, headers=cols, tablefmt="psql"))
    
    # 3) Optionally generate insights
    if args.insight:
        insights = generate_insights(nl, cols, rows)
        print("\n--- Insights ---")
        print(insights)

if __name__ == "__main__":
    main()