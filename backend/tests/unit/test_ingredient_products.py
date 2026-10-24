"""Hidden ingredient finder API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.db.migrate import upgrade
from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.services.seed_service import seed_demo


@pytest.fixture(scope="module", autouse=True)
def _seed():
    upgrade()
    db = SessionLocal()
    try:
        seed_demo(db)
    finally:
        db.close()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_ingredient_products_counts_and_partners(client):
    # Synthetic Ingredient X is in Alpha (single), Beta (single), Gamma (combo), incomplete
    r = client.get("/api/ingredients/ing-synth-x/products", params={"page_size": 50})
    assert r.status_code == 200
    body = r.json()
    assert body["found"] is True
    assert body["total_products"] >= 3
    assert body["single_ingredient"] >= 1
    assert body["combination"] >= 1
    assert "tablet" in body["by_dosage_form"]
    assert "A-Z Medicines" in body["caption"] or "unverified" in body["caption"].lower()
    partners = body["top_combination_partners"]
    assert any(p["ingredient_id"] == "ing-synth-y" for p in partners)


def test_ingredient_products_pagination(client):
    r1 = client.get(
        "/api/ingredients/ing-synth-x/products",
        params={"page": 1, "page_size": 2},
    )
    assert r1.status_code == 200
    b1 = r1.json()
    assert len(b1["products"]) <= 2
    assert b1["page"] == 1
    assert b1["page_size"] == 2
    assert b1["total_filtered"] >= b1["total_pages"]  # sanity
    if b1["total_pages"] > 1:
        r2 = client.get(
            "/api/ingredients/ing-synth-x/products",
            params={"page": 2, "page_size": 2},
        )
        ids1 = {p["id"] for p in b1["products"]}
        ids2 = {p["id"] for p in r2.json()["products"]}
        assert ids1.isdisjoint(ids2)


def test_ingredient_products_incomplete_flag_marked(client):
    r = client.get(
        "/api/ingredients/ing-synth-x/products",
        params={"q": "Incomplete", "page_size": 10},
    )
    assert r.status_code == 200
    items = r.json()["products"]
    assert items
    assert any(p.get("incomplete_flag") for p in items)
    flagged = next(p for p in items if p.get("incomplete_flag"))
    assert "incomplete" in (flagged.get("composition_note") or "").lower()


def test_ingredient_products_404(client):
    r = client.get("/api/ingredients/ing-does-not-exist/products")
    assert r.status_code == 404


def test_ingredients_search_autocomplete(client):
    r = client.get("/api/ingredients/search", params={"q": "synth"})
    assert r.status_code == 200
    names = [i["canonical_name"].lower() for i in r.json()["items"]]
    assert any("synthetic" in n for n in names)
