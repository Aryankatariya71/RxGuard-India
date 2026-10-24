"""Stage 2: search ranking, identity statuses, combination expansion."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.session import Base
from backend.app.models import entities  # noqa: F401
from backend.app.models.entities import Ingredient, Product, ProductIngredient
from backend.app.services.search_service import (
    feeds_ingredient_checks,
    identity_for_match,
    search_medicines,
)
from backend.app.services.seed_service import seed_demo


def _session(tmp_path):
    url = f"sqlite:///{(tmp_path / 's2.db').as_posix()}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()


def test_exact_outranks_suggestions(tmp_path):
    db = _session(tmp_path)
    seed_demo(db)
    result = search_medicines(db, "Demo Product Alpha")
    assert result["exact"], "expected an exact hit"
    assert all(i["match_type"] == "exact" for i in result["exact"])
    if result["suggestions"]:
        assert result["items"][0]["match_type"] == "exact"
        assert result["items"][0]["id"] == result["exact"][0]["id"]
    db.close()


def test_fuzzy_never_auto_confirms(tmp_path):
    db = _session(tmp_path)
    seed_demo(db)
    # Typo should only appear as suggestion
    result = search_medicines(db, "Demo Produkt Alph")
    assert result["exact"] == []
    for s in result["suggestions"]:
        assert s["match_type"] == "suggestion"
        assert s["similarity"] is not None
        assert s["similarity"] < 100
    assert identity_for_match(match_type="suggestion", exact_count=0) == "SUGGESTED_MATCH"
    assert not feeds_ingredient_checks("SUGGESTED_MATCH")
    db.close()


def test_number_aware_exact_rejects_wrong_strength(tmp_path):
    db = _session(tmp_path)
    db.add_all(
        [
            Product(
                id="pantop-40",
                brand_name="Pantop 40",
                normalized_name="pantop 40",
                strength_label="40 mg",
                dosage_form="tablet",
                identity_status="VERIFIED_CATALOGUE_MATCH",
                source="Synthetic demo dataset",
                is_synthetic=True,
            ),
            Product(
                id="pantop-20",
                brand_name="Pantop 20",
                normalized_name="pantop 20",
                strength_label="20 mg",
                dosage_form="tablet",
                identity_status="VERIFIED_CATALOGUE_MATCH",
                source="Synthetic demo dataset",
                is_synthetic=True,
            ),
        ]
    )
    db.commit()
    result = search_medicines(db, "pantop 40")
    exact_ids = {e["id"] for e in result["exact"]}
    assert "pantop-40" in exact_ids
    assert "pantop-20" not in exact_ids
    # pantop 20 must not be treated as an exact match for pantop 40
    for e in result["exact"]:
        assert "20" not in (e.get("normalized_name") or "")
    db.close()


def test_unresolved_does_not_feed_ingredient_checks():
    assert feeds_ingredient_checks("UNRESOLVED") is False
    assert feeds_ingredient_checks("AMBIGUOUS") is False
    assert feeds_ingredient_checks("SUGGESTED_MATCH") is False
    assert feeds_ingredient_checks("VERIFIED_CATALOGUE_MATCH") is True
    assert feeds_ingredient_checks("USER_CONFIRMED_MATCH") is True


def test_combination_product_expands_all_ingredients(tmp_path):
    db = _session(tmp_path)
    seed_demo(db)
    result = search_medicines(db, "Demo Combo Gamma")
    assert result["exact"]
    combo = result["exact"][0]
    assert len(combo["ingredients"]) >= 2
    names = {i["canonical_name"] for i in combo["ingredients"]}
    assert "Synthetic Ingredient X" in names
    assert "Synthetic Ingredient Y" in names
    db.close()


def test_identity_ambiguous_when_multiple_exact(tmp_path):
    db = _session(tmp_path)
    db.add_all(
        [
            Product(
                id="dup-a",
                brand_name="Same Name",
                normalized_name="same name",
                identity_status="VERIFIED_CATALOGUE_MATCH",
                is_synthetic=True,
                source="Synthetic demo dataset",
            ),
            Product(
                id="dup-b",
                brand_name="Same Name",
                normalized_name="same name",
                identity_status="VERIFIED_CATALOGUE_MATCH",
                is_synthetic=True,
                source="Synthetic demo dataset",
            ),
        ]
    )
    db.commit()
    result = search_medicines(db, "Same Name")
    assert len(result["exact"]) == 2
    assert (
        identity_for_match(match_type="exact", exact_count=len(result["exact"]))
        == "AMBIGUOUS"
    )
    db.close()
