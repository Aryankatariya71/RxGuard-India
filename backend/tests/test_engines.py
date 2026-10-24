"""Safety engine unit tests (synthetic Stage-1 demo data)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.db.migrate import upgrade
from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.services.duplicate_detector import detect_duplicates
from backend.app.services.interaction_engine import pair_key
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


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["api"] == "up"
    assert r.json()["database"] == "connected"
    assert "demo_data_mode" in r.json()


def test_public_config_has_disclaimer(client):
    r = client.get("/api/config/public")
    body = r.json()
    assert "disclaimer" in body
    assert "missing alert" in body["disclaimer"].lower()


def test_medicine_search(client):
    r = client.get("/api/medicines", params={"q": "Demo Product Alpha"})
    assert r.status_code == 200
    assert r.json()["total"] >= 1
    assert r.json()["items"][0]["is_synthetic"] is True


def test_combination_product_has_multiple_ingredients(client):
    r = client.get("/api/medicines", params={"q": "Demo Combo Gamma"})
    item = r.json()["items"][0]
    assert len(item["ingredients"]) >= 2


def test_pair_normalization():
    assert pair_key("b", "a") == pair_key("a", "b")


def test_duplicate_detector_two_products():
    findings = detect_duplicates(
        [
            {
                "item_id": "1",
                "product_id": "p1",
                "brand_name": "A",
                "resolution_status": "resolved",
                "ingredients": [{"id": "ing1", "name": "X"}],
            },
            {
                "item_id": "2",
                "product_id": "p2",
                "brand_name": "B",
                "resolution_status": "resolved",
                "ingredients": [{"id": "ing1", "name": "X"}],
            },
        ]
    )
    assert len(findings) == 1
    assert findings[0]["category"] == "DUPLICATE_INGREDIENT"


def test_empty_findings_never_say_safe(client):
    r = client.post("/api/reviews", json={"title": "empty-ish"})
    rid = r.json()["id"]
    # Add one product that has no interaction partner
    meds = client.get("/api/medicines", params={"q": "Demo Product Alpha"}).json()["items"]
    client.post(
        f"/api/reviews/{rid}/items",
        json={
            "product_id": meds[0]["id"],
            "entered_brand_name": meds[0]["brand_name"],
            "dose_amount": 500,
            "dose_unit": "mg",
            "frequency_value": 1,
        },
    )
    report = client.post(f"/api/reviews/{rid}/evaluate").json()
    label = report["summary"]["status_label"]
    # Status labels must never claim clearance / safety (disclaimer may mention "safe" negatively)
    assert label not in {"safe", "clear", "no issues", "100% safe"}
    assert "safe" not in label.lower()
    assert label in {
        "Review recommended",
        "Potential findings",
        "Assessment incomplete",
        "No matching rule in this prototype dataset",
    }


def test_full_duplicate_and_interaction_flow(client):
    r = client.post("/api/demo/scenarios/duplicate")
    assert r.status_code == 200
    report = r.json()["report"]
    cats = {f["category"] for f in report["findings"]}
    assert "DUPLICATE_INGREDIENT" in cats
    for f in report["findings"]:
        if f["category"] == "DUPLICATE_INGREDIENT":
            assert f.get("is_synthetic") is True
            assert f.get("evidence_status") in {
                "DEMO_ONLY",
                "DEMO_ILLUSTRATIVE",
                "NOT_EVALUATED",
                "INCOMPLETE_EVIDENCE",
            }


def test_demo_scenario_interaction(client):
    r = client.post("/api/demo/scenarios/interaction")
    assert r.status_code == 200
    cats = {f["category"] for f in r.json()["report"]["findings"]}
    assert "DRUG_DRUG_INTERACTION" in cats or "INTERACTION_RULE_MATCH" in cats


def test_export_includes_disclaimer(client):
    r = client.post("/api/demo/scenarios/duplicate")
    rid = r.json()["review"]["id"]
    exp = client.get(f"/api/reviews/{rid}/export", params={"format": "txt"})
    assert exp.status_code == 200
    assert b"DISCLAIMER" in exp.content
    assert b"missing alert" in exp.content.lower() or b"Missing alerts" in exp.content


def test_unresolved_stays_visible(client):
    r = client.post("/api/demo/scenarios/unresolved")
    report = r.json()["report"]
    assert report["summary"]["unresolved_products"] >= 1
    statuses = [i["resolution_status"] for i in report["items"]]
    assert "unresolved" in statuses


def test_missing_dose_insufficient(client):
    r = client.post("/api/demo/scenarios/missing_dose")
    assert r.status_code == 200
    findings = r.json()["report"]["findings"]
    assert findings  # structural missing-data / not-evaluated path
