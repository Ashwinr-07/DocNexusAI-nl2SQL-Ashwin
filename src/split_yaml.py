#!/usr/bin/env python3
import yaml
from pathlib import Path

# ─── CONFIG ──────────────────────────────────────────────────────────
SEED_FILE   = Path("docs/examples/nl_sql_seed.yaml")
OUT_DIR     = Path("docs/examples/validated")
# ─────────────────────────────────────────────────────────────────────

def main():
    # load the monolithic seed file
    examples = yaml.safe_load(SEED_FILE.read_text())
    # ensure output directory exists
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for ex in examples:
        ex_id = ex.get("id")
        if not ex_id:
            continue

        out_path = OUT_DIR / f"{ex_id}.yaml"
        # write only this one example (as a single-element list or dict)
        with out_path.open("w") as f:
            yaml.safe_dump(ex, f, sort_keys=False)

        print(f"→ Wrote {out_path}")

if __name__ == "__main__":
    main()
