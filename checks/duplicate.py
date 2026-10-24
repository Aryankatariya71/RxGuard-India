"""Duplicate-ingredient and same-class duplication checks."""

from __future__ import annotations

from typing import Any

from src.rules import get_max_dose, load_classes

# Classes where co-prescribing two members is a duplication concern.
DUP_CLASSES = ("nsaid", "ppi")


def _brands_for_ingredient(row: dict) -> list[str]:
    brands: list[str] = []
    for c in row.get("contributions") or []:
        b = c.get("brand")
        if b and b not in brands:
            brands.append(str(b))
    return brands


def _ingredient_rows(daily_dose_result: dict) -> list[dict]:
    return list(daily_dose_result.get("by_ingredient") or [])


def check_duplicates(daily_dose_result: dict) -> list[dict]:
    """
    Flag same ingredient across 2+ brands, and same-class pairs (NSAID, PPI).

    Tier is review by default; critical only if combined daily dose exceeds a
    known adult max (when a numeric adult_max_mg_day exists).
    """
    alerts: list[dict] = []
    rows = _ingredient_rows(daily_dose_result)
    by_name = {str(r["ingredient"]): r for r in rows if r.get("ingredient")}

    # --- Same ingredient in multiple brands ---
    for name, row in by_name.items():
        brands = _brands_for_ingredient(row)
        if len(brands) < 2:
            continue
        total = float(row.get("total_mg_per_day") or 0)
        unit = str(row.get("unit") or "mg")
        rule = get_max_dose(name)
        tier = "review"
        limit = None
        if rule and rule.get("adult_max_mg_day") is not None and unit == "mg":
            limit = float(rule["adult_max_mg_day"])
            if total > limit:
                tier = "critical"

        brand_list = ", ".join(brands)
        if tier == "critical" and limit is not None:
            pct = (total / limit) * 100.0
            reason = (
                f"{name.title()} appears in {brand_list}: combined {total:g} {unit}/day "
                f"exceeds adult draft limit {limit:g} mg/day ({pct:.0f}%)."
            )
            action = "Stop duplicate sources; keep a single product within the limit."
        else:
            reason = (
                f"{name.title()} appears in more than one product ({brand_list}); "
                f"combined total {total:g} {unit}/day — review for unintended duplication."
            )
            action = "Confirm whether both products are intentional; prefer a single source."

        source_id = rule["id"] if rule else "DUP-ING"
        alerts.append(
            {
                "id": f"DUP-{name}",
                "type": "duplicate",
                "tier": tier,
                "title": f"Duplicate {name}",
                "reason": reason,
                "suggested_action": action,
                "ingredients": [name],
                "brands": brands,
                "source_rule_id": source_id,
                "source_label": "duplicate_ingredient",
                "total_mg_per_day": total,
            }
        )

    # --- Same-class duplication (distinct ingredients) ---
    classes = load_classes()
    present = set(by_name.keys())
    for cls in DUP_CLASSES:
        members = [m for m in classes.get(cls, []) if m in present]
        if len(members) < 2:
            continue
        # One alert listing all class members present
        brands: list[str] = []
        for m in members:
            for b in _brands_for_ingredient(by_name[m]):
                if b not in brands:
                    brands.append(b)
        members_sorted = sorted(members)
        reason = (
            f"More than one {cls.replace('_', ' ')} on this prescription: "
            f"{', '.join(members_sorted)} (brands: {', '.join(brands)})."
        )
        alerts.append(
            {
                "id": f"DUP-CLASS-{cls}-{'+'.join(members_sorted)}",
                "type": "duplicate",
                "tier": "review",
                "title": f"Duplicate {cls.replace('_', ' ')} class",
                "reason": reason,
                "suggested_action": (
                    f"Use a single {cls.replace('_', ' ')} agent unless a clinician "
                    "explicitly intends combination therapy."
                ),
                "ingredients": members_sorted,
                "brands": brands,
                "source_rule_id": f"CLASS-DUP-{cls}",
                "source_label": f"class_duplicate:{cls}",
            }
        )

    return alerts
