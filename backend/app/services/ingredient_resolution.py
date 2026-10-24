"""Exact catalogue resolution — never silently fuzzy-assign ingredients."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from backend.app.models.entities import Product, ProductIngredient


def normalize_brand(name: str) -> str:
    return " ".join((name or "").strip().lower().split())


def _product_options():
    return joinedload(Product.ingredients).joinedload(ProductIngredient.ingredient)


def resolve_product_exact(db: Session, brand_name: str, strength: str | None = None) -> dict:
    """
    Resolve by normalized exact brand name (+ optional strength).

    Returns status: resolved | ambiguous | unresolved
    Never assigns an ingredient from fuzzy matching.
    """
    norm = normalize_brand(brand_name)
    if not norm:
        return {"status": "unresolved", "product": None, "candidates": [], "method": None}

    q = select(Product).options(_product_options()).where(Product.normalized_name == norm)
    rows = list(db.scalars(q).unique().all())

    if strength:
        s = strength.strip().lower()
        strength_hits = [r for r in rows if (r.strength_label or "").lower() == s]
        if strength_hits:
            rows = strength_hits

    if len(rows) == 1:
        return {
            "status": "resolved",
            "product": rows[0],
            "candidates": [rows[0]],
            "method": "exact_brand" + ("_strength" if strength else ""),
        }
    if len(rows) > 1:
        return {
            "status": "ambiguous",
            "product": None,
            "candidates": rows,
            "method": None,
        }

    like = f"%{norm}%"
    suggestions = list(
        db.scalars(
            select(Product)
            .options(_product_options())
            .where(Product.normalized_name.like(like))
            .limit(8)
        )
        .unique()
        .all()
    )
    return {
        "status": "unresolved",
        "product": None,
        "candidates": suggestions,
        "method": None,
        "suggestions_only": True,
    }


def search_products(
    db: Session,
    *,
    q: str | None = None,
    search_by: str = "brand",
    dosage_form: str | None = None,
    catalogue_status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Product], int]:
    stmt = select(Product).options(_product_options())
    count_stmt = select(func.count(Product.id))

    if q:
        term = f"%{normalize_brand(q)}%"
        if search_by == "generic":
            filt = Product.strength_label.ilike(term)
        elif search_by == "strength":
            filt = Product.strength_label.ilike(f"%{q.strip()}%")
        else:
            filt = or_(
                Product.normalized_name.like(term),
                Product.brand_name.ilike(f"%{q.strip()}%"),
            )
        stmt = stmt.where(filt)
        count_stmt = count_stmt.where(filt)

    if dosage_form:
        stmt = stmt.where(Product.dosage_form == dosage_form)
        count_stmt = count_stmt.where(Product.dosage_form == dosage_form)
    if catalogue_status == "synthetic":
        stmt = stmt.where(Product.is_synthetic.is_(True))
        count_stmt = count_stmt.where(Product.is_synthetic.is_(True))
    elif catalogue_status:
        stmt = stmt.where(Product.source.ilike(f"%{catalogue_status}%"))
        count_stmt = count_stmt.where(Product.source.ilike(f"%{catalogue_status}%"))

    total = db.scalar(count_stmt) or 0
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    rows = list(
        db.scalars(
            stmt.order_by(Product.brand_name).offset((page - 1) * page_size).limit(page_size)
        )
        .unique()
        .all()
    )
    return rows, int(total)
