"""Persist external (RxNorm / catalogue) records into local products table."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.entities import Ingredient, Product, ProductIngredient
from backend.app.services.ingredient_resolution import normalize_brand


def upsert_external_product(db: Session, record: dict) -> Product:
    """
    Idempotent upsert keyed by (source, source_record_id).
    Never invents missing clinical fields.
    """
    source = record.get("source") or "unknown"
    source_id = str(record.get("source_record_id") or "").strip()
    name = (record.get("name") or record.get("brand_name") or "").strip()
    if not name:
        raise ValueError("Product name required")

    existing = None
    if source_id:
        existing = db.scalars(
            select(Product).where(
                Product.source == source,
                Product.source_record_id == source_id,
            )
        ).first()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    verification = record.get("verification_status") or "SOURCE_BACKED"
    if record.get("is_synthetic"):
        verification = "DEMO_ONLY"

    if existing:
        p = existing
        p.brand_name = name
        p.normalized_name = normalize_brand(name)
        p.strength_label = record.get("strength_label")
        p.dosage_form = record.get("dosage_form")
        p.source_url = record.get("source_url")
        p.retrieved_at = now
        p.verification_status = verification
        p.geographic_applicability = record.get("geographic_applicability")
        p.is_synthetic = bool(record.get("is_synthetic"))
        p.identity_status = "VERIFIED_CATALOGUE_MATCH"
        p.updated_at = now
    else:
        kwargs: dict = {
            "brand_name": name,
            "normalized_name": normalize_brand(name),
            "strength_label": record.get("strength_label"),
            "dosage_form": record.get("dosage_form"),
            "identity_status": "VERIFIED_CATALOGUE_MATCH",
            "source": source,
            "source_record_id": source_id or None,
            "source_url": record.get("source_url"),
            "source_version": record.get("source_version"),
            "retrieved_at": now,
            "verification_status": verification,
            "geographic_applicability": record.get("geographic_applicability"),
            "is_synthetic": bool(record.get("is_synthetic")),
        }
        if source_id:
            kwargs["id"] = f"ext-{source_id}"
        p = Product(**kwargs)
        db.add(p)
        db.flush()

    for ing in record.get("ingredients") or []:
        cname = (ing.get("canonical_name") or ing.get("name") or "").strip()
        if not cname:
            continue
        nname = normalize_brand(cname)
        ingredient = db.scalars(
            select(Ingredient).where(Ingredient.normalized_name == nname)
        ).first()
        if not ingredient:
            ext_ing_id = ing.get("rxcui") or ing.get("id")
            ing_kwargs: dict = {
                "canonical_name": cname,
                "normalized_name": nname,
                "standard_identifier": str(ext_ing_id) if ext_ing_id else None,
                "status": "REVIEW_PENDING",
                "source": source,
                "dataset_version": "rxnorm-live",
                "is_synthetic": False,
            }
            if ext_ing_id:
                ing_kwargs["id"] = f"rxn-{ext_ing_id}"
            ingredient = Ingredient(**ing_kwargs)
            db.add(ingredient)
            db.flush()

        link = db.scalars(
            select(ProductIngredient).where(
                ProductIngredient.product_id == p.id,
                ProductIngredient.ingredient_id == ingredient.id,
            )
        ).first()
        if not link:
            db.add(
                ProductIngredient(
                    product_id=p.id,
                    ingredient_id=ingredient.id,
                    strength_value=ing.get("strength_value"),
                    strength_unit=ing.get("strength_unit"),
                    source=source,
                    incomplete_flag=False,
                    active_flag=True,
                )
            )

    db.commit()
    db.refresh(p)
    return p
