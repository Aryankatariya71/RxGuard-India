from __future__ import annotations

import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from backend.app.api.schemas.dtos import (
    ItemCreate,
    ItemUpdate,
    ReviewCreate,
    ReviewUpdate,
    item_to_dict,
    review_to_dict,
)
from backend.app.core.config import get_settings
from backend.app.core.constants import SAFETY_DISCLAIMER
from backend.app.db.session import get_db
from backend.app.models.entities import (
    AuditEvent,
    DosageRule,
    InteractionRule,
    Prescription,
    PrescriptionItem,
    Product,
    ProductIngredient,
    ReviewFinding,
)
from backend.app.services.ingredient_resolution import resolve_product_exact
from backend.app.services.review_engine import build_report, evaluate_prescription

router = APIRouter(tags=["reviews"])


def _ref() -> str:
    return f"RXG-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


def _audit(db: Session, event_type: str, resource_type: str, resource_id: str, meta: dict | None = None):
    db.add(
        AuditEvent(
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            minimal_metadata_json=json.dumps(meta or {}),
        )
    )


@router.post("/reviews")
def create_review(body: ReviewCreate, db: Session = Depends(get_db)):
    ctx = dict(body.context or {})
    if body.age_group:
        ctx.setdefault("age_group", body.age_group)
    rx = Prescription(
        review_reference=_ref(),
        title=body.title,
        patient_reference=body.patient_reference,
        age_years=body.age_years,
        context_json=json.dumps(ctx),
        status="draft",
        is_demo=True,
    )
    db.add(rx)
    db.flush()
    _audit(db, "review_created", "prescription", rx.id)
    db.commit()
    db.refresh(rx)
    return review_to_dict(rx, include_items=True)


