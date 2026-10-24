"""Same-composition lower-price options from the local catalogue."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.app.models.entities import Product, ProductIngredient

PRICE_AS_OF = "2022-11"
PRICE_CAVEAT = (
    "Listed prices are from a 2022 dataset. Do not switch medicines without "
    "asking your doctor or pharmacist."
)


def _composition_key(product: Product) -> tuple[tuple[str, float | None, str | None], ...] | None:
    links = list(product.ingredients or [])
    if not links:
        return None
    if any(bool(l.incomplete_flag) for l in links):
        return None
    parts: list[tuple[str, float | None, str | None]] = []
    for l in links:
        if not l.active_flag:
            continue
        unit = (l.strength_unit or "").lower() or None
        parts.append((l.ingredient_id, l.strength_value, unit))
    if not parts:
        return None
    return tuple(sorted(parts, key=lambda x: (x[0], x[1] or -1, x[2] or "")))


def resolve_product_id(db: Session, medicine_id: str) -> str | None:
    """Accept Product.id, cat-{parquet_id}, or bare numeric parquet id."""
    mid = (medicine_id or "").strip()
    if not mid:
        return None
    if db.get(Product, mid):
        return mid
    if mid.isdigit():
        cat = f"cat-{mid}"
        if db.get(Product, cat):
            return cat
    if not mid.startswith("cat-") and mid.replace("-", "").isalnum():
        cat = f"cat-{mid}"
        if db.get(Product, cat):
            return cat
    return None


def find_alternatives(
    db: Session,
    product_id: str,
    *,
    limit: int = 3,
) -> dict[str, Any]:
    resolved_id = resolve_product_id(db, product_id) or product_id
    stmt = (
        select(Product)
        .options(joinedload(Product.ingredients).joinedload(ProductIngredient.ingredient))
        .where(Product.id == resolved_id)
    )
    product = db.scalars(stmt).unique().first()
    if not product:
        return {"product_id": product_id, "found": False, "alternatives": [], "caveat": PRICE_CAVEAT}

    key = _composition_key(product)
    if key is None:
        return {
            "product_id": product_id,
            "brand_name": product.brand_name,
            "found": True,
            "alternatives": [],
            "skipped_reason": "incomplete_composition_or_missing_ingredients",
            "caveat": PRICE_CAVEAT,
            "price_as_of": PRICE_AS_OF,
        }

    base_price = product.price
    form = product.dosage_form

    candidates = list(
        db.scalars(
            select(Product)
            .options(joinedload(Product.ingredients))
            .where(
                Product.id != product.id,
                Product.is_discontinued.is_(False),
            )
        )
        .unique()
        .all()
    )

    matches: list[dict[str, Any]] = []
    for c in candidates:
        if form and c.dosage_form and c.dosage_form.lower() != form.lower():
            continue
        ck = _composition_key(c)
        if ck is None or ck != key:
            continue
        if c.price is None:
            continue
        pct = None
        if base_price is not None and base_price > 0:
            pct = round(((c.price - base_price) / base_price) * 100, 1)
        matches.append(
            {
                "id": c.id,
                "brand_name": c.brand_name,
                "manufacturer": c.manufacturer,
                "price": c.price,
                "price_as_of": c.price_as_of or PRICE_AS_OF,
                "percent_difference": pct,
                "dosage_form": c.dosage_form,
                "verification_status": c.verification_status,
            }
        )

    matches.sort(key=lambda m: (m["price"] is None, m["price"] if m["price"] is not None else 1e18))
    # Prefer cheaper options for the "lower-priced" section
    cheaper = [m for m in matches if base_price is None or (m["price"] is not None and m["price"] < base_price)]
    ordered = cheaper if cheaper else matches

    return {
        "product_id": product_id,
        "brand_name": product.brand_name,
        "found": True,
        "base_price": base_price,
        "price_as_of": product.price_as_of or PRICE_AS_OF,
        "alternatives": ordered[: max(1, min(limit, 10))],
        "caveat": PRICE_CAVEAT,
        "note": "Informational only — not a recommendation to switch medicines.",
    }
