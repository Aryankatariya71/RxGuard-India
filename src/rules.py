"""Load and query draft clinical rules (interactions + max dose)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import jsonschema
import pandas as pd

from src.composition import normalize_ingredient

ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = ROOT / "data" / "rules"

CURATED_PATH = RULES_DIR / "curated_interactions.json"
CLASSES_PATH = RULES_DIR / "classes.json"
MAX_DOSE_PATH = RULES_DIR / "max_dose.json"
DDINTER_PATH = RULES_DIR / "ddinter_pairs.parquet"

TIER_RANK = {"critical": 3, "review": 2, "info": 1}

CURATED_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": [
            "id",
            "ingredient_a",
            "ingredient_b",
            "tier",
            "mechanism",
            "recommended_action",
            "source_url",
            "verified_by_pharmacist",
            "status",
        ],
        "properties": {
            "id": {"type": "string"},
            "ingredient_a": {"type": "string"},
            "ingredient_b": {"type": "string"},
            "tier": {"type": "string", "enum": ["critical", "review", "info"]},
            "mechanism": {"type": "string"},
            "recommended_action": {"type": "string"},
            "source_url": {"type": "string"},
            "verified_by_pharmacist": {"type": "boolean"},
            "status": {"type": "string"},
        },
        "additionalProperties": True,
    },
}

MAX_DOSE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": [
            "id",
            "ingredient",
            "adult_max_mg_day",
            "pediatric_mg_per_kg_day",
            "min_age_years",
            "renal_adjustment",
            "elderly_note",
            "source_url",
            "verified_by_pharmacist",
            "status",
            "notes",
        ],
        "properties": {
            "id": {"type": "string"},
            "ingredient": {"type": "string"},
            "adult_max_mg_day": {"type": ["number", "null"]},
            "pediatric_mg_per_kg_day": {"type": ["number", "null"]},
            "min_age_years": {"type": ["number", "null"]},
            "renal_adjustment": {
                "type": "object",
                "required": ["normal", "mild_moderate", "severe", "kidney_failure"],
                "properties": {
                    "normal": {"type": ["number", "string", "null"]},
                    "mild_moderate": {"type": ["number", "string", "null"]},
                    "severe": {"type": ["number", "string", "null"]},
                    "kidney_failure": {"type": ["number", "string", "null"]},
                },
                "additionalProperties": True,
            },
            "elderly_note": {"type": ["string", "null"]},
            "source_url": {"type": "string"},
            "verified_by_pharmacist": {"type": "boolean"},
            "status": {"type": "string"},
            "notes": {"type": "string"},
        },
        "additionalProperties": True,
    },
}

CLASSES_SCHEMA = {
    "type": "object",
    "additionalProperties": {
        "type": "array",
        "items": {"type": "string"},
    },
}

# Same-class and cross-class draft rules (expanded when no curated/DDInter hit).
CLASS_PAIR_RULES: list[dict[str, Any]] = [
    {
        "id": "CLASS-NSAID-NSAID",
        "class_a": "nsaid",
        "class_b": "nsaid",
        "same_class": True,
        "tier": "review",
        "mechanism": "Two NSAIDs together increase GI, renal, and cardiovascular risk without added benefit.",
        "recommended_action": "Use a single NSAID at the lowest effective dose; avoid stacking NSAIDs.",
        "source_url": "https://www.fda.gov/drugs",
        "source_label": "class:nsaid+nsaid",
    },
    {
        "id": "CLASS-PPI-PPI",
        "class_a": "ppi",
        "class_b": "ppi",
        "same_class": True,
        "tier": "review",
        "mechanism": "Duplicate PPI therapy is usually unnecessary and may increase adverse-effect risk.",
        "recommended_action": "Continue one PPI only; review indication and duration.",
        "source_url": "https://www.fda.gov/drugs",
        "source_label": "class:ppi+ppi",
    },
    {
        "id": "CLASS-NSAID-ACE",
        "class_a": "nsaid",
        "class_b": "ace_inhibitor",
        "same_class": False,
        "tier": "review",
        "mechanism": "NSAIDs may blunt ACE-inhibitor effect and worsen renal function, especially if volume-depleted.",
        "recommended_action": "Limit NSAID duration; monitor blood pressure, creatinine, and potassium.",
        "source_url": "https://www.fda.gov/drugs",
        "source_label": "class:nsaid+ace_inhibitor",
    },
    {
        "id": "CLASS-NSAID-ARB",
        "class_a": "nsaid",
        "class_b": "arb",
        "same_class": False,
        "tier": "review",
        "mechanism": "NSAIDs plus ARBs can reduce renal perfusion and raise potassium risk.",
        "recommended_action": "Avoid prolonged NSAID use; monitor renal function and electrolytes.",
        "source_url": "https://www.fda.gov/drugs",
        "source_label": "class:nsaid+arb",
    },
]


def clear_rules_cache() -> None:
    load_curated_interactions.cache_clear()
    load_classes.cache_clear()
    load_max_dose.cache_clear()
    load_ddinter_pairs.cache_clear()
    _curated_index.cache_clear()
    _ddinter_index.cache_clear()
    _max_dose_index.cache_clear()
    _ingredient_to_classes.cache_clear()


def _pair_key(a: str, b: str) -> tuple[str, str]:
    x, y = normalize_ingredient(a), normalize_ingredient(b)
    return tuple(sorted((x, y)))  # type: ignore[return-value]


@lru_cache(maxsize=1)
def load_curated_interactions() -> list[dict[str, Any]]:
    data = json.loads(CURATED_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(data, CURATED_SCHEMA)
    return data


@lru_cache(maxsize=1)
def load_classes() -> dict[str, list[str]]:
    data = json.loads(CLASSES_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(data, CLASSES_SCHEMA)
    # Normalize ingredient names in class lists
    out: dict[str, list[str]] = {}
    for cls, ings in data.items():
        out[cls] = [normalize_ingredient(i) for i in ings]
    return out


@lru_cache(maxsize=1)
def load_max_dose() -> list[dict[str, Any]]:
    data = json.loads(MAX_DOSE_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(data, MAX_DOSE_SCHEMA)
    return data


@lru_cache(maxsize=1)
def load_ddinter_pairs() -> pd.DataFrame:
    if not DDINTER_PATH.exists():
        return pd.DataFrame(columns=["ing_a", "ing_b", "level", "tier", "source"])
    return pd.read_parquet(DDINTER_PATH)


@lru_cache(maxsize=1)
def _curated_index() -> dict[tuple[str, str], dict[str, Any]]:
    idx: dict[tuple[str, str], dict[str, Any]] = {}
    for row in load_curated_interactions():
        key = _pair_key(row["ingredient_a"], row["ingredient_b"])
        idx[key] = row
    return idx


@lru_cache(maxsize=1)
def _ddinter_index() -> dict[tuple[str, str], dict[str, Any]]:
    df = load_ddinter_pairs()
    idx: dict[tuple[str, str], dict[str, Any]] = {}
    if df.empty:
        return idx
    for row in df.itertuples(index=False):
        key = (str(row.ing_a), str(row.ing_b))
        # Already sorted in parquet builder
        if key[0] > key[1]:
            key = (key[1], key[0])
        idx[key] = {
            "ing_a": key[0],
            "ing_b": key[1],
            "level": row.level,
            "tier": row.tier,
            "source": row.source,
            "id": f"DDINTER-{key[0]}-{key[1]}",
            "mechanism": f"DDInter {row.level} interaction.",
            "recommended_action": "Review combination with a clinician or pharmacist.",
            "source_url": "https://ddinter.scbdd.com/",
            "verified_by_pharmacist": False,
            "status": "DRAFT",
            "source_label": "DDInter 2.0",
        }
    return idx


@lru_cache(maxsize=1)
def _max_dose_index() -> dict[str, dict[str, Any]]:
    return {
        normalize_ingredient(row["ingredient"]): row for row in load_max_dose()
    }


@lru_cache(maxsize=1)
def _ingredient_to_classes() -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for cls, ings in load_classes().items():
        for ing in ings:
            mapping.setdefault(ing, []).append(cls)
    return mapping


def _class_interaction(a: str, b: str) -> dict[str, Any] | None:
    na, nb = normalize_ingredient(a), normalize_ingredient(b)
    if not na or not nb or na == nb:
        return None
    classes_a = set(_ingredient_to_classes().get(na, []))
    classes_b = set(_ingredient_to_classes().get(nb, []))
    if not classes_a or not classes_b:
        return None

    for rule in CLASS_PAIR_RULES:
        ca, cb = rule["class_a"], rule["class_b"]
        if rule.get("same_class"):
            if ca in classes_a and ca in classes_b:
                return {
                    "id": rule["id"],
                    "ingredient_a": na,
                    "ingredient_b": nb,
                    "tier": rule["tier"],
                    "mechanism": rule["mechanism"],
                    "recommended_action": rule["recommended_action"],
                    "source_url": rule["source_url"],
                    "verified_by_pharmacist": False,
                    "status": "DRAFT",
                    "source": "class",
                    "source_label": rule["source_label"],
                    "source_rule_id": rule["id"],
                }
        else:
            match_ab = ca in classes_a and cb in classes_b
            match_ba = cb in classes_a and ca in classes_b
            if match_ab or match_ba:
                return {
                    "id": rule["id"],
                    "ingredient_a": na,
                    "ingredient_b": nb,
                    "tier": rule["tier"],
                    "mechanism": rule["mechanism"],
                    "recommended_action": rule["recommended_action"],
                    "source_url": rule["source_url"],
                    "verified_by_pharmacist": False,
                    "status": "DRAFT",
                    "source": "class",
                    "source_label": rule["source_label"],
                    "source_rule_id": rule["id"],
                }
    return None


def get_interaction(a: str, b: str) -> dict[str, Any] | None:
    """Lookup interaction: curated > DDInter > class-level. Unordered pair."""
    key = _pair_key(a, b)
    if not key[0] or not key[1] or key[0] == key[1]:
        return None

    curated = _curated_index().get(key)
    if curated is not None:
        out = dict(curated)
        out["source"] = "curated"
        out["source_label"] = f"curated:{out['id']}"
        out["source_rule_id"] = out["id"]
        out["ingredient_a"], out["ingredient_b"] = key
        return out

    dd = _ddinter_index().get(key)
    if dd is not None:
        out = dict(dd)
        out["source_rule_id"] = out["id"]
        return out

    return _class_interaction(a, b)


def get_max_dose(ingredient: str) -> dict[str, Any] | None:
    """Return max-dose rule for ingredient, or None if unknown."""
    name = normalize_ingredient(ingredient)
    if not name:
        return None
    row = _max_dose_index().get(name)
    return dict(row) if row is not None else None
