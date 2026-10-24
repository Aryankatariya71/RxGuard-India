"""Parse and normalize brand medicine compositions (deterministic)."""

from __future__ import annotations

import json
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PARQUET_PATH = ROOT / "data" / "brands_clean.parquet"
SYNONYMS_PATH = ROOT / "data" / "synonyms.json"
OVERRIDES_PATH = ROOT / "data" / "combo_overrides.json"

_WHITESPACE_RE = re.compile(r"\s+")

# Ingredient name, then parenthetical strength blob.
_COMPOSITION_RE = re.compile(
    r"^(?P<ingredient>.+?)\s*\(\s*(?P<inside>[^)]*)\s*\)\s*$",
)

# Strength patterns, e.g. 500mg | 30mg/5ml | 100IU/ml | 2% | 2% w/w | 0.25mcg | 1gm
# `gm` is treated as an alias for `g` (common on Indian pack labels).
_STRENGTH_RE = re.compile(
    r"^(?P<value>\d+(?:\.\d+)?)\s*"
    r"(?P<unit>mcg|mg|gm|g|iu|%|ml)"
    r"(?:\s*w/[wv])?"
    r"(?:\s*/\s*(?:(?P<per_value>\d+(?:\.\d+)?)\s*)?(?P<per_unit>mcg|mg|gm|g|iu|%|ml))?"
    r"\s*$",
    re.IGNORECASE,
)

_UNIT_ALIASES = {"gm": "g"}

_LIQUID_FORMS = frozenset({"syrup", "suspension", "drops"})


