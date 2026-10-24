from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.app.api.schemas.dtos import ingredient_to_dict, product_to_dict
from backend.app.db.session import get_db
from backend.app.models.entities import Ingredient, Product, ProductIngredient
from backend.app.services.ingredient_resolution import search_products
from backend.app.services.search_service import search_medicines

router = APIRouter(tags=["medicines"])


@router.get("/medicines/search")
def medicines_search(
    q: str = Query(..., min_length=1, description="Brand or strength query"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Exact normalised matches first; RapidFuzz suggestions second (never auto-selected)."""
    return search_medicines(db, q, limit=limit)


@router.get("/medicines")
def list_medicines(
    q: str | None = None,
    search_by: str = Query("brand", pattern="^(brand|generic|strength)$"),
    dosage_form: str | None = None,
    catalogue_status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    # Prefer Stage-2 search shape when q is provided
    if q:
        result = search_medicines(db, q, limit=page_size)
        return {
            "items": result["items"],
            "exact": result["exact"],
            "suggestions": result["suggestions"],
            "total": len(result["items"]),
            "page": page,
            "page_size": page_size,
            "query_normalized": result["query_normalized"],
            "note": result["note"],
        }

    rows, total = search_products(
        db,
        q=q,
        search_by=search_by,
        dosage_form=dosage_form,
        catalogue_status=catalogue_status,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [product_to_dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/medicines/{medicine_id}")
def get_medicine(medicine_id: str, db: Session = Depends(get_db)):
    stmt = (
        select(Product)
        .options(joinedload(Product.ingredients).joinedload(ProductIngredient.ingredient))
        .where(Product.id == medicine_id)
    )
    p = db.scalars(stmt).unique().first()
    if not p:
        raise HTTPException(status_code=404, detail="Medicine not found")
    data = product_to_dict(p)
    data["source"] = p.source or "source not recorded"
    data["source_date"] = p.source_date
    data["source_version"] = p.source_version
    data["identity_status"] = p.identity_status
    data["verification_status"] = (
        "DEMO_ILLUSTRATIVE" if p.is_synthetic else "catalogue_unverified"
    )
    return data


@router.get("/ingredients/search")
def search_ingredients(q: str = "", db: Session = Depends(get_db)):
    term = f"%{(q or '').strip().lower()}%"
    rows = list(
        db.scalars(
            select(Ingredient).where(Ingredient.normalized_name.like(term)).limit(30)
        ).all()
    )
    return {"items": [ingredient_to_dict(r) for r in rows]}
