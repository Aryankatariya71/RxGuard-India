"""Tests for checks.duplicate — ingredient and class duplication."""

from __future__ import annotations

import pytest

from checks.duplicate import check_duplicates
from src.rules import clear_rules_cache


@pytest.fixture(autouse=True)
def _clear():
    clear_rules_cache()
    yield
    clear_rules_cache()


def _dose(ingredients: list[dict]) -> dict:
    return {"by_ingredient": ingredients, "strength_unclear": []}


def _row(name: str, total: float, brands: list[str], unit: str = "mg") -> dict:
    return {
        "ingredient": name,
        "total_mg_per_day": total,
        "unit": unit,
        "contributions": [{"brand": b, "mg_per_day": total / len(brands)} for b in brands],
    }


def test_same_ingredient_two_brands_review():
    alerts = check_duplicates(
        _dose([_row("paracetamol", 2950, ["Dolo 650", "Crocin Advance"])])
    )
    dups = [a for a in alerts if a["type"] == "duplicate" and a["ingredients"] == ["paracetamol"]]
    assert len(dups) == 1
    assert dups[0]["tier"] == "review"
    assert "Dolo" in dups[0]["reason"] or "Dolo" in ",".join(dups[0]["brands"])


def test_same_ingredient_over_limit_critical():
    alerts = check_duplicates(
        _dose([_row("paracetamol", 5575, ["Dolo 650", "Crocin Advance", "Combiflam"])])
    )
    dups = [a for a in alerts if "paracetamol" in a["ingredients"] and len(a["ingredients"]) == 1]
    assert dups[0]["tier"] == "critical"


def test_single_brand_no_duplicate():
    alerts = check_duplicates(_dose([_row("paracetamol", 1950, ["Dolo 650"])]))
    assert not any(
        a["type"] == "duplicate" and a["ingredients"] == ["paracetamol"] for a in alerts
    )


def test_combiflam_style_hidden_para_with_dolo():
    """Combination product + solo para = duplicate ingredient."""
    alerts = check_duplicates(
        _dose(
            [
                _row("paracetamol", 2600, ["Dolo 650", "Combiflam"]),
                _row("ibuprofen", 800, ["Combiflam"]),
            ]
        )
    )
    para = [a for a in alerts if a["ingredients"] == ["paracetamol"]]
    assert len(para) == 1
    assert para[0]["tier"] == "review"


def test_two_nsaids_class_duplicate():
    alerts = check_duplicates(
        _dose(
            [
                _row("ibuprofen", 800, ["Brufen"]),
                _row("diclofenac", 100, ["Voveran"]),
            ]
        )
    )
    class_alerts = [a for a in alerts if "nsaid" in a.get("source_label", "")]
    assert len(class_alerts) == 1
    assert class_alerts[0]["tier"] == "review"
    assert set(class_alerts[0]["ingredients"]) == {"ibuprofen", "diclofenac"}


def test_two_ppis_class_duplicate():
    alerts = check_duplicates(
        _dose(
            [
                _row("pantoprazole", 40, ["Pantocid"]),
                _row("omeprazole", 20, ["Omez"]),
            ]
        )
    )
    assert any("ppi" in a.get("source_label", "") for a in alerts)


def test_different_classes_no_class_dup():
    alerts = check_duplicates(
        _dose(
            [
                _row("paracetamol", 1000, ["Dolo"]),
                _row("pantoprazole", 40, ["Pantocid"]),
            ]
        )
    )
    assert not any("class_duplicate" in a.get("source_label", "") for a in alerts)


def test_one_nsaid_no_class_dup():
    alerts = check_duplicates(_dose([_row("ibuprofen", 800, ["Brufen"])]))
    assert not any("nsaid" in a.get("source_label", "") for a in alerts)


def test_alert_shape():
    alerts = check_duplicates(
        _dose([_row("paracetamol", 3000, ["A", "B"])])
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


def test_empty_input():
    assert check_duplicates(_dose([])) == []


def test_three_brands_listed():
    alerts = check_duplicates(
        _dose([_row("paracetamol", 3000, ["Dolo 650", "Crocin Advance", "Combiflam"])])
    )
    assert len(alerts[0]["brands"]) == 3


def test_null_limit_ingredient_stays_review():
    """Amoxicillin has null adult max — duplicate stays review even if high total."""
    alerts = check_duplicates(
        _dose([_row("amoxicillin", 9000, ["BrandA", "BrandB"])])
    )
    amox = [a for a in alerts if a["ingredients"] == ["amoxicillin"]]
    assert amox[0]["tier"] == "review"


def test_ibuprofen_over_limit_duplicate_critical():
    alerts = check_duplicates(
        _dose([_row("ibuprofen", 4000, ["Brufen", "Combiflam"])])
    )
    assert alerts[0]["tier"] == "critical"


def test_no_false_alarm_unrelated_ingredients():
    alerts = check_duplicates(
        _dose(
            [
                _row("metformin", 1000, ["Glycomet"]),
                _row("atorvastatin", 10, ["Atorva"]),
                _row("amlodipine", 5, ["Amlong"]),
            ]
        )
    )
    assert alerts == []


def test_aspirin_ibuprofen_nsaid_class():
    alerts = check_duplicates(
        _dose(
            [
                _row("aspirin", 75, ["Ecosprin"]),
                _row("ibuprofen", 400, ["Brufen"]),
            ]
        )
    )
    assert any(
        set(a["ingredients"]) == {"aspirin", "ibuprofen"}
        or "nsaid" in a.get("source_label", "")
        for a in alerts
    )


def test_same_ingredient_once_not_class():
    """Two contributions same brand name still one brand — no dup if single brand string."""
    row = {
        "ingredient": "paracetamol",
        "total_mg_per_day": 2000,
        "unit": "mg",
        "contributions": [
            {"brand": "Dolo 650", "mg_per_day": 1000},
            {"brand": "Dolo 650", "mg_per_day": 1000},
        ],
    }
    alerts = check_duplicates(_dose([row]))
    assert not any(a["ingredients"] == ["paracetamol"] for a in alerts)
