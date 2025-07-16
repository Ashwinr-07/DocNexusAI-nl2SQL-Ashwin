# Healthcare Data NLP → SQL Pipeline

This project provides a full end‑to‑end system for translating natural‑language healthcare queries into SQL, executing them against a Postgres database, and optionally generating AI‑driven insights. It combines several modular “agents” with retrieval‑augmented prompting (RAG) and multiple OpenAI models:

- **Intent Agent** (`src/intent_agent.py`) and **Extract‑Entities Agent** (`src/extract_entities_agent.py`) run on **gpt-4o-mini** for fast intent and entity extraction.
- **SQL Generation** (`src/query_rag.py`) uses RAG over a FAISS index of few‑shot examples, then calls:
  - **gpt-4o** for simple or large‑table queries,
  - **o4-mini** (the reasoning model) for medium‑complexity (2–3 tables).
- **Insights Agent** (`src/pipeline_agent.py`) executes the SQL and, when requested, calls **gpt-4o-mini** to produce concise data insights.

---

## Table of Contents

1. [Prerequisites](#prerequisites)  
2. [Installation](#installation)  
3. [Database Setup](#database-setup)  
4. [Build RAG Index](#build-rag-index)  
5. [Configuration](#configuration)  
6. [Project Structure](#project-structure)  
7. [Running the Application](#running-the-application)  
8. [API Endpoints](#api-endpoints)  
9. [Model Usage](#model-usage)  
10. [Front-end Integration](#front-end-integration)  
11. [Troubleshooting](#troubleshooting)  

---

## Prerequisites

- Python 3.9+  
- PostgreSQL 12+  
- Bash shell (for provided scripts)  
- OpenAI API key with access to gpt-4o, o4-mini, and gpt-4o-mini  

---

## Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/your-org/DocNexusAI-nl2SQL.git
   cd DocNexusAI-nl2SQL
   ```

2. **Create and activate a virtual environment**  
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Python dependencies**  
   ```bash
   pip install -r requirements.txt
   ```
   *Key packages include:*  
   - `flask`, `flask-cors`  
   - `psycopg2-binary`  
   - `openai`  
   - `langchain`, `langchain-community`  
   - `faiss-cpu` (or `faiss-gpu`)  
   - `tabulate`  

---

## Database Setup

Load your CSV/TSV data into Postgres using the provided script:

```bash
bash load_csv.sh
```

This will:

1. Drop and recreate the `health_data_db` database.  
2. Create all required tables.  
3. Import TSV files from `data/` into Postgres.

---

## Build RAG Index

Generate a FAISS index of your few‑shot YAML examples for Retrieval‑Augmented Generation:

```bash
python src/build_rag_index.py
```

This reads `docs/examples/validated/ex*.yaml`, embeds them with **OpenAIEmbeddings**, and saves the index under `vector_store/`.

---

## Configuration

Set your OpenAI key and any custom DB credentials as environment variables, or edit the top of `app.py` and agent files:

```bash
export OPENAI_API_KEY="sk-..."
export PGHOST="127.0.0.1"
export PGPORT="5433"
export PGUSER="postgres"
export PGPASSWORD="yourpassword"
export DB_NAME="health_data_db"
```

---

## Project Structure

```
├── app.py                      # Flask server, API endpoints
├── main.py                     # Entrypoint (runs app.py)
├── static/                     # Front-end JS/CSS
│   ├── script.js
│   └── style.css
├── templates/                  # HTML templates
│   └── index.html
├── src/                        # Core agents & pipeline code
│   ├── intent_agent.py         # Intent detection (gpt-4o-mini)
│   ├── extract_entities_agent.py  # Entity extraction (gpt-4o-mini)
│   ├── build_rag_index.py      # FAISS index builder
│   ├── query_rag.py            # NL→SQL pipeline (gpt-4o/o4-mini)
│   ├── pipeline_agent.py       # SQL execution + insights (gpt-4o-mini)
│   ├── run_query.sh            # CLI helper to run a single query
│   └── … (other utilities)
├── data/                       # Raw CSVs
├── docs/                       # Schema dumps, glossaries, examples
│   ├── schema.txt
│   └── examples/validated/*.yaml
├── vector_store/               # FAISS index output
├── load_csv.sh                 # Script to create DB and import data
└── requirements.txt            # Python dependencies
```

Architecture Diagram

<img width="951" height="830" alt="image" src="https://github.com/user-attachments/assets/227c59cb-6390-4015-8af6-2892ecaf5e1b" />


---

## Running the Application

1. **Start the Flask server on port 5001**  
   ```bash
   python app.py
   ```
   By default, it listens on `0.0.0.0:5001`.

2. **Open the UI**  
   Navigate to `http://localhost:5001` in your browser.

3. **Enter a natural-language query**, click **Generate SQL**, then **Execute**, and optionally **Generate Insights**.

---

## API Endpoints

- **POST /generate_sql**  
  Request: `{ "query": "..." }`  
  Response: `{ "sql": "...", "query": "..." }`

- **POST /execute_sql**  
  Request: `{ "sql": "..." }`  
  Response:  
  ```json
  {
    "results": {
      "columns": [...],
      "data": [[...], ...]
    },
    "row_count": N
  }
  ```

- **POST /generate_insights**  
  Request: `{ "sql":"...","query":"..." }`  
  Response:  
  ```json
  {
    "insights": [
      {"title":"","value":"","description":"...", "icon":"fas fa-lightbulb"},
      ...
    ]
  }
  ```

---

## Model Usage

| Agent / Step             | Model           | Purpose                                          |
|--------------------------|-----------------|--------------------------------------------------|
| Intent Extraction        | **gpt-4o-mini** | Fast intent classification & normalization       |
| Entity Extraction        | **gpt-4o-mini** | Structured extraction of tables/columns/filters  |
| SQL Generation (simple)  | **gpt-4o**      | Single-table or large-table SQL generation       |
| SQL Generation (reasoning)| **o4-mini**    | Multi-table (2–3) queries requiring deeper logic |
| Data Insights            | **gpt-4o-mini** | Concise bullet-point analysis of query results   |

---

## Front-end Integration

- The **HTML/CSS/JS** in `templates/` and `static/` implements a step-by-step UI:
  1. **Generate SQL** → calls `/generate_sql`.  
  2. **Execute Query** → calls `/execute_sql`.  
  3. **Generate Insights** → calls `/generate_insights`.  

- The server must run on **port 5001** to match the front-end configuration.

---

## Troubleshooting

- **No SQL appears when clicking “Generate SQL”**  
  - Ensure your Flask app is running on `localhost:5001`.  
  - Check DevTools → Console & Network tabs for errors.

- **Deprecation warnings from LangChain**  
  - Suppress them with:
    ```python
    import warnings
    from langchain import LangChainDeprecationWarning
    warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)
    ```
  - Or update imports to `langchain_community`.

---


