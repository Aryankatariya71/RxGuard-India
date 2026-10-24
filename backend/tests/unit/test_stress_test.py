"""Stress-test endpoint: determinism, N cap."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.db.migrate import upgrade
from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.services.seed_service import seed_demo
from backend.app.services.stress_test import MAX_N, run_stress_test


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


def test_stress_test_determinism_fixed_seed(client):
    r1 = client.post("/api/stress-test", json={"n": 100, "seed": 42})
    r2 = client.post("/api/stress-test", json={"n": 100, "seed": 42})
    assert r1.status_code == 200
    assert r2.status_code == 200
    a, b = r1.json(), r2.json()
    assert a["ok"] and b["ok"]
    assert a["seed"] == b["seed"] == 42
    assert a["n"] == b["n"] == 100
    assert a["had_duplicates"] == b["had_duplicates"]
    assert a["had_interactions"] == b["had_interactions"]
    assert a["had_dose_rule_matches"] == b["had_dose_rule_matches"]
    assert a["had_unresolved_items"] == b["had_unresolved_items"]
    assert a["had_check_not_run"] == b["had_check_not_run"]
    assert a["alerts_per_prescription"]["naive"] == b["alerts_per_prescription"]["naive"]
    assert (
        a["alerts_per_prescription"]["rxguard_merged"]
        == b["alerts_per_prescription"]["rxguard_merged"]
    )
    assert "Synthetic data" in a["caption"]


def test_stress_test_n_cap(client):
    r = client.post("/api/stress-test", json={"n": 99999, "seed": 1})
    # Pydantic le=MAX_N should reject, or service clamps
    assert r.status_code in {200, 422}
    if r.status_code == 200:
        assert r.json()["n"] <= MAX_N


def test_run_stress_test_service_cap():
    db = SessionLocal()
    try:
        out = run_stress_test(db, n=5000, seed=7)
        assert out["n"] <= MAX_N
        assert out["seed"] == 7
    finally:
        db.close()
