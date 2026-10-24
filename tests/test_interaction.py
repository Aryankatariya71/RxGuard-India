"""Tests for checks.interaction — curated, DDInter, class-level pairs."""

from __future__ import annotations

import pytest

from checks.interaction import check_interactions
from src.rules import clear_rules_cache, get_interaction


@pytest.fixture(autouse=True)
def _clear():
    clear_rules_cache()
    yield
    clear_rules_cache()


def _dose(names_brands: dict[str, list[str]]) -> dict:
    rows = []
    for name, brands in names_brands.items():
        rows.append(
            {
                "ingredient": name,
                "total_mg_per_day": 100.0,
                "unit": "mg",
                "contributions": [
                    {"brand": b, "mg_per_day": 50.0} for b in brands
                ],
            }
        )
    return {"by_ingredient": rows, "strength_unclear": []}


def test_warfarin_aspirin_critical():
    alerts = check_interactions(
        _dose({"warfarin": ["Mywarf"], "aspirin": ["Ecosprin"]})
    )
    assert len(alerts) == 1
    assert alerts[0]["tier"] == "critical"
    assert set(alerts[0]["ingredients"]) == {"aspirin", "warfarin"}
    assert alerts[0]["mechanism"] or "bleeding" in alerts[0]["reason"].lower()


def test_warfarin_ibuprofen_critical():
    alerts = check_interactions(
        _dose({"warfarin": ["Mywarf"], "ibuprofen": ["Brufen"]})
    )
    assert alerts[0]["tier"] == "critical"


def test_warfarin_aspirin_ibuprofen_three_critical_pairs():
    alerts = check_interactions(
        _dose(
            {
                "warfarin": ["Mywarf"],
                "aspirin": ["Ecosprin"],
                "ibuprofen": ["Brufen"],
            }
        )
    )
    crit = [a for a in alerts if a["tier"] == "critical"]
    # warfarin+aspirin, warfarin+ibuprofen; aspirin+ibuprofen may be review (NSAID)
    assert len(crit) >= 2
    pairs = {tuple(sorted(a["ingredients"])) for a in crit}
    assert ("aspirin", "warfarin") in pairs
    assert ("ibuprofen", "warfarin") in pairs


def test_unordered_pairs_once():
    alerts = check_interactions(
        _dose({"tramadol": ["Ultram"], "ondansetron": ["Emeset"]})
    )
    assert len(alerts) == 1
    assert "tramadol" in alerts[0]["ingredients"]
    assert "ondansetron" in alerts[0]["ingredients"]


def test_clopidogrel_omeprazole():
    alerts = check_interactions(
        _dose({"clopidogrel": ["Clopilet"], "omeprazole": ["Omez"]})
    )
    assert len(alerts) == 1
    assert alerts[0]["suggested_action"]


def test_class_level_nsaid_pair_in_check():
    # naproxen + ketorolac via class if not curated
    assert get_interaction("naproxen", "ketorolac") is not None
    alerts = check_interactions(
        _dose({"naproxen": ["Naprosyn"], "ketorolac": ["Ketorol"]})
    )
    assert len(alerts) == 1
    assert alerts[0]["type"] == "interaction"


def test_nsaid_ace_class():
    alerts = check_interactions(
        _dose({"etoricoxib": ["Etoshine"], "lisinopril": ["Listril"]})
    )
    assert len(alerts) >= 1
    assert any(a["tier"] in ("review", "critical") for a in alerts)


def test_single_ingredient_no_alert():
    assert check_interactions(_dose({"paracetamol": ["Dolo"]})) == []


def test_empty_no_alert():
    assert check_interactions(_dose({})) == []


def test_no_alert_when_no_rule():
    """Invented ingredients must not false-alarm."""
    alerts = check_interactions(
        _dose({"zzzzdrugone": ["A"], "yyyydrugtwo": ["B"]})
    )
    assert alerts == []


def test_mechanism_and_action_present():
    alerts = check_interactions(
        _dose({"ramipril": ["Cardace"], "spironolactone": ["Aldactone"]})
    )
    assert len(alerts) == 1
    assert alerts[0]["reason"]
    assert alerts[0]["suggested_action"]
    assert alerts[0]["source_rule_id"]


def test_alert_shape():
    alerts = check_interactions(
        _dose({"warfarin": ["W"], "diclofenac": ["V"]})
    )
    a = alerts[0]
    for key in (
        "id",
        "type",
        "tier",
        "title",
        "reason",
        "suggested_action",
        "ingredients",
        "brands",
        "source_rule_id",
        "source_label",
    ):
        assert key in a
    assert a["type"] == "interaction"


def test_draft_disclaimer_on_unverified():
    alerts = check_interactions(
        _dose({"warfarin": ["W"], "aspirin": ["E"]})
    )
    assert "Draft rule" in alerts[0]["reason"]


def test_brands_collected_from_both():
    alerts = check_interactions(
        _dose({"warfarin": ["Mywarf 5"], "aspirin": ["Ecosprin 75"]})
    )
    assert "Mywarf 5" in alerts[0]["brands"]
    assert "Ecosprin 75" in alerts[0]["brands"]


def test_enalapril_spironolactone():
    alerts = check_interactions(
        _dose({"enalapril": ["Envas"], "spironolactone": ["Aldactone"]})
    )
    assert len(alerts) == 1
    assert alerts[0]["source_rule_id"].startswith("CUR-") or "CUR" in alerts[0]["source_label"].upper() or alerts[0]["source_rule_id"]


def test_different_non_interacting_pair_negative():
    """If get_interaction is None, check emits nothing (no false alarm)."""
    a, b = "zzzzalpha", "zzzzbeta"
    assert get_interaction(a, b) is None
    assert check_interactions(_dose({a: ["A"], b: ["B"]})) == []


def test_ibuprofen_diclofenac_review_curated_or_class():
    alerts = check_interactions(
        _dose({"ibuprofen": ["Brufen"], "diclofenac": ["Voveran"]})
    )
    assert len(alerts) == 1
    assert alerts[0]["tier"] in ("review", "critical")
