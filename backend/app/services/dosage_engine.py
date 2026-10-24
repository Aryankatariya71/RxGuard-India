"""Configurable dosage concern detection — synthetic ranges only for demo."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.entities import DosageRule

# Explicit conversion table (safe subset only)
TO_MG = {"mg": 1.0, "g": 1000.0, "mcg": 0.001}


def to_mg(amount: float, unit: str | None) -> float | None:
    if unit is None:
        return None
    u = unit.strip().lower()
    if u not in TO_MG:
        return None
    return float(amount) * TO_MG[u]


def evaluate_dosage(
    db: Session,
    resolved_items: list[dict[str, Any]],
    *,
    age_years: float | None,
    rule_set_version: str,
) -> list[dict[str, Any]]:
    rules = list(
        db.scalars(select(DosageRule).where(DosageRule.active.is_(True))).all()
    )
    rules_by_ing: dict[str, list[DosageRule]] = {}
    for r in rules:
        rules_by_ing.setdefault(r.ingredient_id, []).append(r)

    findings: list[dict[str, Any]] = []

    for item in resolved_items:
        if item.get("resolution_status") != "resolved":
            continue
        brand = item.get("brand_name")
        product_id = item.get("product_id")
        dose_amount = item.get("dose_amount")
        dose_unit = item.get("dose_unit")
        freq = item.get("frequency_value")

        for ing in item.get("ingredients") or []:
            iid = ing["id"]
            applicable = rules_by_ing.get(iid) or []
            if not applicable:
                findings.append(
                    {
                        "finding_code": "DOSE-NO-RULE",
                        "category": "NO_RULE_MATCHED",
                        "severity": "INFORMATIONAL",
                        "title": f"Dosage not evaluated: {ing['name']}",
                        "description": (
                            "Dosage not evaluated: no applicable configured rule is available "
                            f"for {ing['name']}."
                        ),
                        "affected_product_ids": [product_id] if product_id else [],
                        "affected_ingredient_ids": [iid],
                        "affected_brand_names": [brand] if brand else [],
                        "evidence_status": "NOT_EVALUATED",
                        "source_reference": None,
                        "rule_id": None,
                        "rule_version": rule_set_version,
                        "is_synthetic": True,
                        "limitations": "Absence of a rule does not mean dosage is appropriate.",
                        "recommended_next_step": "Confirm dosing with a clinician or pharmacist.",
                        "evaluation_status": "NOT_EVALUATED",
                    }
                )
                continue

            for rule in applicable:
                # Population gate
                if rule.applicable_population == "adult" and age_years is not None and age_years < 18:
                    continue
                if rule.applicable_population == "pediatric" and (
                    age_years is None or age_years >= 18
                ):
                    if age_years is None:
                        findings.append(_insufficient(item, ing, rule, "Age required for pediatric dosage rule."))
                    continue

                if dose_amount is None or not dose_unit or freq is None:
                    findings.append(
                        _insufficient(
                            item,
                            ing,
                            rule,
                            "Dose amount, unit, and frequency are required to evaluate this rule.",
                        )
                    )
                    continue

                amount_mg = to_mg(float(dose_amount), dose_unit)
                if amount_mg is None:
                    findings.append(
                        {
                            "finding_code": rule.rule_code + "-UNIT",
                            "category": "UNIT_MISMATCH",
                            "severity": "UNKNOWN",
                            "title": f"Unit mismatch: {ing['name']}",
                            "description": (
                                f"Dose unit '{dose_unit}' cannot be safely converted for rule "
                                f"{rule.rule_code}."
                            ),
                            "affected_product_ids": [product_id] if product_id else [],
                            "affected_ingredient_ids": [iid],
                            "affected_brand_names": [brand] if brand else [],
                            "evidence_status": rule.evidence_status,
                            "source_reference": rule.source_reference,
                            "rule_id": rule.rule_code,
                            "rule_version": rule.rule_version,
                            "is_synthetic": bool(rule.is_synthetic),
                            "limitations": "Demonstration rule — not medical guidance.",
                            "recommended_next_step": "Clarify dose units with the prescriber.",
                            "evaluation_status": "INSUFFICIENT_DATA",
                        }
                    )
                    continue

                # Per-administration dose vs configured single-dose range (demo)
                daily = amount_mg * float(freq)
                rule_max = rule.dose_max
                rule_min = rule.dose_min
                # Convert rule limits if in mg
                if rule.dose_unit and rule.dose_unit.lower() != "mg":
                    # only compare when same unit family via TO_MG
                    pass

                if rule_max is not None and daily > float(rule_max):
                    findings.append(
                        {
                            "finding_code": rule.rule_code,
                            "category": "DOSE_OUTSIDE_CONFIGURED_RANGE",
                            "severity": rule.severity,
                            "title": f"Configured dose range exceeded: {ing['name']}",
                            "description": (
                                f"Entered regimen totals approximately {daily:g} mg/day versus "
                                f"demonstration max {rule_max:g} {rule.dose_unit or 'mg'}/day "
                                f"(rule {rule.rule_code}). Demonstration rule — not medical guidance."
                            ),
                            "affected_product_ids": [product_id] if product_id else [],
                            "affected_ingredient_ids": [iid],
                            "affected_brand_names": [brand] if brand else [],
                            "evidence_status": rule.evidence_status,
                            "source_reference": rule.source_reference,
                            "rule_id": rule.rule_code,
                            "rule_version": rule.rule_version,
                            "is_synthetic": True,
                            "limitations": "Synthetic range for hackathon demo only.",
                            "recommended_next_step": (
                                "Discuss the regimen with a qualified doctor or pharmacist."
                            ),
                            "evaluation_status": "EVALUATED",
                        }
                    )
                elif rule_min is not None and daily < float(rule_min):
                    findings.append(
                        {
                            "finding_code": rule.rule_code + "-LOW",
                            "category": "DOSE_OUTSIDE_CONFIGURED_RANGE",
                            "severity": "LOW",
                            "title": f"Below configured demo range: {ing['name']}",
                            "description": (
                                f"Entered total {daily:g} mg/day is below demonstration minimum "
                                f"{rule_min:g}. This is not a treatment recommendation."
                            ),
                            "affected_product_ids": [product_id] if product_id else [],
                            "affected_ingredient_ids": [iid],
                            "affected_brand_names": [brand] if brand else [],
                            "evidence_status": rule.evidence_status,
                            "source_reference": rule.source_reference,
                            "rule_id": rule.rule_code,
                            "rule_version": rule.rule_version,
                            "is_synthetic": True,
                            "limitations": "Synthetic range for hackathon demo only.",
                            "recommended_next_step": "Confirm intended dosing with a clinician.",
                            "evaluation_status": "EVALUATED",
                        }
                    )

                if rule.frequency_max is not None and float(freq) > float(rule.frequency_max):
                    findings.append(
                        {
                            "finding_code": rule.rule_code + "-FREQ",
                            "category": "FREQUENCY_OUTSIDE_CONFIGURED_RANGE",
                            "severity": rule.severity,
                            "title": f"Frequency outside configured range: {ing['name']}",
                            "description": (
                                f"Frequency {freq}/day exceeds demonstration max "
                                f"{rule.frequency_max}/day."
                            ),
                            "affected_product_ids": [product_id] if product_id else [],
                            "affected_ingredient_ids": [iid],
                            "affected_brand_names": [brand] if brand else [],
                            "evidence_status": rule.evidence_status,
                            "source_reference": rule.source_reference,
                            "rule_id": rule.rule_code,
                            "rule_version": rule.rule_version,
                            "is_synthetic": True,
                            "limitations": "Demonstration rule — not medical guidance.",
                            "recommended_next_step": "Confirm frequency with a clinician.",
                            "evaluation_status": "EVALUATED",
                        }
                    )

    return findings


def _insufficient(item: dict, ing: dict, rule: DosageRule, reason: str) -> dict:
    return {
        "finding_code": rule.rule_code + "-MISS",
        "category": "INSUFFICIENT_DOSAGE_INFORMATION",
        "severity": "INFORMATIONAL",
        "title": f"Insufficient dosage information: {ing['name']}",
        "description": reason,
        "affected_product_ids": [item.get("product_id")] if item.get("product_id") else [],
        "affected_ingredient_ids": [ing["id"]],
        "affected_brand_names": [item.get("brand_name")] if item.get("brand_name") else [],
        "evidence_status": "NOT_EVALUATED",
        "source_reference": rule.source_reference,
        "rule_id": rule.rule_code,
        "rule_version": rule.rule_version,
        "is_synthetic": True,
        "limitations": "Required inputs missing; check not completed.",
        "recommended_next_step": "Provide dose, unit, and frequency to evaluate this demo rule.",
        "evaluation_status": "INSUFFICIENT_DATA",
    }