def _is_null(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _empty_result(raw: str, *, parse_error: bool = False, strength_missing: bool = False) -> dict:
    return {
        "ingredient": "",
        "ingredient_full": "",
        "strength_value": None,
        "unit": None,
        "per_value": None,
        "per_unit": None,
        "per_unit_missing": False,
        "strength_missing": strength_missing,
        "raw": raw,
        "parse_error": parse_error,
    }


@lru_cache(maxsize=1)
def load_synonyms() -> dict[str, str]:
    with SYNONYMS_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    return {str(k).strip().lower(): str(v).strip().lower() for k, v in data.items()}


@lru_cache(maxsize=1)
def load_combo_overrides() -> dict[str, list[dict]]:
    """Return map of name_norm -> ingredient list."""
    with OVERRIDES_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    overrides = data.get("overrides", data if isinstance(data, list) else [])
    out: dict[str, list[dict]] = {}
    for entry in overrides:
        key = str(entry["name_norm"]).strip().lower()
        out[key] = list(entry["ingredients"])
    return out


def normalize_ingredient(name: str) -> str:
    """
    Canonical base ingredient name.

    Applies synonyms.json, salt/ester stripping (data/salts.json), protected-name
    rules, and clavulanate/diclofenac family aliases via ingredient_norm.
    """
    from src.ingredient_norm import normalize_ingredient_parts

    return normalize_ingredient_parts(name)["ingredient"]


def normalize_ingredient_detailed(name: str) -> dict[str, str]:
    """Return both ingredient (base) and ingredient_full (pre-strip)."""
    from src.ingredient_norm import normalize_ingredient_parts

    return normalize_ingredient_parts(name)


def parse_composition(text: Any) -> dict:
    """Parse a single composition string into a structured dict."""
    if _is_null(text):
        return _empty_result("", parse_error=True)

    raw = str(text)
    collapsed = _WHITESPACE_RE.sub(" ", raw).strip()
    if not collapsed or collapsed.lower() == "<na>":
        return _empty_result(raw, parse_error=True)

    match = _COMPOSITION_RE.match(collapsed)
    if not match:
        # No brackets / no strength — ingredient-only, not an error.
        parts = normalize_ingredient_detailed(collapsed)
        return {
            "ingredient": parts["ingredient"],
            "ingredient_full": parts["ingredient_full"],
            "strength_value": None,
            "unit": None,
            "per_value": None,
            "per_unit": None,
            "per_unit_missing": False,
            "strength_missing": True,
            "raw": raw,
            "parse_error": False,
        }

    parts = normalize_ingredient_detailed(match.group("ingredient"))
    ingredient = parts["ingredient"]
    ingredient_full = parts["ingredient_full"]
    inside = match.group("inside").strip()

    if not inside or inside.upper() == "NA":
        return {
            "ingredient": ingredient,
            "ingredient_full": ingredient_full,
            "strength_value": None,
            "unit": None,
            "per_value": None,
            "per_unit": None,
            "per_unit_missing": False,
            "strength_missing": True,
            "raw": raw,
            "parse_error": False,
        }

    strength = _STRENGTH_RE.match(inside)
    if not strength:
        return {
            "ingredient": ingredient,
            "ingredient_full": ingredient_full,
            "strength_value": None,
            "unit": None,
            "per_value": None,
            "per_unit": None,
            "per_unit_missing": False,
            "strength_missing": True,
            "raw": raw,
            "parse_error": True,
        }

    unit = _UNIT_ALIASES.get(strength.group("unit").lower(), strength.group("unit").lower())
    per_unit_raw = strength.group("per_unit")
    per_unit = (
        _UNIT_ALIASES.get(per_unit_raw.lower(), per_unit_raw.lower())
        if per_unit_raw
        else None
    )
    per_value_raw = strength.group("per_value")
    per_value = float(per_value_raw) if per_value_raw is not None else None

    return {
        "ingredient": ingredient,
        "ingredient_full": ingredient_full,
        "strength_value": float(strength.group("value")),
        "unit": unit,
        "per_value": per_value,
        "per_unit": per_unit,
        "per_unit_missing": False,
        "strength_missing": False,
        "raw": raw,
        "parse_error": False,
    }


def _row_get(row: Any, key: str) -> Any:
    if isinstance(row, dict):
        return row.get(key)
    if hasattr(row, "get"):
        try:
            return row.get(key)
        except Exception:
            pass
    index = getattr(row, "index", None)
    if index is not None and key in index:
        return row[key]
    return getattr(row, key, None)


def _is_liquid_form(row: Any) -> bool:
    form = str(_row_get(row, "form") or "").lower()
    if form in _LIQUID_FORMS:
        return True
    # Dry syrup may be mistyped in form; also match pack/name explicitly.
    pack = str(_row_get(row, "pack_size_label") or "").lower()
    name = str(_row_get(row, "name") or "").lower()
    return "dry syrup" in pack or "dry syrup" in name


def expand_brand(row: Any, overrides: dict[str, list[dict]] | None = None) -> list[dict]:
    """
    Expand a brand row into ingredient dicts.
    Checks combo_overrides.json (by name_norm) first, then parses compositions.
    """
    name_norm = _row_get(row, "name_norm")
    if _is_null(name_norm):
        name = _row_get(row, "name")
        name_norm = (
            _WHITESPACE_RE.sub(" ", str(name)).strip().lower()
            if not _is_null(name)
            else ""
        )
    else:
        name_norm = str(name_norm).strip().lower()

    ov = overrides if overrides is not None else load_combo_overrides()
    if name_norm in ov:
        # Return copies so callers can annotate without mutating the cache.
        return [dict(item) for item in ov[name_norm]]

    ingredients: list[dict] = []
    for col in ("short_composition1", "short_composition2"):
        value = _row_get(row, col)
        if _is_null(value):
            continue
        text = str(value).strip()
        if not text or text.lower() == "<na>":
            continue
        parsed = parse_composition(text)
        ingredients.append(parsed)

    if _is_liquid_form(row):
        for item in ingredients:
            if item.get("per_unit") is None and not item.get("strength_missing"):
                item["per_unit_missing"] = True

    return ingredients


def frequent_ingredients_not_in_synonyms(df: pd.DataFrame, top_n: int = 50) -> list[tuple[str, int]]:
    """Most common raw ingredient names (pre-synonym) absent from synonyms keys/values."""
    synonyms = load_synonyms()
    covered = set(synonyms.keys()) | set(synonyms.values())
    counts: Counter[str] = Counter()
    for col in ("short_composition1", "short_composition2"):
        for value in df[col].dropna():
            text = _WHITESPACE_RE.sub(" ", str(value)).strip()
            match = _COMPOSITION_RE.match(text)
            raw_name = match.group("ingredient") if match else text
            key = _WHITESPACE_RE.sub(" ", raw_name).strip().lower()
            if key and key not in covered:
                counts[key] += 1
    return counts.most_common(top_n)


def scan_parquet(path: Path = PARQUET_PATH) -> dict:
    """Expand every brand row; return aggregate parse stats."""
    df = pd.read_parquet(path)
    fail_rows = 0
    strength_missing_rows = 0
    failures: list[dict] = []
    overrides = load_combo_overrides()

    # name=None avoids NamedTuple clobbering the `name` column.
    columns = list(df.columns)
    for tup in df.itertuples(index=False, name=None):
        row = dict(zip(columns, tup, strict=True))
        items = expand_brand(row, overrides=overrides)
        row_fail = any(i.get("parse_error") for i in items)
        row_missing = any(i.get("strength_missing") for i in items)
        if row_fail:
            fail_rows += 1
            if len(failures) < 20:
                failures.append(
                    {
                        "id": int(row["id"]),
                        "name": row["name"],
                        "form": row["form"],
                        "items": [
                            {
                                "raw": i["raw"],
                                "ingredient": i["ingredient"],
                                "parse_error": i["parse_error"],
                                "strength_missing": i["strength_missing"],
                            }
                            for i in items
                            if i.get("parse_error")
                        ],
                    }
                )
        if row_missing:
            strength_missing_rows += 1

    return {
        "total_rows": len(df),
        "rows_fail_to_parse": fail_rows,
        "rows_with_strength_missing": strength_missing_rows,
        "sample_failures": failures,
        "unmapped_top50": frequent_ingredients_not_in_synonyms(df, 50),
    }


def main() -> None:
    load_synonyms.cache_clear()
    load_combo_overrides.cache_clear()
    stats = scan_parquet()

    print("=" * 60)
    print("SYNONYM COVERAGE — top 50 ingredients NOT in synonyms map")
    print("=" * 60)
    for name, count in stats["unmapped_top50"]:
        print(f"{count:6d}  {name}")

    print("\n" + "=" * 60)
    print("EXPAND_BRAND SCAN")
    print("=" * 60)
    print(f"total rows: {stats['total_rows']}")
    print(f"rows fail to parse: {stats['rows_fail_to_parse']}")
    print(f"rows with strength_missing: {stats['rows_with_strength_missing']}")

    print("\n" + "=" * 60)
    print("20 SAMPLE FAILURES")
    print("=" * 60)
    if not stats["sample_failures"]:
        print("(none)")
    for sample in stats["sample_failures"]:
        print(f"\nid={sample['id']} name={sample['name']!r} form={sample['form']}")
        for item in sample["items"]:
            print(f"  raw={item['raw']!r} ingredient={item['ingredient']!r}")


if __name__ == "__main__":
    main()
