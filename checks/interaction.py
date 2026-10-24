"""Drug–drug interaction checks via src.rules.get_interaction."""

from __future__ import annotations

from itertools import combinations
from typing import Any

from src.rules import get_interaction


def _ingredient_brand_map(daily_dose_result: dict) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for row in daily_dose_result.get("by_ingredient") or []:
        name = str(row.get("ingredient") or "")
        if not name:
            continue
        brands: list[str] = []
        for c in row.get("contributions") or []:
            b = c.get("brand")
            if b and b not in brands:
                brands.append(str(b))
        mapping[name] = brands
    return mapping


def check_interactions(daily_dose_result: dict) -> list[dict]:
    """
    Check every unordered pair of distinct ingredients via rules.get_interaction.

    Includes curated, DDInter, and class-level pairs. Each alert carries
    mechanism and recommended action from the rule.
    """
    brand_map = _ingredient_brand_map(daily_dose_result)
    names = sorted(brand_map.keys())
    alerts: list[dict] = []

    for a, b in combinations(names, 2):
        hit = get_interaction(a, b)
        if hit is None:
            continue

        brands: list[str] = []
        for n in (a, b):
            for br in brand_map.get(n, []):
                if br not in brands:
                    brands.append(br)

        rule_id = hit.get("source_rule_id") or hit.get("id") or f"INT-{a}-{b}"
        mechanism = hit.get("mechanism") or "Interaction flagged by rules engine."
        action = (
            hit.get("recommended_action")
            or "Review combination with a clinician or pharmacist."
        )
        tier = hit.get("tier") or "review"
        source_label = hit.get("source_label") or hit.get("source") or "interaction"

        draft = ""
        if hit.get("verified_by_pharmacist") is not True:
            draft = " Draft rule, pending pharmacist verification."

        alerts.append(
            {
                "id": f"INT-{a}+{b}",
                "type": "interaction",
                "tier": tier,
                "title": f"Interaction: {a} + {b}",
                "reason": f"{mechanism}{draft}",
                "suggested_action": action,
                "ingredients": sorted([a, b]),
                "brands": brands,
                "source_rule_id": str(rule_id),
                "source_label": str(source_label),
                "mechanism": mechanism,
            }
        )

    return alerts
