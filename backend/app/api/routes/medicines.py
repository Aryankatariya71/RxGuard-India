from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.app.api.schemas.dtos import ingredient_to_dict, product_to_dict
from backend.app.db.session import get_db
from backend.app.models.entities import Ingredient, Product, ProductIngredient
from backend.app.services.ingredient_resolution import search_products

router = APIRouter(tags=["medicines"])


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
        raise HTTPException(404, "Medicine not found")
    return product_to_dict(p)


@router.get("/ingredients/search")
def search_ingredients(q: str = "", db: Session = Depends(get_db)):
    term = f"%{(q or '').strip().lower()}%"
    rows = list(
        db.scalars(
            select(Ingredient).where(Ingredient.normalized_name.like(term)).limit(30)
        ).all()
    )
    return {"items": [ingredient_to_dict(r) for r in rows]}
