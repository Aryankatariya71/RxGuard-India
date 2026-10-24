"""Build data/rules/ddinter_pairs.parquet from DDInter CSVs (Major/Moderate/Minor)."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pandas as pd

from src.composition import expand_brand, normalize_ingredient
from src.ingredient_norm import load_salts

ROOT = Path(__file__).resolve().parent.parent
DDINTER_DIR = ROOT / "data" / "ddinter"
PARQUET_BRANDS = ROOT / "data" / "brands_clean.parquet"
OUT_PATH = ROOT / "data" / "rules" / "ddinter_pairs.parquet"

LEVEL_RANK = {"major": 3, "moderate": 2, "minor": 1}
TIER_MAP = {"major": "critical", "moderate": "review", "minor": "info"}

_SPECIAL_RE = re.compile(r"[/+]|\band\b", re.IGNORECASE)


def _norm(name: object) -> str:
    return normalize_ingredient(str(name)) if name is not None else ""


def brand_ingredient_set(parquet_path: Path = PARQUET_BRANDS) -> set[str]:
    df = pd.read_parquet(parquet_path)
    ings: set[str] = set()
    cols = list(df.columns)
    for tup in df.itertuples(index=False, name=None):
        row = dict(zip(cols, tup, strict=True))
        for item in expand_brand(row):
            name = item.get("ingredient")
            if name:
                ings.add(str(name))
    return ings


def review_complex_names(raw_names: list[str], limit: int = 80) -> list[tuple[str, str]]:
    """Print-ready list of DDInter names with /, +, and, or a salt word."""
    salts = set(load_salts())
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for raw in sorted(raw_names, key=lambda s: s.lower()):
        low = raw.lower()
        toks = set(re.findall(r"[a-z0-9]+", low))
        if not (_SPECIAL_RE.search(raw) or (toks & salts)):
            continue
        norm = _norm(raw)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        out.append((norm, raw))
        if len(out) >= limit:
            break
    return out


def build_ddinter_pairs() -> pd.DataFrame:
    paths = sorted(DDINTER_DIR.glob("ddinter_downloads_code_*.csv"))
    if not paths:
        raise FileNotFoundError(f"No DDInter CSVs in {DDINTER_DIR}")

    frames = [pd.read_csv(p, usecols=["Drug_A", "Drug_B", "Level"]) for p in paths]
    raw = pd.concat(frames, ignore_index=True)
    print(f"Loaded rows (all files): {len(raw)}")

    # Review names (does not merge)
    all_names = pd.concat([raw["Drug_A"], raw["Drug_B"]]).dropna().astype(str).unique().tolist()
    review = review_complex_names(all_names, 80)
    print("\n=== Up to 80 DDInter names with '/', '+', 'and', or a salt word (for review) ===")
    for i, (norm, raw_name) in enumerate(review, 1):
        print(f"{i:2d}. norm={norm!r}  raw={raw_name!r}")

    raw["level_key"] = raw["Level"].astype(str).str.strip().str.lower()
    before_unknown = len(raw)
    raw = raw[raw["level_key"].isin(LEVEL_RANK)].copy()
    print(f"\nAfter dropping Unknown/other levels: {len(raw)} (from {before_unknown})")

    raw["ing_a"] = raw["Drug_A"].map(_norm)
    raw["ing_b"] = raw["Drug_B"].map(_norm)
    raw = raw[(raw["ing_a"] != "") & (raw["ing_b"] != "") & (raw["ing_a"] != raw["ing_b"])]

    # Unordered pair key
    pair_cols = raw.apply(
        lambda r: tuple(sorted((r["ing_a"], r["ing_b"]))),
        axis=1,
    )
    raw["ing_a"] = pair_cols.map(lambda t: t[0])
    raw["ing_b"] = pair_cols.map(lambda t: t[1])
    raw["rank"] = raw["level_key"].map(LEVEL_RANK)

    before_dedupe = len(raw)
    # Keep highest severity per unordered pair
    idx = raw.groupby(["ing_a", "ing_b"], sort=False)["rank"].idxmax()
    deduped = raw.loc[idx, ["ing_a", "ing_b", "level_key"]].copy()
    deduped = deduped.rename(columns={"level_key": "level"})
    print(f"After unordered dedupe (keep highest level): {len(deduped)} (from {before_dedupe})")

    print("Loading brand ingredient set (expand_brand over parquet)...")
    brand_ings = brand_ingredient_set()
    print(f"Unique ingredients in brand dataset: {len(brand_ings)}")

    before_filter = len(deduped)
    kept = deduped[
        deduped["ing_a"].isin(brand_ings) & deduped["ing_b"].isin(brand_ings)
    ].copy()
    print(f"After both-in-brand-dataset filter: {len(kept)} (from {before_filter})")

    kept["tier"] = kept["level"].map(TIER_MAP)
    kept["source"] = "DDInter 2.0"
    kept = kept.sort_values(["tier", "ing_a", "ing_b"]).reset_index(drop=True)

    tier_counts = Counter(kept["tier"])
    print("Per tier:", dict(tier_counts))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    kept[["ing_a", "ing_b", "level", "tier", "source"]].to_parquet(OUT_PATH, index=False)
    print(f"Saved {OUT_PATH}")
    return kept


def main() -> None:
    # Clear synonym cache if composition cached loaders
    from src.composition import load_synonyms
    from src.ingredient_norm import load_salts

    load_synonyms.cache_clear()
    load_salts.cache_clear()
    build_ddinter_pairs()


if __name__ == "__main__":
    main()
