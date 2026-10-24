"""Pydantic schemas and serializers."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from backend.app.models.entities import (
    Ingredient,
    Prescription,
    PrescriptionItem,
    Product,
    ReviewFinding,
)


class ReviewCreate(BaseModel):
    title: str | None = None
    patient_reference: str | None = None
    age_years: float | None = Field(None, ge=0, le=120)
    age_group: str | None = None
    context: dict[str, Any] | None = None


class ReviewUpdate(BaseModel):
    title: str | None = None
    patient_reference: str | None = None
    age_years: float | None = Field(None, ge=0, le=120)
    age_group: str | None = None
    context: dict[str, Any] | None = None


class ItemCreate(BaseModel):
    product_id: str | None = None
    entered_brand_name: str
    entered_strength: str | None = None
    dose_amount: float | None = None
    dose_unit: str | None = None
    frequency_value: float | None = None
    frequency_unit: str | None = "per_day"
    route: str | None = None
    duration_value: float | None = None
    duration_unit: str | None = None
    instructions: str | None = None


class ItemUpdate(BaseModel):
    product_id: str | None = None
    entered_brand_name: str | None = None
    entered_strength: str | None = None
    dose_amount: float | None = None
    dose_unit: str | None = None
    frequency_value: float | None = None
    frequency_unit: str | None = None
    route: str | None = None
    duration_value: float | None = None
    duration_unit: str | None = None
    instructions: str | None = None


def ingredient_to_dict(ing: Ingredient) -> dict:
    return {
        "id": ing.id,
        "canonical_name": ing.canonical_name,
        "normalized_name": ing.normalized_name,
        "standard_identifier": ing.standard_identifier,
        "verification_status": ing.status,
        "status": ing.status,
        "is_synthetic": ing.is_synthetic,
        "source_reference": ing.source,
        "source": ing.source,
        "dataset_version": ing.dataset_version,
    }


def product_to_dict(p: Product) -> dict:
    ings = []
    for pi in p.ingredients or []:
        if not pi.ingredient:
            continue
        ings.append(
            {
                **ingredient_to_dict(pi.ingredient),
                "ingredient_strength": pi.strength_value,
                "strength_value": pi.strength_value,
                "strength_unit": pi.strength_unit,
                "incomplete_flag": pi.incomplete_flag,
            }
        )
    return {
        "id": p.id,
        "brand_name": p.brand_name,
        "normalized_name": p.normalized_name,
        "generic_display_name": p.strength_label,
        "strength": p.strength_label,
        "strength_label": p.strength_label,
        "dosage_form": p.dosage_form,
        "route": p.route,
        "manufacturer": p.manufacturer,
        "identity_status": p.identity_status,
        "catalogue_status": "synthetic" if p.is_synthetic else "catalogue",
        "source_name": p.source,
        "source": p.source,
        "source_reference": p.source,
        "source_url": p.source_url,
        "source_record_id": p.source_record_id,
        "source_verified_at": None,
        "source_date": p.source_date,
        "source_version": p.source_version,
        "retrieved_at": p.retrieved_at.isoformat() if p.retrieved_at else None,
        "verification_status": p.verification_status
        or ("DEMO_ONLY" if p.is_synthetic else "UNRESOLVED"),
        "geographic_applicability": p.geographic_applicability,
        "data_version": p.source_version,
        "is_discontinued": p.is_discontinued,
        "is_synthetic": p.is_synthetic,
        "price": p.price,
        "price_as_of": p.price_as_of,
        "ingredients": ings,
    }


def item_to_dict(item: PrescriptionItem) -> dict:
    product = product_to_dict(item.product) if item.product else None
    entered = item.entered_name or item.entered_brand_name
    return {
        "id": item.id,
        "product_id": item.product_id,
        "entered_brand_name": entered,
        "entered_name": entered,
        "entered_strength": item.entered_strength,
        "dose_amount": item.dose_amount,
        "dose_unit": item.dose_unit,
        "frequency_value": item.frequency_value,
        "frequency_unit": item.frequency_unit,
        "frequency_original_text": item.frequency_original_text,
        "frequency_structured": json.loads(item.frequency_structured_json)
        if item.frequency_structured_json
        else None,
        "route": item.route,
        "duration_value": item.duration_value,
        "duration_unit": item.duration_unit,
        "duration": item.duration,
        "instructions": item.instructions or item.notes,
        "identity_status": item.identity_status,
        "resolution_status": item.resolution_status,
        "resolution_method": item.resolution_method,
        "product": product,
    }


def finding_to_dict(f: ReviewFinding) -> dict:
    return {
        "id": f.id,
        "finding_code": f.finding_code,
        "category": f.category,
        "severity": f.severity,
        "title": f.title,
        "description": f.description,
        "affected_product_ids": json.loads(f.affected_product_ids_json or "[]"),
        "affected_ingredient_ids": json.loads(f.affected_ingredient_ids_json or "[]"),
        "affected_brand_names": json.loads(f.affected_brand_names_json or "[]"),
        "evidence_status": f.evidence_status,
        "source_reference": f.source_reference,
        "rule_id": f.rule_id,
        "rule_version": f.rule_version,
        "is_synthetic": f.is_synthetic,
        "limitations": f.limitations,
        "recommended_next_step": f.recommended_next_step,
        "evaluation_status": f.evaluation_status,
        "why_trace": json.loads(f.why_trace_json) if f.why_trace_json else None,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }


def review_to_dict(rx: Prescription, include_items: bool = False) -> dict:
    out = {
        "id": rx.id,
        "review_reference": rx.review_reference,
        "title": rx.title,
        "patient_reference": rx.patient_reference,
        "age_years": rx.age_years,
        "weight_kg": rx.weight_kg,
        "is_demo": rx.is_demo,
        "status": rx.status,
        "catalogue_version": rx.catalogue_version,
        "rule_set_version": rx.rule_set_version,
        "created_at": rx.created_at.isoformat() if rx.created_at else None,
        "updated_at": rx.updated_at.isoformat() if rx.updated_at else None,
        "context": json.loads(rx.context_json) if rx.context_json else None,
    }
    if include_items:
        out["items"] = [item_to_dict(i) for i in (rx.items or [])]
    return out
