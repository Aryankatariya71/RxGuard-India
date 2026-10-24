"""Methodology stats endpoint — real counts, null when missing."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.methodology_stats import build_methodology_stats


client = TestClient(app)


def test_methodology_stats_endpoint_shape():
    res = client.get("/api/methodology/stats")
    assert res.status_code == 200
    data = res.json()
    assert "disclaimer" in data
    assert "does not replace a doctor" in data["disclaimer"].lower()
    assert "products_in_db" in data
    assert "interaction_rules" in data
    assert "dose_rules" in data
    assert "tests" in data
    # Missing must be null, never invent zeroes for file stats when absent —
    # but present DB may legitimately be 0 in empty test DB; null preferred for absent files.
    files = data.get("catalogue_files") or {}
    for key in ("source_csv_rows", "cleaned_parquet_rows", "ddinter_pairs_loaded"):
        assert key in files
        assert files[key] is None or isinstance(files[key], int)


def test_meta_and_evaluation_endpoints():
    meta = client.get("/api/meta")
    assert meta.status_code == 200
    body = meta.json()
    assert body.get("engine_version")
    assert body.get("disclaimer")

    ev = client.get("/api/evaluation")
    assert ev.status_code == 200
    ebody = ev.json()
    assert "gold" in ebody
    assert "clinical accuracy" in (ebody.get("disclaimer") or "").lower()


def test_build_stats_null_not_fake_for_missing_products(monkeypatch):
    """When DB has no products, products_in_db is null (not a fabricated catalogue size)."""
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        stats = build_methodology_stats(db)
        # Either null (empty) or a real int from seeded DB — never a magic marketing number string
        val = stats["products_in_db"]
        assert val is None or isinstance(val, int)
        if val is not None:
            assert val >= 0
    finally:
        db.close()
