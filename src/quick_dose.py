"""Draft max-dose checks against commonly cited label limits."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.patient import Patient

ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = ROOT / "data" / "rules" / "max_dose_draft.json"


@lru_cache(maxsize=1)
def load_max_dose_rules() -> dict[str, dict[str, Any]]:
    with RULES_PATH.open(encoding="utf-8") as f:
        rows = json.load(f)
    return {str(r["ingredient"]).strip().lower(): r for r in rows}


def check_doses(daily_dose_result: dict, patient: Patient) -> list[dict]:
    """
    Compare daily totals to draft adult/pediatric limits.

    Returns alerts:
      {ingredient, total_mg, limit_mg, percent, tier, reason, basis}
    tier: critical | review | info
    """
    rules = load_max_dose_rules()
    by_ing = daily_dose_result.get("by_ingredient") or []
    age = float(patient.age_years)
    weight = patient.weight_kg
    is_child = age < 18.0

    alerts: list[dict] = []
    needs_weight_info = False

    for row in by_ing:
        name = str(row.get("ingredient") or "").strip().lower()
        unit = str(row.get("unit") or "").lower()
        if name not in rules or unit != "mg":
            continue

        rule = rules[name]
        total = float(row.get("total_mg_per_day") or 0)
        assumed = any(c.get("assumed_max") for c in (row.get("contributions") or []))

        limit: float | None = None
        basis = ""

        ped_mg_kg: float | None = None
        if is_child:
            ped = rule.get("pediatric_mg_per_kg_day")
            if ped is None:
                continue
            if weight is None or float(weight) <= 0:
                needs_weight_info = True
                continue
            ped_mg_kg = float(ped)
            w = float(weight)
            limit = w * ped_mg_kg
            basis = "pediatric_mg_per_kg"
        else:
            adult = rule.get("adult_max_mg_day")
            if adult is None:
                continue
            limit = float(adult)
            basis = "adult_max"

        if limit is None or limit <= 0:
            continue

        percent = (total / limit) * 100.0
        if is_child and ped_mg_kg is not None:
            formula = (
                f"{float(weight):g} kg x {ped_mg_kg:g} mg/kg = {limit:g} mg/day limit"
            )
            if total > limit:
                tier = "critical"
                reason = (
                    f"{name} total {total:g} mg/day exceeds pediatric draft limit "
                    f"({formula}; {percent:.0f}% of limit)."
                )
            elif percent >= 80.0:
                tier = "review"
                reason = (
                    f"{name} total {total:g} mg/day is {percent:.0f}% of pediatric "
                    f"draft limit ({formula}) — review with prescriber."
                )
            else:
                continue
        else:
            if total > limit:
                tier = "critical"
                reason = (
                    f"{name} total {total:g} mg/day exceeds draft limit "
                    f"{limit:g} mg/day ({percent:.0f}% of limit)."
                )
            elif percent >= 80.0:
                tier = "review"
                reason = (
                    f"{name} total {total:g} mg/day is {percent:.0f}% of draft limit "
                    f"{limit:g} mg/day — review with prescriber."
                )
            else:
                continue

        if assumed:
            reason += " (assumed at max frequency)"

        alerts.append(
            {
                "ingredient": name,
                "total_mg": total,
                "limit_mg": limit,
                "percent": percent,
                "tier": tier,
                "reason": reason,
                "basis": basis,
            }
        )

    if is_child and needs_weight_info:
        alerts.append(
            {
                "ingredient": None,
                "total_mg": None,
                "limit_mg": None,
                "percent": None,
                "tier": "info",
                "reason": "Weight needed for pediatric dose check",
                "basis": "weight_needed",
            }
        )

    return alerts
