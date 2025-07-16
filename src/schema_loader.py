# src/schema_loader.py
from pathlib import Path
import pandas as pd
from textwrap import shorten

DATA_DIR = Path(__file__).resolve().parents[1] / "data"   # ../data/

def _canonical(name: str) -> str:
    """
    Turn 'Payments to HCPs.csv'  ➜  payments_to_hcps
    Makes downstream matching easier.
    """
    return (
        name.lower()
        .replace(".csv", "")
        .replace("&", "and")
        .replace(" ", "_")
    )

def load_schema(data_dir: Path | None = None) -> dict[str, list[str]]:
    """
    Read every *.csv in data_dir (first row only) and
    build {table_name: [columns…]}.
    """
    data_dir = data_dir or DATA_DIR
    schema: dict[str, list[str]] = {}

    for csv_path in data_dir.glob("*.csv"):
        table_name = _canonical(csv_path.name)
        # read just the header – very fast even on GB-scale csv
        cols = list(pd.read_csv(csv_path, nrows=0).columns)
        schema[table_name] = cols

    if not schema:
        raise RuntimeError(f"No CSV files found under {data_dir!s}")
    return schema


# ---------- Tiny helper API ---------- #
SCHEMA = load_schema()

def list_tables() -> list[str]:
    return list(SCHEMA.keys())

def list_columns(table: str) -> list[str]:
    return SCHEMA.get(_canonical(table), [])


# ---------- CLI preview ---------- #
if __name__ == "__main__":
    import rich
    from rich.table import Table

    tb = Table(title="Schema overview")
    tb.add_column("Table", style="bold cyan")
    tb.add_column("#cols", justify="right")
    tb.add_column("First few columns")

    for t, cols in SCHEMA.items():
        tb.add_row(
            t,
            str(len(cols)),
            shorten(", ".join(cols), width=70, placeholder=" …"),
        )
    rich.print(tb)
