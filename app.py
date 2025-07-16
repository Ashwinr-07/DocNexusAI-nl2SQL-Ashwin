import os
import logging

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

# Force Python to load modules from src/
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from query_rag import generate_sql
from pipeline_agent import rows_to_csv, generate_insights

# ─── Configure Flask ─────────────────────────────────────────────────────
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
CORS(app)

# ─── Database settings ────────────────────────────────────────────────────
PGHOST     = os.getenv("PGHOST", "127.0.0.1")
PGPORT     = int(os.getenv("PGPORT", "5433"))
PGUSER     = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "aryan2008")
DB_NAME    = os.getenv("DB_NAME", "health_data_db")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate_sql', methods=['POST'])
def generate_sql_endpoint():
    data = request.get_json()
    nlp_query = data.get('query', '').strip()
    if not nlp_query:
        return jsonify(error='No query provided', sql=''), 400

    app.logger.info(f"[generate_sql] NL query: {nlp_query}")
    try:
        # 1) Generate the raw SQL
        sql = generate_sql(nlp_query, debug=False)
        # 2) Strip any trailing backticks or fences
        import re
        sql = re.sub(r'```+$', '', sql).strip()
        return jsonify(sql=sql, query=nlp_query)
    except Exception as e:
        app.logger.error(f"[generate_sql] Failed: {e}", exc_info=True)
        return jsonify(error=str(e), sql=''), 500



@app.route('/execute_sql', methods=['POST'])
def execute_sql_endpoint():
    data = request.get_json()
    sql_query = data.get('sql', '').strip()
    if not sql_query:
        return jsonify(error='No SQL provided', results={}), 400
    if not sql_query.lower().startswith('select'):
        return jsonify(error='Only SELECT allowed', results={}), 400

    app.logger.info(f"[execute_sql] SQL: {sql_query}")
    try:
        conn = psycopg2.connect(
            host=PGHOST, port=PGPORT,
            user=PGUSER, password=PGPASSWORD,
            dbname=DB_NAME
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(sql_query)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        columns = list(rows[0].keys()) if rows else []
        data = [list(r.values()) for r in rows]
        return jsonify(results={'columns': columns, 'data': data},
                       row_count=len(data))
    except Exception as e:
        app.logger.error(f"[execute_sql] Failed: {e}", exc_info=True)
        return jsonify(error=str(e), results={}), 500


@app.route('/generate_insights', methods=['POST'])
def generate_insights_endpoint():
    data = request.get_json()
    sql_query = data.get('sql', '').strip()
    nlp_query = data.get('query', '').strip()
    if not sql_query or not nlp_query:
        return jsonify(error='SQL and original query required', insights=[]), 400

    app.logger.info(f"[generate_insights] SQL: {sql_query[:80]}...")
    try:
        # (Re‑)execute to get rows
        conn = psycopg2.connect(
            host=PGHOST, port=PGPORT,
            user=PGUSER, password=PGPASSWORD,
            dbname=DB_NAME
        )
        cur = conn.cursor()
        cur.execute(sql_query)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        cur.close()
        conn.close()

        # Get raw LLM string
        raw = generate_insights(nlp_query, cols, rows)  # returns a string of bullet points

        # Split into lines, extract bullets (lines starting with "-" or "•")
        lines = [line.strip() for line in raw.splitlines() if line.strip().startswith(("-", "•"))]
        if not lines:
            # fallback: wrap the entire text
            insights = [{"title": "", "value": "", "description": raw, "icon": "fas fa-lightbulb"}]
        else:
            insights = []
            for ln in lines:
                text = ln.lstrip("•- ").strip()
                insights.append({
                    "title": "", 
                    "value": "", 
                    "description": text, 
                    "icon": "fas fa-lightbulb"
                })

        return jsonify(insights=insights)

    except Exception as e:
        app.logger.error(f"[generate_insights] Failed: {e}", exc_info=True)
        return jsonify(error=str(e), insights=[]), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
