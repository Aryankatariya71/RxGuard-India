"""Central evaluate_prescription service."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.app.core.config import get_settings
from backend.app.core.constants import SAFETY_DISCLAIMER
from backend.app.models.entities import (
    Prescription,
    PrescriptionItem,
    Product,
    ProductIngredient,
    ReviewFinding,
)
from backend.app.services.dosage_engine import evaluate_dosage
from backend.app.services.duplicate_detector import detect_duplicates
from backend.app.services.interaction_engine import evaluate_interactions
from backend.app.services.search_service import feeds_ingredient_checks


def _load_items(db: Session, prescription_id: str) -> list[PrescriptionItem]:
    stmt = (
        select(PrescriptionItem)
        .options(
            joinedload(PrescriptionItem.product)
            .joinedload(Product.ingredients)
            .joinedload(ProductIngredient.ingredient)
        )
        .where(PrescriptionItem.prescription_id == prescription_id)
    )
    return list(db.scalars(stmt).unique().all())


def _item_payload(item: PrescriptionItem) -> dict[str, Any]:
    identity = item.identity_status or (
        "VERIFIED_CATALOGUE_MATCH"
        if item.resolution_status == "resolved"
        else "UNRESOLVED"
    )
    # Only verified / user-confirmed identities feed ingredient-dependent checks
    include_ingredients = feeds_ingredient_checks(identity)
    ings = []
    if include_ingredients and item.product_id and item.product:
        for pi in item.product.ingredients or []:
            ing = pi.ingredient
            if not ing:
                continue
            ings.append({"id": ing.id, "name": ing.canonical_name})
    effective_resolution = "resolved" if include_ingredients else "unresolved"
    return {
        "item_id": item.id,
        "product_id": item.product_id,
        "brand_name": (
            item.product.brand_name
            if item.product
            else (item.entered_name or item.entered_brand_name)
        ),
        "identity_status": identity,
        "resolution_status": effective_resolution,
        "ingredients": ings,
        "dose_amount": item.dose_amount,
        "dose_unit": item.dose_unit,
        "frequency_value": item.frequency_value,
        "frequency_unit": item.frequency_unit,
        "duration_value": item.duration_value,
        "duration_unit": item.duration_unit,
        "route": item.route,
    }


def evaluate_prescription(db: Session, prescription_id: str) -> dict[str, Any]:
    settings = get_settings()
    rx = db.get(Prescription, prescription_id)
    if not rx:
        raise ValueError("Review not found")

    items = _load_items(db, prescription_id)
    payloads = [_item_payload(it) for it in items]
    resolved = [p for p in payloads if p["resolution_status"] == "resolved"]
    unresolved = [p for p in payloads if p["resolution_status"] != "resolved"]

    findings_raw: list[dict[str, Any]] = []
    findings_raw.extend(detect_duplicates(resolved))
    findings_raw.extend(evaluate_interactions(db, resolved, settings.rule_set_version))
    findings_raw.extend(
        evaluate_dosage(
            db,
            resolved,
            age_years=rx.age_years,
            rule_set_version=settings.rule_set_version,
        )
    )

    for u in unresolved:
        findings_raw.append(
            {
                "finding_code": "UNRESOLVED",
                "category": "UNRESOLVED_PRODUCT",
                "severity": "INFORMATIONAL",
                "title": f"Unresolved medicine: {u['brand_name']}",
                "description": (
                    "This product could not be uniquely matched to the catalogue. "
                    "It was not included in definitive ingredient-based checks."
                ),
                "affected_product_ids": [],
                "affected_ingredient_ids": [],
                "affected_brand_names": [u["brand_name"]],
                "evidence_status": "NOT_EVALUATED",
                "source_reference": None,
                "rule_id": None,
                "rule_version": settings.rule_set_version,
                "is_synthetic": True,
                "limitations": "Unresolved products keep uncertainty visible.",
                "recommended_next_step": (
                    "Select the exact catalogue product or confirm with a pharmacist."
                ),
                "evaluation_status": "UNRESOLVED",
            }
        )

    for old in list(rx.findings):
        db.delete(old)
    db.flush()

    for f in findings_raw:
        db.add(
            ReviewFinding(
                prescription_id=rx.id,
                finding_code=f["finding_code"],
                category=f["category"],
                severity=f["severity"],
                title=f["title"],
                description=f["description"],
                affected_product_ids_json=json.dumps(f.get("affected_product_ids") or []),
                affected_ingredient_ids_json=json.dumps(
                    f.get("affected_ingredient_ids") or []
                ),
                affected_brand_names_json=json.dumps(f.get("affected_brand_names") or []),
                evidence_status=f.get("evidence_status") or "DEMO_ONLY",
                source_reference=f.get("source_reference"),
                rule_id=f.get("rule_id"),
                rule_version=f.get("rule_version"),
                is_synthetic=bool(f.get("is_synthetic", True)),
                limitations=f.get("limitations"),
                recommended_next_step=f.get("recommended_next_step"),
                evaluation_status=f.get("evaluation_status") or "EVALUATED",
            )
        )

    n_dup = sum(1 for f in findings_raw if f["category"] == "DUPLICATE_INGREDIENT")
    n_int = sum(1 for f in findings_raw if f["category"] == "DRUG_DRUG_INTERACTION")
    n_dose = sum(
        1
        for f in findings_raw
        if f["category"]
        in {
            "DOSE_OUTSIDE_CONFIGURED_RANGE",
            "FREQUENCY_OUTSIDE_CONFIGURED_RANGE",
            "DURATION_OUTSIDE_CONFIGURED_RANGE",
            "UNIT_MISMATCH",
            "INSUFFICIENT_DOSAGE_INFORMATION",
        }
    )
    n_not = sum(
        1
        for f in findings_raw
        if f.get("evaluation_status")
        in {"NOT_EVALUATED", "INSUFFICIENT_DATA", "UNRESOLVED"}
    )

    issue_findings = [
        f
        for f in findings_raw
        if f["category"]
        in {
            "DUPLICATE_INGREDIENT",
            "DRUG_DRUG_INTERACTION",
            "DOSE_OUTSIDE_CONFIGURED_RANGE",
            "FREQUENCY_OUTSIDE_CONFIGURED_RANGE",
        }
        and f.get("evaluation_status") == "EVALUATED"
    ]

    if unresolved or (n_not > 0 and not issue_findings):
        completeness = "incomplete"
        status_label = "Assessment incomplete"
        status_note = (
            "Unresolved products or missing inputs blocked some checks. "
            "A missing alert does not prove safety."
        )
    elif issue_findings:
        completeness = "issues_identified"
        status_label = "Potential findings"
        status_note = "Review recommended with a qualified clinician or pharmacist."
    else:
        completeness = "no_configured_rule_matched"
        status_label = "No matching rule in this prototype dataset"
        status_note = (
            "No matching rule in this prototype dataset for the resolved medicines. "
            "This is not a clearance and does not mean the prescription has no issues."
        )

    summary = {
        "medicines_entered": len(payloads),
        "resolved_products": len(resolved),
        "unresolved_products": len(unresolved),
        "resolved_ingredient_occurrences": sum(len(p["ingredients"]) for p in resolved),
        "duplicate_findings": n_dup,
        "interaction_findings": n_int,
        "dosage_findings": n_dose,
        "checks_not_evaluated": n_not,
        "total_findings": len(findings_raw),
        "completeness": completeness,
        "status_label": status_label,
        "status_note": status_note,
        "catalogue_version": settings.catalogue_version,
        "rule_set_version": settings.rule_set_version,
        "disclaimer": SAFETY_DISCLAIMER,
    }

    rx.status = "evaluated" if completeness != "incomplete" else "incomplete"
    rx.catalogue_version = settings.catalogue_version
    rx.rule_set_version = settings.rule_set_version
    rx.summary_json = json.dumps(summary)
    db.commit()

    return build_report(db, rx.id)


def build_report(db: Session, prescription_id: str) -> dict[str, Any]:
    from backend.app.api.schemas.dtos import finding_to_dict, item_to_dict

    rx = db.get(Prescription, prescription_id)
    if not rx:
        raise ValueError("Review not found")

    items = _load_items(db, prescription_id)
    findings = list(
        db.scalars(
            select(ReviewFinding)
            .where(ReviewFinding.prescription_id == prescription_id)
            .order_by(ReviewFinding.created_at)
        ).all()
    )
    summary = json.loads(rx.summary_json) if rx.summary_json else {}

    sev_counts: dict[str, int] = {}
    for f in findings:
        sev_counts[f.severity] = sev_counts.get(f.severity, 0) + 1

    return {
        "review": {
            "id": rx.id,
            "review_reference": rx.review_reference,
            "title": rx.title,
            "patient_reference": rx.patient_reference,
            "age_years": rx.age_years,
            "status": rx.status,
            "created_at": rx.created_at.isoformat() if rx.created_at else None,
            "updated_at": rx.updated_at.isoformat() if rx.updated_at else None,
            "catalogue_version": rx.catalogue_version,
            "rule_set_version": rx.rule_set_version,
        },
        "items": [item_to_dict(i) for i in items],
        "findings": [finding_to_dict(f) for f in findings],
        "summary": summary,
        "severity_counts": sev_counts,
        "disclaimer": SAFETY_DISCLAIMER,
    }
