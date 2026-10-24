"""Same-composition lower-price alternatives."""

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


def test_alternatives_identical_ingredients_and_strengths(client):
    r = client.get("/api/medicines/prod-demo-alpha/alternatives", params={"limit": 3})
    assert r.status_code == 200
    body = r.json()
    assert body["found"] is True
    assert body["base_price"] == 100.0
    assert body["price_as_of"] == "2022-11"
    assert "2022" in body["caveat"]
    alts = body["alternatives"]
    assert len(alts) >= 1
    names = {a["brand_name"] for a in alts}
    assert "Demo Product Alpha Value" in names
    # Cheapest first among returned
    prices = [a["price"] for a in alts]
    assert prices == sorted(prices)
    assert all(a["price"] < 100 for a in alts)
    # Percent difference vs base
    cheap = next(a for a in alts if a["id"] == "prod-demo-alpha-cheap")
    assert cheap["percent_difference"] == -37.5


def test_alternatives_excludes_discontinued(client):
    r = client.get("/api/medicines/prod-demo-alpha/alternatives", params={"limit": 10})
    ids = {a["id"] for a in r.json()["alternatives"]}
    assert "prod-demo-alpha-disc" not in ids


def test_alternatives_skips_incomplete_flag(client):
    r = client.get("/api/medicines/prod-demo-incomplete/alternatives")
    assert r.status_code == 200
    body = r.json()
    assert body["found"] is True
    assert body["alternatives"] == []
    assert body.get("skipped_reason")


def test_alternatives_different_strength_not_matched(client):
    """Beta is same ingredient but 325 mg — must not appear for Alpha 500 mg."""
    r = client.get("/api/medicines/prod-demo-alpha/alternatives", params={"limit": 10})
    names = {a["brand_name"] for a in r.json()["alternatives"]}
    assert "Demo Product Beta" not in names


def test_alternatives_not_found(client):
    r = client.get("/api/medicines/prod-does-not-exist/alternatives")
    assert r.status_code == 200
    assert r.json()["found"] is False
