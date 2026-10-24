#!/usr/bin/env python3
"""Regenerate methodology build-time metadata (test counts, file stats)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "backend" / "app" / "data"


def count_tests() -> dict:
    n = 0
    files = 0
    for root in (ROOT / "tests", ROOT / "backend" / "tests"):
        if not root.exists():
            continue
        for p in root.rglob("test_*.py"):
            files += 1
            text = p.read_text(encoding="utf-8", errors="ignore")
            n += len(re.findall(r"^def test_", text, re.M))
            n += len(re.findall(r"^async def test_", text, re.M))
    return {
        "backend_test_function_count": n,
        "backend_test_file_count": files,
        "generated_note": (
            "Counted from tests/ and backend/tests/. "
            "Regenerate: python backend/scripts/generate_methodology_meta.py"
        ),
    }


def catalogue_file_stats() -> dict:
    out: dict = {
        "source_csv_rows": None,
        "cleaned_parquet_rows": None,
        "ddinter_pairs_loaded": None,
    }
    csv = ROOT / "data" / "Extensive_A_Z_medicines_dataset_of_India.csv"
    if csv.exists():
        with csv.open("rb") as f:
            lines = sum(1 for _ in f)
        out["source_csv_rows"] = max(0, lines - 1)
    pq = ROOT / "data" / "brands_clean.parquet"
    if pq.exists():
        try:
            import pandas as pd

            out["cleaned_parquet_rows"] = int(len(pd.read_parquet(pq)))
        except Exception:
            out["cleaned_parquet_rows"] = None
    dd = ROOT / "data" / "rules" / "ddinter_pairs.parquet"
    if dd.exists():
        try:
            import pandas as pd

            out["ddinter_pairs_loaded"] = int(len(pd.read_parquet(dd)))
        except Exception:
            out["ddinter_pairs_loaded"] = None
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "methodology_build_meta.json").write_text(
        json.dumps(count_tests(), indent=2) + "\n", encoding="utf-8"
    )
    (OUT_DIR / "catalogue_file_stats.json").write_text(
        json.dumps(catalogue_file_stats(), indent=2) + "\n", encoding="utf-8"
    )
    print("Wrote", OUT_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
