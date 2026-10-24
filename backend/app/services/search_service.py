"""Medicine search: exact normalised match first; RapidFuzz suggestions never auto-selected."""

from __future__ import annotations

import re
from typing import Any

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.app.api.schemas.dtos import product_to_dict
from backend.app.models.entities import Product, ProductIngredient
from backend.app.services.ingredient_resolution import normalize_brand
from src.resolver import _numbers_compatible, normalize_query

_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
SUGGESTION_MIN = 60.0


def _product_query():
    return select(Product).options(
        joinedload(Product.ingredients).joinedload(ProductIngredient.ingredient)
    )


def _product_numbers(p: Product) -> tuple[str, ...]:
    text = f"{p.normalized_name or ''} {p.strength_label or ''} {p.brand_name or ''}"
    return tuple(_NUMBER_RE.findall(text.lower()))


def _serialize(
    p: Product,
    *,
    match_type: str,
    similarity: float | None = None,
) -> dict[str, Any]:
    data = product_to_dict(p)
    data["match_type"] = match_type  # exact | suggestion
    data["similarity"] = similarity
    data["identity_status"] = p.identity_status
    data["verification_status"] = (
        "DEMO_ILLUSTRATIVE"
        if p.is_synthetic
        else ("catalogue_unverified" if p.source else "source not recorded")
    )
    return data


def search_medicines(db: Session, q: str, *, limit: int = 20) -> dict[str, Any]:
    """
    Exact normalised case-insensitive match first; RapidFuzz suggestions second.

    Never auto-selects a fuzzy match. Number-aware: when the query includes a
    strength number, candidates missing that number are excluded from exact
    matches (e.g. "pantop 40" must never exact-match "pantop 20").
    """
    raw = (q or "").strip()
    if not raw:
        return {
            "query": q,
            "query_normalized": "",
            "query_numbers": [],
            "exact": [],
            "suggestions": [],
            "items": [],
            "note": "Empty query",
        }

    nq = normalize_query(raw)
    norm = normalize_brand(nq.get("query_norm") or raw)
    query_numbers = list(nq.get("numbers") or [])

    all_products = list(db.scalars(_product_query()).unique().all())

    exact: list[dict[str, Any]] = []
    for p in all_products:
        cand_norm = p.normalized_name or normalize_brand(p.brand_name)
        if cand_norm != norm and normalize_brand(p.brand_name) != norm:
            continue
        # Number gate: query numbers must appear on the product
        if not _numbers_compatible(query_numbers, _product_numbers(p)):
            continue
        exact.append(_serialize(p, match_type="exact", similarity=100.0))

    seen = {e["id"] for e in exact}
    suggestions: list[dict[str, Any]] = []
    scored: list[tuple[float, Product]] = []
    for p in all_products:
        if p.id in seen:
            continue
        if not _numbers_compatible(query_numbers, _product_numbers(p)):
            continue
        cand = p.normalized_name or normalize_brand(p.brand_name)
        score = float(
            max(
                fuzz.WRatio(norm, cand),
                fuzz.token_set_ratio(norm, cand),
                fuzz.ratio(norm, normalize_brand(p.brand_name)),
            )
        )
        if score >= SUGGESTION_MIN:
            scored.append((score, p))

    scored.sort(key=lambda x: (-x[0], x[1].brand_name or ""))
    for score, p in scored[:limit]:
        suggestions.append(
            _serialize(p, match_type="suggestion", similarity=round(score, 1))
        )

    items = exact + suggestions
    return {
        "query": raw,
        "query_normalized": norm,
        "query_numbers": query_numbers,
        "exact": exact,
        "suggestions": suggestions,
        "items": items[:limit],
        "note": (
            "Suggestions are never auto-selected. Confirm a product before "
            "ingredient-dependent checks run."
        ),
    }


def identity_for_match(
    *,
    match_type: str,
    exact_count: int,
    user_confirmed: bool = False,
) -> str:
    if user_confirmed:
        return "USER_CONFIRMED_MATCH"
    if match_type == "exact" and exact_count == 1:
        return "VERIFIED_CATALOGUE_MATCH"
    if match_type == "exact" and exact_count > 1:
        return "AMBIGUOUS"
    if match_type == "suggestion":
        return "SUGGESTED_MATCH"
    return "UNRESOLVED"


def feeds_ingredient_checks(identity_status: str) -> bool:
    """Only verified / user-confirmed identities feed ingredient-dependent checks."""
    return identity_status in {"VERIFIED_CATALOGUE_MATCH", "USER_CONFIRMED_MATCH"}