@router.get("/reviews")
def list_reviews(
    q: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(Prescription).options(
        joinedload(Prescription.items), joinedload(Prescription.findings)
    )
    count_stmt = select(func.count(Prescription.id))
    if q:
        like = f"%{q.strip()}%"
        filt = or_(
            Prescription.review_reference.ilike(like),
            Prescription.title.ilike(like),
            Prescription.patient_reference.ilike(like),
        )
        stmt = stmt.where(filt)
        count_stmt = count_stmt.where(filt)
    if status:
        stmt = stmt.where(Prescription.status == status)
        count_stmt = count_stmt.where(Prescription.status == status)
    total = db.scalar(count_stmt) or 0
    rows = list(
        db.scalars(
            stmt.order_by(Prescription.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .unique()
        .all()
    )
    return {
        "items": [review_to_dict(r) for r in rows],
        "total": int(total),
        "page": page,
        "page_size": page_size,
    }


@router.get("/reviews/{review_id}")
def get_review(review_id: str, db: Session = Depends(get_db)):
    rx = db.scalars(
        select(Prescription)
        .options(joinedload(Prescription.items).joinedload(PrescriptionItem.product))
        .where(Prescription.id == review_id)
    ).unique().first()
    if not rx:
        raise HTTPException(404, "Review not found")
    return review_to_dict(rx, include_items=True)


@router.patch("/reviews/{review_id}")
def update_review(review_id: str, body: ReviewUpdate, db: Session = Depends(get_db)):
    rx = db.get(Prescription, review_id)
    if not rx:
        raise HTTPException(404, "Review not found")
    data = body.model_dump(exclude_unset=True)
    if "context" in data or "age_group" in data:
        ctx = json.loads(rx.context_json or "{}")
        if "context" in data:
            ctx.update(data.pop("context") or {})
        if "age_group" in data:
            ctx["age_group"] = data.pop("age_group")
        rx.context_json = json.dumps(ctx)
    data.pop("age_group", None)
    for k, v in data.items():
        setattr(rx, k, v)
    db.commit()
    db.refresh(rx)
    return review_to_dict(rx, include_items=True)


@router.delete("/reviews/{review_id}")
def delete_review(review_id: str, db: Session = Depends(get_db)):
    rx = db.get(Prescription, review_id)
    if not rx:
        raise HTTPException(404, "Review not found")
    _audit(db, "review_deleted", "prescription", rx.id)
    db.delete(rx)
    db.commit()
    return {"ok": True}


@router.post("/reviews/{review_id}/items")
def add_item(review_id: str, body: ItemCreate, db: Session = Depends(get_db)):
    rx = db.get(Prescription, review_id)
    if not rx:
        raise HTTPException(404, "Review not found")

    product_id = body.product_id
    resolution_status = "unresolved"
    resolution_method = None

    identity_status = "UNRESOLVED"
    if product_id:
        p = db.get(Product, product_id)
        if not p:
            raise HTTPException(400, "Unknown product_id")
        resolution_status = "resolved"
        resolution_method = "catalogue_id"
        brand = p.brand_name
        identity_status = "USER_CONFIRMED_MATCH"
    else:
        result = resolve_product_exact(db, body.entered_brand_name, body.entered_strength)
        brand = body.entered_brand_name
        if result["status"] == "resolved":
            product_id = result["product"].id
            resolution_status = "resolved"
            resolution_method = result["method"]
            identity_status = "VERIFIED_CATALOGUE_MATCH"
        elif result["status"] == "ambiguous":
            resolution_status = "ambiguous"
            identity_status = "AMBIGUOUS"
        else:
            resolution_status = "unresolved"
            identity_status = "UNRESOLVED"

    item = PrescriptionItem(
        prescription_id=rx.id,
        product_id=product_id,
        entered_name=brand,
        entered_brand_name=brand,
        entered_strength=body.entered_strength,
        dose_amount=body.dose_amount,
        dose_unit=body.dose_unit,
        frequency_value=body.frequency_value,
        frequency_unit=body.frequency_unit,
        route=body.route,
        duration_value=body.duration_value,
        duration_unit=body.duration_unit,
        instructions=body.instructions,
        identity_status=identity_status,
        resolution_status=resolution_status,
        resolution_method=resolution_method,
    )
    db.add(item)
    rx.status = "draft"
    db.commit()
    db.refresh(item)
    # reload with product
    item = db.scalars(
        select(PrescriptionItem)
        .options(
            joinedload(PrescriptionItem.product)
            .joinedload(Product.ingredients)
            .joinedload(ProductIngredient.ingredient)
        )
        .where(PrescriptionItem.id == item.id)
    ).unique().first()
    out = item_to_dict(item)
    if resolution_status != "resolved":
        result = resolve_product_exact(db, body.entered_brand_name, body.entered_strength)
        from backend.app.api.schemas.dtos import product_to_dict

        out["candidates"] = [product_to_dict(c) for c in (result.get("candidates") or [])]
        out["suggestions_only"] = bool(result.get("suggestions_only"))
    return out


@router.patch("/reviews/{review_id}/items/{item_id}")
def update_item(
    review_id: str, item_id: str, body: ItemUpdate, db: Session = Depends(get_db)
):
    item = db.get(PrescriptionItem, item_id)
    if not item or item.prescription_id != review_id:
        raise HTTPException(404, "Item not found")
    data = body.model_dump(exclude_unset=True)
    if "product_id" in data and data["product_id"]:
        p = db.get(Product, data["product_id"])
        if not p:
            raise HTTPException(400, "Unknown product_id")
        item.product_id = p.id
        item.entered_name = p.brand_name
        item.entered_brand_name = p.brand_name
        item.resolution_status = "resolved"
        item.resolution_method = "user_confirmed"
        item.identity_status = "USER_CONFIRMED_MATCH"
        data.pop("product_id", None)
    for k, v in data.items():
        setattr(item, k, v)
        if k == "entered_brand_name" and v:
            item.entered_name = v
    db.commit()
    item = db.scalars(
        select(PrescriptionItem)
        .options(
            joinedload(PrescriptionItem.product)
            .joinedload(Product.ingredients)
            .joinedload(ProductIngredient.ingredient)
        )
        .where(PrescriptionItem.id == item_id)
    ).unique().first()
    return item_to_dict(item)


@router.delete("/reviews/{review_id}/items/{item_id}")
def delete_item(review_id: str, item_id: str, db: Session = Depends(get_db)):
    item = db.get(PrescriptionItem, item_id)
    if not item or item.prescription_id != review_id:
        raise HTTPException(404, "Item not found")
    db.delete(item)
    db.commit()
    return {"ok": True}


@router.post("/reviews/{review_id}/evaluate")
def evaluate(review_id: str, db: Session = Depends(get_db)):
    if not db.get(Prescription, review_id):
        raise HTTPException(404, "Review not found")
    try:
        report = evaluate_prescription(db, review_id)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    _audit(db, "review_evaluated", "prescription", review_id)
    db.commit()
    return report


@router.get("/reviews/{review_id}/report")
def report(review_id: str, db: Session = Depends(get_db)):
    if not db.get(Prescription, review_id):
        raise HTTPException(404, "Review not found")
    try:
        return build_report(db, review_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@router.get("/reviews/{review_id}/export")
def export_report(
    review_id: str,
    format: str = Query("txt", pattern="^(txt|csv)$"),
    db: Session = Depends(get_db),
):
    if not db.get(Prescription, review_id):
        raise HTTPException(404, "Review not found")
    report = build_report(db, review_id)
    rx = report["review"]
    if format == "csv":
        lines = ["severity,category,title,evidence_status,is_synthetic,rule_id"]
        for f in report["findings"]:
            lines.append(
                ",".join(
                    [
                        f['severity'],
                        f['category'],
                        '"' + f['title'].replace('"', "'") + '"',
                        f['evidence_status'],
                        str(f['is_synthetic']),
                        f.get("rule_id") or "",
                    ]
                )
            )
        lines.append("")
        lines.append(f'"DISCLAIMER","{SAFETY_DISCLAIMER.replace(chr(34), chr(39))}"')
        content = "\n".join(lines)
        return Response(
            content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="rxguard-{rx["review_reference"]}.csv"'
            },
        )

    lines = [
        "RxGuard India — Prescription Review Report",
        f"Reference: {rx['review_reference']}",
        f"Generated: {datetime.utcnow().isoformat()}Z",
        f"Catalogue: {rx.get('catalogue_version')}",
        f"Rule set: {rx.get('rule_set_version')}",
        "",
        "Medicines:",
    ]
    for it in report["items"]:
        lines.append(
            f"- {it['entered_brand_name']} [{it['resolution_status']}] "
            f"dose={it.get('dose_amount')} {it.get('dose_unit')} freq={it.get('frequency_value')}"
        )
    lines.append("")
    lines.append("Findings:")
    for f in report["findings"]:
        syn = " [DEMO]" if f.get("is_synthetic") else ""
        lines.append(f"- [{f['severity']}]{syn} {f['title']}")
        lines.append(f"  {f['description']}")
        lines.append(f"  Evidence: {f['evidence_status']} | Rule: {f.get('rule_id')}")
    lines.append("")
    lines.append("DISCLAIMER")
    lines.append(SAFETY_DISCLAIMER)
    content = "\n".join(lines)
    return Response(
        content,
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="rxguard-{rx["review_reference"]}.txt"'
        },
    )


@router.get("/rules/status")
def rules_status(db: Session = Depends(get_db)):
    settings = get_settings()
    ints = list(db.scalars(select(InteractionRule)).all())
    doses = list(db.scalars(select(DosageRule)).all())
    return {
        "rule_set_version": settings.rule_set_version,
        "active_interaction_rules": sum(1 for r in ints if r.active),
        "active_dosage_rules": sum(1 for r in doses if r.active),
        "synthetic_rule_count": sum(1 for r in ints + doses if r.is_synthetic),
        "reviewed_rule_count": sum(
            1 for r in ints + doses if r.status == "CLINICALLY_REVIEWED"
        ),
        "demo_illustrative_count": sum(
            1 for r in ints + doses if r.status == "DEMO_ILLUSTRATIVE"
        ),
        "review_pending_count": sum(
            1 for r in ints + doses if r.status == "REVIEW_PENDING"
        ),
        "unsupported_categories": ["allergy", "pregnancy", "renal_function"],
        "demo_mode": settings.demo_mode,
    }


@router.get("/data/status")
def data_status(db: Session = Depends(get_db)):
    settings = get_settings()
    products = list(db.scalars(select(Product)).all())
    return {
        "catalogue_version": settings.catalogue_version,
        "synthetic_product_count": sum(1 for p in products if p.is_synthetic),
        "source_backed_product_count": sum(1 for p in products if not p.is_synthetic),
        "unverified_product_count": sum(
            1 for p in products if not p.is_synthetic and p.source
        ),
        "total_products": len(products),
        "demo_data_mode": settings.demo_data_mode,
        "demo_mode": settings.demo_mode,
        "last_data_update": "seed_demo_data",
    }


@router.post("/demo/scenarios/{scenario_id}")
def load_demo_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """Create a review preloaded with a labeled synthetic scenario."""
    from backend.app.services.demo_scenarios import build_scenario

    try:
        return build_scenario(db, scenario_id)
    except KeyError as e:
        raise HTTPException(404, str(e)) from e
