"""Clean the Indian brand medicines CSV into a parquet for the rules engine."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = ROOT / "data" / "Extensive_A_Z_medicines_dataset_of_India.csv"
OUT_PARQUET = ROOT / "data" / "brands_clean.parquet"

KEEP_COLS = [
    "id",
    "name",
    "price(₹)",
    "Is_discontinued",
    "manufacturer_name",
    "pack_size_label",
    "short_composition1",
    "short_composition2",
    "Therapeutic Class",
    "use0",
]

# Order matters: more specific keywords before overlapping ones.
FORM_KEYWORDS = [
    ("suspension", "suspension"),
    ("injection", "injection"),
    ("capsule", "capsule"),
    ("tablet", "tablet"),
    ("syrup", "syrup"),
    ("drops", "drops"),
    ("cream", "cream"),
]

_WHITESPACE_RE = re.compile(r"\s+")


def collapse_whitespace(value: object) -> object:
    """Strip and collapse repeated whitespace; leave nulls as null."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return pd.NA
    if not isinstance(value, str):
        if pd.isna(value):
            return pd.NA
        value = str(value)
    cleaned = _WHITESPACE_RE.sub(" ", value).strip()
    return cleaned if cleaned else pd.NA


def detect_form(pack_size_label: object, name: object) -> str:
    """Derive dosage form from pack_size_label first, then name."""
    for source in (pack_size_label, name):
        if source is None or (isinstance(source, float) and pd.isna(source)):
            continue
        text = str(source).lower()
        for keyword, form in FORM_KEYWORDS:
            if keyword in text:
                return form
    return "other"


def clean_brands(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Apply cleaning rules. Returns cleaned frame and removal/stats summary."""
    stats: dict = {"rows_before": len(df)}

    missing = [c for c in KEEP_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    out = df[KEEP_COLS].copy()
    stats["rows_after_column_select"] = len(out)

    before = len(out)
    out = out.drop_duplicates(subset=["id"], keep="first")
    stats["removed_duplicate_id"] = before - len(out)

    before = len(out)
    # Prefer non-discontinued when (name, composition) collide.
    out = out.sort_values(
        by=["Is_discontinued", "id"],
        ascending=[True, True],
        kind="mergesort",
    )
    out = out.drop_duplicates(
        subset=["name", "short_composition1", "short_composition2"],
        keep="first",
    )
    stats["removed_duplicate_name_composition"] = before - len(out)

    for col in ("name", "short_composition1", "short_composition2"):
        out[col] = out[col].map(collapse_whitespace)

    out["name_norm"] = out["name"].str.lower()

    out["form"] = [
        detect_form(pack, name)
        for pack, name in zip(out["pack_size_label"], out["name"], strict=True)
    ]

    out = out.rename(
        columns={
            "price(₹)": "price",
            "Is_discontinued": "is_discontinued",
            "Therapeutic Class": "therapeutic_class",
        }
    )

    # Stable column order
    out = out[
        [
            "id",
            "name",
            "name_norm",
            "price",
            "is_discontinued",
            "manufacturer_name",
            "pack_size_label",
            "form",
            "short_composition1",
            "short_composition2",
            "therapeutic_class",
            "use0",
        ]
    ].reset_index(drop=True)

    stats["rows_after"] = len(out)
    stats["form_counts"] = out["form"].value_counts().to_dict()
    stats["null_short_composition2"] = int(out["short_composition2"].isna().sum())
    return out, stats


def print_summary(cleaned: pd.DataFrame, stats: dict) -> None:
    print("=" * 60)
    print("CLEANING SUMMARY")
    print("=" * 60)
    print(f"rows before: {stats['rows_before']}")
    print(f"rows after:  {stats['rows_after']}")
    print(f"removed by duplicate id: {stats['removed_duplicate_id']}")
    print(
        "removed by duplicate (name, short_composition1, short_composition2): "
        f"{stats['removed_duplicate_name_composition']}"
    )
    print(f"rows with null short_composition2: {stats['null_short_composition2']}")
    print("\ncount per form:")
    for form, count in sorted(stats["form_counts"].items(), key=lambda x: (-x[1], x[0])):
        print(f"  {form}: {count}")

    multi_mask = cleaned["name"].str.contains(
        r"plus|forte|cold", case=False, na=False, regex=True
    )
    sample = cleaned.loc[multi_mask].head(15)
    print("\n" + "=" * 60)
    print("15 SAMPLE ROWS WITH plus / forte / cold IN NAME")
    print("=" * 60)
    cols = [
        "id",
        "name",
        "form",
        "short_composition1",
        "short_composition2",
        "is_discontinued",
    ]
    print(sample[cols].to_string(index=False))


def main() -> None:
    raw = pd.read_csv(RAW_CSV)
    cleaned, stats = clean_brands(raw)
    cleaned.to_parquet(OUT_PARQUET, index=False)
    print_summary(cleaned, stats)
    print(f"\nSaved: {OUT_PARQUET}")


if __name__ == "__main__":
    main()
