"""Salt/ester stripping and protected-name rules for ingredient normalization."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SALTS_PATH = ROOT / "data" / "salts.json"
PARQUET_PATH = ROOT / "data" / "brands_clean.parquet"

_WHITESPACE_RE = re.compile(r"\s+")

# Whole-name phrases that must NOT lose a trailing token (drug IS "... acid", etc.).
PROTECTED_NAMES = frozenset(
    {
        "clavulanic acid",
        "mefenamic acid",
        "folic acid",
        "salicylic acid",
        "benzoic acid",
        "ascorbic acid",
        "citric acid",
        "fusidic acid",
        "nalidixic acid",
        "tranexamic acid",
        "valproic acid",
        "pantothenic acid",
        "thioctic acid",
        "uric acid",
        "amino acid",
        "amoxicillin",
        "amoxycillin",
        "clavulanate",  # mapped specially; do not strip further
    }
)

# Explicit alias families applied before/after salt stripping.
SPECIAL_ALIASES: dict[str, str] = {
    "clavulanate": "clavulanic acid",
    "clavulanic acid": "clavulanic acid",
    "potassium clavulanate": "clavulanic acid",
    "clavulanate potassium": "clavulanic acid",
    "clavulanic acid potassium": "clavulanic acid",
    "diclofenac": "diclofenac",
    "diclofenac sodium": "diclofenac",
    "diclofenac potassium": "diclofenac",
    "diclofenac diethylamine": "diclofenac",
    "diclofenac diethylammonium": "diclofenac",
    "diclofenac resinate": "diclofenac",
    "diclofenac epolamine": "diclofenac",
}

TARGET_INGREDIENTS = [
    "paracetamol",
    "ibuprofen",
    "diclofenac",
    "aceclofenac",
    "nimesulide",
    "mefenamic acid",
    "amoxicillin",
    "clavulanic acid",
    "azithromycin",
    "cetirizine",
    "levocetirizine",
    "pantoprazole",
    "rabeprazole",
    "omeprazole",
    "domperidone",
    "metformin",
    "glimepiride",
    "atorvastatin",
    "rosuvastatin",
    "aspirin",
    "clopidogrel",
    "warfarin",
    "amlodipine",
    "telmisartan",
    "metoprolol",
    "ramipril",
    "enalapril",
    "tramadol",
    "ondansetron",
    "montelukast",
]


@lru_cache(maxsize=1)
def load_salts() -> list[str]:
    with SALTS_PATH.open(encoding="utf-8") as f:
        salts = [str(s).strip().lower() for s in json.load(f)]
    # Longest first so "hydrochloride" wins over shorter tokens if ever overlapping.
    return sorted(set(salts), key=len, reverse=True)


@lru_cache(maxsize=1)
def _salt_suffix_re() -> re.Pattern[str]:
    salts = load_salts()
    alternation = "|".join(re.escape(s) for s in salts)
    return re.compile(rf"^(?P<base>.+?)\s+(?:{alternation})$", re.IGNORECASE)


def _collapse(name: str) -> str:
    return _WHITESPACE_RE.sub(" ", str(name)).strip().lower()


def strip_salt_suffix(name: str) -> str:
    """
    Strip one trailing salt/ester suffix unless the full name is protected.
    Does not strip when the name is itself a distinct drug (protected list).
    """
    text = _collapse(name)
    if not text or text in PROTECTED_NAMES:
        return text

    match = _salt_suffix_re().match(text)
    if not match:
        return text

    base = match.group("base").strip()
    if not base or base in load_salts():
        return text
    # If the full protected phrase would be destroyed, keep original.
    if text in PROTECTED_NAMES:
        return text
    return base


def normalize_ingredient_parts(name: str) -> dict[str, str]:
    """
    Return ingredient_full (pre-strip canonical text) and ingredient (base + aliases).

    Pipeline:
      1. lowercase / collapse whitespace
      2. record ingredient_full
      3. special aliases (clavulanate / diclofenac families)
      4. salt/ester strip (unless protected)
      5. synonyms.json via composition.load_synonyms
      6. special aliases again (post-strip)
    """
    # Local import avoids circular import at module load.
    from src.composition import load_synonyms

    full = _collapse(name)
    if not full:
        return {"ingredient": "", "ingredient_full": ""}

    working = SPECIAL_ALIASES.get(full, full)
    if working not in PROTECTED_NAMES and full not in PROTECTED_NAMES:
        working = strip_salt_suffix(working)

    synonyms = load_synonyms()
    working = synonyms.get(working, working)
    working = SPECIAL_ALIASES.get(working, working)

    # Synonym may expand to a salted form (rare); strip once more unless protected.
    if working not in PROTECTED_NAMES:
        stripped = strip_salt_suffix(working)
        working = synonyms.get(stripped, stripped)
        working = SPECIAL_ALIASES.get(working, working)

    return {"ingredient": working, "ingredient_full": full}


def ingredient_still_has_salt_word(ingredient: str) -> bool:
    """True if the normalized base still contains a configured salt token as a word."""
    text = _collapse(ingredient)
    if not text:
        return False
    salts = load_salts()
    tokens = set(text.split())
    return any(salt in tokens for salt in salts)


def scan_normalized_ingredients(path: Path = PARQUET_PATH) -> dict[str, Any]:
    """Scan brands_clean.parquet and aggregate normalized ingredient stats."""
    from src.composition import expand_brand, load_combo_overrides

    df = pd.read_parquet(path)
    overrides = load_combo_overrides()
    ingredient_counts: Counter[str] = Counter()
    salted_leftovers: Counter[str] = Counter()
    # brand (row) ids per target ingredient
    target_brands: dict[str, set[int]] = defaultdict(set)

    columns = list(df.columns)
    for tup in df.itertuples(index=False, name=None):
        row = dict(zip(columns, tup, strict=True))
        brand_id = int(row["id"])
        items = expand_brand(row, overrides=overrides)
        seen_in_row: set[str] = set()
        for item in items:
            ing = item.get("ingredient") or ""
            if not ing:
                continue
            ingredient_counts[ing] += 1
            if ingredient_still_has_salt_word(ing):
                salted_leftovers[ing] += 1
            if ing in TARGET_INGREDIENTS:
                seen_in_row.add(ing)
        for ing in seen_in_row:
            target_brands[ing].add(brand_id)

    return {
        "total_rows": len(df),
        "top60": ingredient_counts.most_common(60),
        "still_salted": sorted(salted_leftovers.items(), key=lambda x: (-x[1], x[0])),
        "target_brand_counts": {
            name: len(target_brands.get(name, set())) for name in TARGET_INGREDIENTS
        },
    }


def main() -> None:
    load_salts.cache_clear()
    _salt_suffix_re.cache_clear()
    stats = scan_normalized_ingredients()

    print("=" * 60)
    print("60 MOST FREQUENT NORMALIZED INGREDIENTS")
    print("=" * 60)
    for name, count in stats["top60"]:
        print(f"{count:6d}  {name}")

    print("\n" + "=" * 60)
    print("INGREDIENTS WHOSE NAME STILL CONTAINS A SALT WORD")
    print("=" * 60)
    if not stats["still_salted"]:
        print("(none)")
    else:
        for name, count in stats["still_salted"]:
            print(f"{count:6d}  {name}")

    print("\n" + "=" * 60)
    print("TARGET INGREDIENT COVERAGE (brands containing each)")
    print("=" * 60)
    for name in TARGET_INGREDIENTS:
        n = stats["target_brand_counts"][name]
        status = "PRESENT" if n > 0 else "MISSING"
        print(f"{status:8s}  {n:6d}  {name}")


if __name__ == "__main__":
    main()
