"""Hidden-ingredient finder: catalogue products containing a given ingredient."""

from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from backend.app.models.entities import Ingredient, Product, ProductIngredient

CAPTION = "Counts come from the A-Z Medicines Dataset of India (unverified)."
PAGE_SIZE_DEFAULT = 50


def ingredient_product_report(
    db: Session,
    ingredient_id: str,
    *,
    page: int = 1,
    page_size: int = PAGE_SIZE_DEFAULT,
    dosage_form: str | None = None,
    q: str | None = None,
    combination_only: bool | None = None,
) -> dict[str, Any]:
    ing = db.get(Ingredient, ingredient_id)
    if not ing:
        return {"found": False, "ingredient_id": ingredient_id, "caption": CAPTION}

    # All product links for this ingredient (ids only — fast with index)
    link_rows = list(
        db.execute(
            select(
                ProductIngredient.product_id,
                ProductIngredient.strength_value,
                ProductIngredient.strength_unit,
                ProductIngredient.incomplete_flag,
            ).where(
                ProductIngredient.ingredient_id == ingredient_id,
                ProductIngredient.active_flag.is_(True),
            )
        ).all()
    )
    product_ids = [r.product_id for r in link_rows]
    link_by_pid = {r.product_id: r for r in link_rows}

    if not product_ids:
        return {
            "found": True,
            "ingredient": {
                "id": ing.id,
                "canonical_name": ing.canonical_name,
                "normalized_name": ing.normalized_name,
            },
            "total_products": 0,
            "by_dosage_form": {},
            "single_ingredient": 0,
            "combination": 0,
            "top_combination_partners": [],
            "products": [],
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "caption": CAPTION,
        }

    # Ingredient counts per product (for single vs combo)
    count_map: dict[str, int] = dict(
        db.execute(
            select(ProductIngredient.product_id, func.count(ProductIngredient.id))
            .where(ProductIngredient.product_id.in_(product_ids))
            .group_by(ProductIngredient.product_id)
        ).all()
    )

    # Load product metadata for forms / filters
    products = list(
        db.scalars(
            select(Product).where(Product.id.in_(product_ids))
        ).all()
    )
    prod_by_id = {p.id: p for p in products}

    form_counts: Counter[str] = Counter()
    single = 0
    combo = 0
    for pid in product_ids:
        p = prod_by_id.get(pid)
        if not p:
            continue
        form = (p.dosage_form or "unknown").strip() or "unknown"
        form_counts[form] += 1
        if count_map.get(pid, 1) <= 1:
            single += 1
        else:
            combo += 1

    # Combination partners: other ingredients co-occurring in the same products
    co_links = list(
        db.execute(
            select(
                ProductIngredient.ingredient_id,
                Ingredient.canonical_name,
                func.count(ProductIngredient.product_id),
            )
            .join(Ingredient, Ingredient.id == ProductIngredient.ingredient_id)
            .where(
                ProductIngredient.product_id.in_(product_ids),
                ProductIngredient.ingredient_id != ingredient_id,
                ProductIngredient.active_flag.is_(True),
            )
            .group_by(ProductIngredient.ingredient_id, Ingredient.canonical_name)
            .order_by(func.count(ProductIngredient.product_id).desc())
            .limit(10)
        ).all()
    )
    top_partners = [
        {
            "ingredient_id": row[0],
            "canonical_name": row[1],
            "product_count": int(row[2]),
        }
        for row in co_links
    ]

    # Filter + paginate brand list
    filtered: list[str] = []
    q_norm = (q or "").strip().lower()
    form_filter = (dosage_form or "").strip().lower() or None
    for pid in product_ids:
        p = prod_by_id.get(pid)
        if not p:
            continue
        n_ings = count_map.get(pid, 1)
        if combination_only is True and n_ings <= 1:
            continue
        if combination_only is False and n_ings > 1:
            continue
        if form_filter and (p.dosage_form or "").lower() != form_filter:
            continue
        if q_norm and q_norm not in (p.brand_name or "").lower() and q_norm not in (
            p.normalized_name or ""
        ):
            continue
        filtered.append(pid)

    filtered.sort(key=lambda pid: (prod_by_id[pid].brand_name or "").lower())
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    total = len(filtered)
    total_pages = (total + page_size - 1) // page_size if total else 0
    start = (page - 1) * page_size
    page_ids = filtered[start : start + page_size]

    # Strengths for page products (all ingredients for display)
    page_items: list[dict[str, Any]] = []
    if page_ids:
        page_products = (
            db.scalars(
                select(Product)
                .options(
                    joinedload(Product.ingredients).joinedload(ProductIngredient.ingredient)
                )
                .where(Product.id.in_(page_ids))
            )
            .unique()
            .all()
        )
        by_id = {p.id: p for p in page_products}
        for pid in page_ids:
            p = by_id.get(pid)
            if not p:
                continue
            link = link_by_pid.get(pid)
            incomplete = bool(link.incomplete_flag) if link else False
            # Also incomplete if any link on product is flagged
            if any(bool(l.incomplete_flag) for l in (p.ingredients or [])):
                incomplete = True
            strengths = []
            for l in p.ingredients or []:
                if not l.ingredient:
                    continue
                strengths.append(
                    {
                        "ingredient_id": l.ingredient_id,
                        "name": l.ingredient.canonical_name,
                        "strength_value": l.strength_value,
                        "strength_unit": l.strength_unit,
                        "is_target": l.ingredient_id == ingredient_id,
                    }
                )
            page_items.append(
                {
                    "id": p.id,
                    "brand_name": p.brand_name,
                    "manufacturer": p.manufacturer,
                    "dosage_form": p.dosage_form,
                    "strength_label": p.strength_label,
                    "ingredient_count": count_map.get(pid, 1),
                    "is_combination": count_map.get(pid, 1) > 1,
                    "incomplete_flag": incomplete,
                    "composition_note": (
                        "composition may be incomplete" if incomplete else None
                    ),
                    "target_strength_value": link.strength_value if link else None,
                    "target_strength_unit": link.strength_unit if link else None,
                    "ingredients": strengths,
                }
            )

    return {
        "found": True,
        "ingredient": {
            "id": ing.id,
            "canonical_name": ing.canonical_name,
            "normalized_name": ing.normalized_name,
            "status": ing.status,
            "source": ing.source,
        },
        "total_products": len(product_ids),
        "by_dosage_form": dict(form_counts.most_common()),
        "single_ingredient": single,
        "combination": combo,
        "top_combination_partners": top_partners,
        "products": page_items,
        "page": page,
        "page_size": page_size,
        "total_filtered": total,
        "total_pages": total_pages,
        "caption": CAPTION,
        "filters": {
            "q": q,
            "dosage_form": dosage_form,
            "combination_only": combination_only,
        },
    }
