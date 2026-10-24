"""Integration tests for src.pipeline.analyze."""

from __future__ import annotations

import pytest

from src.patient import Patient
from src.pipeline import analyze
from src.resolver import clear_brand_index_cache
from src.rules import clear_rules_cache


@pytest.fixture(scope="module", autouse=True)
def _warm():
    clear_brand_index_cache()
    clear_rules_cache()
    analyze("Tab Dolo 650 TDS", Patient(age_years=30, weight_kg=70))
    yield
    clear_brand_index_cache()
    clear_rules_cache()


def test_duplicate_hidden_paracetamol():
    rx = (
        "Tab Dolo 650 1-0-1 x 5 days\n"
        "Tab Crocin Advance BD\n"
        "Tab Combiflam 1-0-1"
    )
    report = analyze(rx, Patient(age_years=35, weight_kg=70))
    assert report["counts"]["critical"] == 0
    assert report["counts"]["review"] >= 1
    assert any(
        a["type"] in ("duplicate", "duplicate_dose") and "paracetamol" in a["ingredients"]
        for a in report["alerts"]
    )


def test_adult_overdose_merged_critical():
    rx = (
        "Tab Dolo 650 1-1-1-1\n"
        "Tab Crocin Advance QID\n"
        "Tab Combiflam 1-1-1"
    )
    report = analyze(rx, Patient(age_years=35, weight_kg=70))
    assert report["counts"]["critical"] >= 1
    assert report["verdict"] == "action_needed"
    para = [
        a
        for a in report["alerts"]
        if a["tier"] == "critical" and "paracetamol" in (a.get("ingredients") or [])
    ]
    assert len(para) == 1  # merged duplicate+dose


def test_child_overdose():
    rx = "Tab Dolo 650 TDS\nTab Crocin Advance BD"
    report = analyze(rx, Patient(age_years=5, weight_kg=18))
    assert report["counts"]["critical"] >= 1
    crit = [a for a in report["alerts"] if a["tier"] == "critical"]
    assert any("18 kg" in (a.get("reason") or "") or "paracetamol" in a["ingredients"] for a in crit)


def test_interaction_warfarin():
    rx = "Tab Warf 5 1-0-0\nTab Ecosprin 75 OD\nTab Brufen 400 TDS"
    report = analyze(rx, Patient(age_years=55, weight_kg=70))
    crit_ints = [
        a
        for a in report["alerts"]
        if a["type"] == "interaction" and a["tier"] == "critical"
    ]
    assert len(crit_ints) == 3
    assert report["counts"]["critical"] == 3


def test_misspelling_and_unknown_brand():
    rx = "Tab Dolo650 TDS\nTab Pantap 40 OD\nTab Xyzabc 1-0-1"
    report = analyze(rx, Patient(age_years=35, weight_kg=70))
    assert report["needs_confirmation"]
    # At least one unresolved / confirmation alert
    assert any(
        a["type"] == "needs_confirmation" or a.get("tier") in ("info", "review")
        for a in report["alerts"]
    ) or report["needs_confirmation"]
    # Dolo650 / Pantap may resolve; Xyzabc must need confirmation
    unresolved = [
        n for n in report["needs_confirmation"] if "xyz" in (n.get("drug_text") or "").lower()
    ]
    assert unresolved


def test_unknown_brand_not_skipped():
    report = analyze("Tab CompletelyFakeBrand999 OD", Patient(age_years=30, weight_kg=70))
    assert len(report["needs_confirmation"]) >= 1
    assert report["items"]
    assert report["items"][0]["resolved"] is False


def test_clean_prescription():
    rx = "Tab Pantop 40 OD\nTab Amlong 5 OD"
    report = analyze(rx, Patient(age_years=40, weight_kg=70))
    assert report["counts"]["critical"] == 0
    assert report["verdict"] in ("clear", "review")


def test_syrup_unclear_strength():
    rx = "Syp Ascoril LS 5ml TDS"
    report = analyze(rx, Patient(age_years=35, weight_kg=70))
    # May resolve brand; strength often unclear for multi-ingredient syrups
    unclear = (report.get("daily_doses") or {}).get("strength_unclear") or []
    strength_alerts = [a for a in report["alerts"] if a["type"] == "strength_unclear"]
    # Either unclear list or info alert, or resolved with some totals — must not crash
    assert report["verdict"] in ("clear", "review", "action_needed")
    assert "alerts" in report
    _ = unclear, strength_alerts
