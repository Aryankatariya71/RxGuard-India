"""Labeled synthetic demo scenarios for the UI."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.schemas.dtos import review_to_dict
from backend.app.models.entities import Prescription, PrescriptionItem, Product
from backend.app.services.ingredient_resolution import normalize_brand
from backend.app.services.review_engine import evaluate_prescription


def _ref() -> str:
    return f"DEMO-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:5].upper()}"


def _product(db: Session, brand: str) -> Product | None:
    return db.scalars(
        select(Product).where(Product.normalized_name == normalize_brand(brand))
    ).first()


def build_scenario(db: Session, scenario_id: str) -> dict:
    specs = {
        "duplicate": {
            "title": "DEMO: Duplicate ingredient example",
            "age_years": 40,
            "items": [
                {"brand": "Demo Product Alpha", "dose": 500, "unit": "mg", "freq": 2},
                {"brand": "Demo Product Beta", "dose": 325, "unit": "mg", "freq": 2},
            ],
        },
        "interaction": {
            "title": "DEMO: Synthetic interaction example",
            "age_years": 55,
            "items": [
                {"brand": "Demo Combo Gamma", "dose": 1, "unit": "tablet", "freq": 1},
                {"brand": "Demo Product Delta", "dose": 75, "unit": "mg", "freq": 1},
            ],
        },
        "missing_dose": {
            "title": "DEMO: Missing dosage information",
            "age_years": 35,
            "items": [
                {"brand": "Demo Product Alpha", "dose": None, "unit": None, "freq": None},
            ],
        },
        "unresolved": {
            "title": "DEMO: Unresolved brand example",
            "age_years": 30,
            "items": [
                {
                    "brand": "DEMO-Unknown-XYZ-999",
                    "dose": 1,
                    "unit": "tablet",
                    "freq": 1,
                    "force_unresolved": True,
                },
                {"brand": "Demo Product Alpha", "dose": 500, "unit": "mg", "freq": 1},
            ],
        },
        "combination": {
            "title": "DEMO: Combination product example",
            "age_years": 28,
            "items": [
                {"brand": "Demo Combo Gamma", "dose": 1, "unit": "tablet", "freq": 2},
                {"brand": "Demo Product Alpha", "dose": 500, "unit": "mg", "freq": 2},
            ],
        },
    }
    if scenario_id not in specs:
        raise KeyError(f"Unknown scenario: {scenario_id}")
    spec = specs[scenario_id]

    rx = Prescription(
        review_reference=_ref(),
        title=spec["title"],
        patient_reference="DEMO-PATIENT",
        age_years=spec["age_years"],
        context_json=json.dumps({"demo_scenario": scenario_id, "synthetic": True}),
        status="draft",
        is_demo=True,
    )
    db.add(rx)
    db.flush()

    for it in spec["items"]:
        force = it.get("force_unresolved")
        p = None if force else _product(db, it["brand"])
        item = PrescriptionItem(
            prescription_id=rx.id,
            product_id=None if force else (p.id if p else None),
            entered_name=it["brand"],
            entered_brand_name=it["brand"],
            dose_amount=it.get("dose"),
            dose_unit=it.get("unit"),
            frequency_value=it.get("freq"),
            frequency_unit="per_day",
            identity_status="UNRESOLVED" if force or not p else "VERIFIED_CATALOGUE_MATCH",
            resolution_status="unresolved" if force or not p else "resolved",
            resolution_method=None if force or not p else "catalogue_id",
        )
        db.add(item)
    db.commit()

    report = evaluate_prescription(db, rx.id)
    return {
        "scenario_id": scenario_id,
        "label": "Synthetic demonstration — not medical guidance",
        "review": review_to_dict(db.get(Prescription, rx.id), include_items=True),
        "report": report,
    }
