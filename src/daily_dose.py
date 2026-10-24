"""Resolve prescription lines to brands and compute per-ingredient daily dose."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from src.composition import expand_brand
from src.patient import Patient
from src.resolver import resolve

ROOT = Path(__file__).resolve().parent.parent
PARQUET_PATH = ROOT / "data" / "brands_clean.parquet"

_FORM_QUERY_WORD = {
    "tablet": "tab",
    "capsule": "cap",
    "syrup": "syp",
    "injection": "inj",
    "suspension": "susp",
    "drops": "drops",
    "cream": "cream",
}

_PRN_ASSUMED_MAX_DOSES = 4


@lru_cache(maxsize=1)
def _load_brands(parquet_path: str | None = None) -> pd.DataFrame:
    path = Path(parquet_path) if parquet_path else PARQUET_PATH
    return pd.read_parquet(path)


def clear_daily_dose_caches() -> None:
    _load_brands.cache_clear()


def _brand_row(brand_id: int, parquet_path: str | None = None) -> dict[str, Any]:
    df = _load_brands(parquet_path)
    hits = df[df["id"] == brand_id]
    if hits.empty:
        raise KeyError(f"brand_id {brand_id} not found in catalog")
    return hits.iloc[0].to_dict()


def _build_resolve_query(item: dict) -> str:
    drug = str(item.get("drug_text") or "").strip()
    form_hint = item.get("form_hint")
    if form_hint:
        word = _FORM_QUERY_WORD.get(str(form_hint).lower(), str(form_hint))
        return f"{word} {drug}".strip()
    return drug


def resolve_prescription(
    items: list[dict],
    *,
    top_n: int = 3,
    parquet_path: str | None = None,
) -> dict[str, list[dict]]:
    """
    Resolve each parsed rx line to a catalog brand and expand ingredients.

    exact/confident -> resolved (with ingredients)
    ambiguous/not_found -> needs_confirmation (never silently skipped)
    """
    resolved: list[dict] = []
    needs_confirmation: list[dict] = []

    for item in items:
        query = _build_resolve_query(item)
        result = resolve(query, top_n=top_n, parquet_path=parquet_path)
        status = result.get("status")
        candidates = result.get("candidates") or []

        if status in {"exact", "confident"} and candidates:
            top = candidates[0]
            row = _brand_row(int(top["brand_id"]), parquet_path=parquet_path)
            ingredients = expand_brand(row)
            resolved.append(
                {
                    **item,
                    "resolve_status": status,
                    "resolve_query": query,
                    "brand_id": int(top["brand_id"]),
                    "brand_name": top["name"],
                    "resolve_score": top.get("score"),
                    "candidates": candidates,
                    "ingredients": ingredients,
                }
            )
        else:
            needs_confirmation.append(
                {
                    **item,
                    "resolve_status": status or "not_found",
                    "resolve_query": query,
                    "candidates": candidates,
                    "reason": (
                        "ambiguous brand match"
                        if status == "ambiguous"
                        else "brand not found"
                    ),
                }
            )

    return {"resolved": resolved, "needs_confirmation": needs_confirmation}


def _to_mg(strength_value: float, unit: str | None) -> tuple[float | None, str]:
    """Convert strength to mg when possible. Returns (value, unit)."""
    if strength_value is None or unit is None:
        return None, unit or ""
    u = unit.lower()
    if u == "mg":
        return float(strength_value), "mg"
    if u == "g":
        return float(strength_value) * 1000.0, "mg"
    if u == "mcg":
        return float(strength_value) / 1000.0, "mg"
    # IU and % stay in their own unit
    return float(strength_value), u


def _mg_per_single_dose(
    ingredient: dict,
    *,
    dose_amount: float,
    dose_unit: str | None,
) -> tuple[float | None, str, str | None]:
    """
    Amount of ingredient in one administered dose.

    Returns (amount, unit, unclear_reason). unclear_reason set => do not compute.
    """
    if ingredient.get("per_unit_missing"):
        return None, "", "per_unit_missing"
    if ingredient.get("strength_missing") or ingredient.get("strength_value") is None:
        return None, "", "strength_missing"
    if ingredient.get("parse_error"):
        return None, "", "parse_error"

    strength = float(ingredient["strength_value"])
    unit = ingredient.get("unit")
    per_value = ingredient.get("per_value")
    per_unit = ingredient.get("per_unit")

    # Liquid / syrup / suspension: scale by dose_ml / per_value
    is_liquid_dose = (dose_unit or "").lower() == "ml" or (
        per_unit == "ml" and per_value is not None
    )
    if is_liquid_dose and per_value is not None and float(per_value) > 0:
        amount = strength * (float(dose_amount) / float(per_value))
        amount_mg, out_unit = _to_mg(amount, unit)
        if amount_mg is None:
            return None, out_unit, "unsupported_unit"
        return amount_mg, out_unit, None

    # Solid / injection default: strength × number of units
    amount_mg, out_unit = _to_mg(strength, unit)
    if amount_mg is None:
        return None, out_unit, "unsupported_unit"
    return amount_mg * float(dose_amount), out_unit, None


def _doses_per_day(item: dict) -> tuple[float, bool]:
    """Return (times_per_day, assumed_max)."""
    if item.get("prn"):
        stated = item.get("times_per_day")
        if stated is not None:
            return float(stated), False
        return float(_PRN_ASSUMED_MAX_DOSES), True
    times = item.get("times_per_day")
    if times is None:
        return 0.0, False
    return float(times), False


def daily_dose_by_ingredient(
    resolved_items: list[dict],
    patient: Patient | None = None,
) -> dict[str, Any]:
    """
    Sum daily ingredient exposure across all resolved brands.

    patient is accepted for future renal/age adjustments; not used in totals yet.
    """
    _ = patient  # reserved for decision-support rules

    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    strength_unclear: list[dict] = []

    for item in resolved_items:
        brand = item.get("brand_name") or item.get("drug_text") or "unknown"
        dose_amount = float(item.get("dose_amount") or 1)
        dose_unit = item.get("dose_unit")
        times, assumed_max = _doses_per_day(item)
        duration_days = item.get("duration_days")
        ingredients = item.get("ingredients") or []

        for ing in ingredients:
            name = ing.get("ingredient") or ""
            if not name:
                continue

            per_dose, unit, unclear = _mg_per_single_dose(
                ing, dose_amount=dose_amount, dose_unit=dose_unit
            )
            if unclear:
                strength_unclear.append(
                    {
                        "ingredient": name,
                        "brand": brand,
                        "reason": unclear,
                        "raw": ing.get("raw"),
                    }
                )
                continue

            if times <= 0:
                # Frequency missing on a resolved line — skip numeric total
                strength_unclear.append(
                    {
                        "ingredient": name,
                        "brand": brand,
                        "reason": "frequency_missing",
                        "raw": ing.get("raw"),
                    }
                )
                continue

            mg_per_day = float(per_dose) * times
            key = (name, unit)
            bucket = buckets.get(key)
            contribution = {
                "brand": brand,
                "mg_per_day": mg_per_day,
                "assumed_max": assumed_max,
            }
            if duration_days is not None:
                contribution["duration_days"] = duration_days

            if bucket is None:
                buckets[key] = {
                    "ingredient": name,
                    "total_mg_per_day": mg_per_day,
                    "unit": unit,
                    "contributions": [contribution],
                }
            else:
                bucket["total_mg_per_day"] += mg_per_day
                bucket["contributions"].append(contribution)

    by_ingredient = sorted(
        buckets.values(),
        key=lambda x: (x["ingredient"], x["unit"]),
    )
    # Clean float display noise for whole numbers
    for row in by_ingredient:
        total = row["total_mg_per_day"]
        if abs(total - round(total)) < 1e-9:
            row["total_mg_per_day"] = float(round(total))
        for c in row["contributions"]:
            v = c["mg_per_day"]
            if abs(v - round(v)) < 1e-9:
                c["mg_per_day"] = float(round(v))

    return {
        "by_ingredient": by_ingredient,
        "strength_unclear": strength_unclear,
    }
