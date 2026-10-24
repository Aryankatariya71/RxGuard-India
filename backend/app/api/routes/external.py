"""Public medicine database routes (RxNorm) + catalogue stats."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from backend.app.api.schemas.dtos import product_to_dict
from backend.app.db.session import get_db
from backend.app.models.entities import Product, ProductIngredient
from backend.app.services.external_catalogue import upsert_external_product
from backend.app.services.rxnorm_adapter import check_rxnorm_connectivity, search_rxnorm
from backend.app.services.search_service import search_medicines

router = APIRouter(tags=["external"])


class ConfirmExternalBody(BaseModel):
    source_record_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    source: str | None = None
    source_url: str | None = None
    dosage_form: str | None = None
    strength_label: str | None = None
    ingredients: list[dict] | None = None
    verification_status: str | None = "SOURCE_BACKED"
    geographic_applicability: str | None = "US_RXNORM"
    tty: str | None = None
    match_type: str | None = None


@router.get("/external/rxnorm/status")
def rxnorm_status():
    return check_rxnorm_connectivity()


@router.get("/external/rxnorm/search")
def rxnorm_search(q: str = Query(..., min_length=1), limit: int = Query(15, ge=1, le=30)):
    try:
        return search_rxnorm(q, max_results=limit)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "RxNorm request failed",
                "error": type(exc).__name__,
            },
        ) from exc


@router.post("/external/rxnorm/confirm")
def rxnorm_confirm(body: ConfirmExternalBody, db: Session = Depends(get_db)):
    """Persist a user-confirmed RxNorm hit into the local catalogue."""
    record = body.model_dump()
    record["source"] = body.source or "RxNorm (NLM RxNav REST API)"
    try:
        product = upsert_external_product(db, record)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    stmt = (
        select(Product)
        .options(joinedload(Product.ingredients).joinedload(ProductIngredient.ingredient))
        .where(Product.id == product.id)
    )
    p = db.scalars(stmt).unique().first()
    data = product_to_dict(p)
    data["verification_status"] = p.verification_status
    data["source_record_id"] = p.source_record_id
    data["source_url"] = p.source_url
    data["geographic_applicability"] = p.geographic_applicability
    data["retrieved_at"] = p.retrieved_at.isoformat() if p.retrieved_at else None
    return data


@router.get("/medicines/search/combined")
def combined_search(
    q: str = Query(..., min_length=1),
    include_rxnorm: bool = True,
    limit: int = Query(20, ge=1, le=40),
    db: Session = Depends(get_db),
):
    """Local catalogue first, optional live RxNorm second."""
    local = search_medicines(db, q, limit=limit)
    for item in local["items"]:
        item["catalogue"] = "local"
        # Map verification for UI labels
        if item.get("is_synthetic"):
            item["verification_status"] = "DEMO_ONLY"
        elif not item.get("verification_status"):
            item["verification_status"] = (
                "SOURCE_BACKED" if item.get("source") else "UNRESOLVED"
            )

    rxnorm = None
    if include_rxnorm:
        try:
            rxnorm = search_rxnorm(q, max_results=limit)
        except Exception as exc:
            rxnorm = {
                "query": q,
                "exact": [],
                "suggestions": [],
                "items": [],
                "errors": [type(exc).__name__],
                "message": "RxNorm unavailable",
            }

    return {
        "query": q,
        "local": local,
        "rxnorm": rxnorm,
        "empty": not local["items"] and not (rxnorm or {}).get("items"),
        "message": (
            None
            if local["items"] or (rxnorm or {}).get("items")
            else "No suitable match was found in the available sources."
        ),
    }


@router.get("/catalogue/stats")
def catalogue_stats(db: Session = Depends(get_db)):
    """Real counts for UI — never fabricate brand totals."""
    total = db.scalar(select(func.count()).select_from(Product)) or 0
    synthetic = (
        db.scalar(select(func.count()).select_from(Product).where(Product.is_synthetic.is_(True)))
        or 0
    )
    source_backed = (
        db.scalar(
            select(func.count())
            .select_from(Product)
            .where(Product.verification_status == "SOURCE_BACKED")
        )
        or 0
    )
    india_catalogue = (
        db.scalar(
            select(func.count())
            .select_from(Product)
            .where(Product.geographic_applicability == "INDIA_CATALOGUE")
        )
        or 0
    )
    # Also count Kaggle-imported rows labeled in source text
    kaggle = (
        db.scalar(
            select(func.count())
            .select_from(Product)
            .where(Product.source.ilike("%A-Z Medicines%"))
        )
        or 0
    )
    return {
        "total_products": int(total),
        "synthetic_products": int(synthetic),
        "source_backed_products": int(source_backed),
        "india_catalogue_products": int(india_catalogue or kaggle),
        "rxnorm_products": int(
            db.scalar(
                select(func.count())
                .select_from(Product)
                .where(Product.geographic_applicability == "US_RXNORM")
            )
            or 0
        ),
        "note": (
            "Counts reflect rows currently in the local database. "
            "RxNorm is US terminology; the India A–Z parquet import is unverified "
            "Kaggle-derived data, not a CDSCO bulk API."
        ),
    }
