"""Duplicate active ingredient detection (deterministic)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def detect_duplicates(resolved_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    resolved_items: [{item_id, product_id, brand_name, ingredients: [{id, name}]}]

    Unresolved items are excluded from definitive duplicate matching.
    """
    by_ing: dict[str, list[dict]] = defaultdict(list)

    for item in resolved_items:
        if item.get("resolution_status") != "resolved":
            continue
        seen_in_item: set[str] = set()
        for ing in item.get("ingredients") or []:
            iid = ing.get("id")
            if not iid or iid in seen_in_item:
                continue
            seen_in_item.add(iid)
            by_ing[iid].append(
                {
                    "item_id": item["item_id"],
                    "product_id": item.get("product_id"),
                    "brand_name": item.get("brand_name"),
                    "ingredient_name": ing.get("name"),
                }
            )

    findings: list[dict[str, Any]] = []
    for iid, occ in by_ing.items():
        product_ids = {o["product_id"] for o in occ if o.get("product_id")}
        # Distinct products OR same brand added twice as separate items
        distinct_items = {o["item_id"] for o in occ}
        if len(distinct_items) < 2:
            continue
        brands = list(dict.fromkeys(o["brand_name"] for o in occ if o.get("brand_name")))
        name = occ[0]["ingredient_name"]
        findings.append(
            {
                "finding_code": "DUP-ING",
                "category": "DUPLICATE_INGREDIENT",
                "severity": "MODERATE",
                "title": f"Duplicate active ingredient: {name}",
                "description": (
                    f"{name} appears in {len(distinct_items)} selected products "
                    f"({', '.join(brands)}). This identifies a potential issue requiring "
                    "professional review; it does not automatically mean an overdose."
                ),
                "affected_product_ids": [p for p in product_ids if p],
                "affected_ingredient_ids": [iid],
                "affected_brand_names": brands,
                "evidence_status": "DEMO_ONLY",
                "source_reference": "Built-in duplicate detection (deterministic)",
                "rule_id": "RULE-DUP-001",
                "rule_version": "demo-rules-v1",
                "is_synthetic": True,
                "limitations": (
                    "Severity is configured for demonstration. Does not assess clinical harm."
                ),
                "recommended_next_step": (
                    "Ask a doctor or pharmacist whether both products are intentional."
                ),
                "evaluation_status": "EVALUATED",
            }
        )
    return findings
