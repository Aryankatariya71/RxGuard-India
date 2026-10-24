"""Deterministic drug–drug interaction rule engine."""

from __future__ import annotations

from itertools import combinations
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.entities import InteractionRule


def pair_key(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b)))  # type: ignore[return-value]


def evaluate_interactions(
    db: Session,
    resolved_items: list[dict[str, Any]],
    rule_set_version: str,
) -> list[dict[str, Any]]:
    # Map ingredient -> products carrying it
    ing_to_products: dict[str, list[dict]] = {}
    ing_names: dict[str, str] = {}
    for item in resolved_items:
        if item.get("resolution_status") != "resolved":
            continue
        for ing in item.get("ingredients") or []:
            iid = ing["id"]
            ing_names[iid] = ing["name"]
            ing_to_products.setdefault(iid, []).append(
                {
                    "product_id": item.get("product_id"),
                    "brand_name": item.get("brand_name"),
                }
            )

    ids = sorted(ing_to_products.keys())
    if len(ids) < 2:
        return []

    rules = list(
        db.scalars(
            select(InteractionRule).where(
                InteractionRule.active.is_(True),
                InteractionRule.version == rule_set_version,
            )
        ).all()
    )
    # Also accept any active rules if version filter empty / mismatched seed version
    if not rules:
        rules = list(db.scalars(select(InteractionRule).where(InteractionRule.active.is_(True))).all())

    rule_index: dict[tuple[str, str], InteractionRule] = {}
    for r in rules:
        rule_index[pair_key(r.ingredient_a_id, r.ingredient_b_id)] = r

    findings: list[dict[str, Any]] = []
    seen_rules: set[str] = set()

    for a, b in combinations(ids, 2):
        key = pair_key(a, b)
        rule = rule_index.get(key)
        if not rule:
            continue
        if rule.rule_code in seen_rules:
            continue
        seen_rules.add(rule.rule_code)

        brands = []
        product_ids = []
        for src in (a, b):
            for p in ing_to_products.get(src, []):
                if p.get("brand_name") and p["brand_name"] not in brands:
                    brands.append(p["brand_name"])
                if p.get("product_id") and p["product_id"] not in product_ids:
                    product_ids.append(p["product_id"])

        findings.append(
            {
                "finding_code": rule.rule_code,
                "category": "DRUG_DRUG_INTERACTION",
                "severity": rule.severity,
                "title": rule.title,
                "description": rule.explanation,
                "affected_product_ids": product_ids,
                "affected_ingredient_ids": [a, b],
                "affected_brand_names": brands,
                "evidence_status": rule.evidence_status,
                "source_reference": rule.source_reference or rule.source_name,
                "rule_id": rule.rule_code,
                "rule_version": rule.rule_version,
                "is_synthetic": bool(rule.is_synthetic),
                "limitations": (
                    "Demonstration rule — not medical guidance."
                    if rule.is_synthetic
                    else "Rule-based check only; does not replace clinical judgment."
                ),
                "recommended_next_step": rule.recommended_action,
                "evaluation_status": "EVALUATED",
            }
        )
    return findings
