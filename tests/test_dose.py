"""Tests for checks.dose — max dose, pediatric, renal, null limits."""

from __future__ import annotations

import pytest

from checks.dose import check_doses
from src.patient import Patient
from src.rules import clear_rules_cache


@pytest.fixture(autouse=True)
def _clear():
    clear_rules_cache()
    yield
    clear_rules_cache()


def _dose(ingredients: list[dict]) -> dict:
    return {"by_ingredient": ingredients, "strength_unclear": []}


def _row(
    name: str,
    total: float,
    brands: list[str] | None = None,
    *,
    assumed: bool = False,
) -> dict:
    brands = brands or [name.title()]
    return {
        "ingredient": name,
        "total_mg_per_day": total,
        "unit": "mg",
        "contributions": [
            {"brand": b, "mg_per_day": total / len(brands), "assumed_max": assumed}
            for b in brands
        ],
    }


def test_adult_over_limit_critical():
    alerts = check_doses(
        _dose([_row("paracetamol", 5000, ["Dolo"])]),
        Patient(age_years=30),
    )
    assert len(alerts) == 1
    assert alerts[0]["tier"] == "critical"
    assert "4000" in alerts[0]["reason"]
    assert "Draft rule" in alerts[0]["reason"]


def test_adult_80_percent_review():
    # 80% of 4000 = 3200
    alerts = check_doses(
        _dose([_row("paracetamol", 3200, ["Dolo"])]),
        Patient(age_years=30),
    )
    assert len(alerts) == 1
    assert alerts[0]["tier"] == "review"


def test_adult_below_80_no_alert():
    alerts = check_doses(
        _dose([_row("paracetamol", 2000, ["Dolo"])]),
        Patient(age_years=30),
    )
    assert alerts == []


def test_child_formula_in_reason():
    # 18 kg x 60 = 1080; dose 2000 > limit
    alerts = check_doses(
        _dose([_row("paracetamol", 2000, ["Dolo"])]),
        Patient(age_years=5, weight_kg=18),
    )
    assert len(alerts) == 1
    assert alerts[0]["tier"] == "critical"
    assert "18 kg x 60" in alerts[0]["reason"]
    assert "1080" in alerts[0]["reason"]


def test_child_missing_weight_info():
    alerts = check_doses(
        _dose([_row("paracetamol", 1000, ["Dolo"])]),
        Patient(age_years=5),
    )
    assert len(alerts) == 1
    assert alerts[0]["tier"] == "info"
    assert "weight" in alerts[0]["reason"].lower()


def test_child_never_guesses_weight():
    alerts = check_doses(
        _dose([_row("paracetamol", 5000, ["Dolo"])]),
        Patient(age_years=8, weight_kg=None),
    )
    assert all(a["tier"] == "info" for a in alerts)
    assert not any(a["tier"] == "critical" for a in alerts)


def test_null_limit_skipped():
    alerts = check_doses(
        _dose([_row("amoxicillin", 3000, ["Augmentin"])]),
        Patient(age_years=30),
    )
    assert alerts == []


def test_sos_assumed_max_frequency_note():
    alerts = check_doses(
        _dose([_row("paracetamol", 5000, ["Dolo"], assumed=True)]),
        Patient(age_years=40),
    )
    assert "assumed at max frequency" in alerts[0]["reason"]


def test_renal_avoid_ibuprofen_critical():
    alerts = check_doses(
        _dose([_row("ibuprofen", 400, ["Brufen"])]),
        Patient(age_years=50, egfr=10),
    )
    assert any(a["tier"] == "critical" and "ibuprofen" in a["ingredients"] for a in alerts)
    assert any("avoid" in a["reason"].lower() or "renal" in a["reason"].lower() for a in alerts)


def test_renal_normal_ibuprofen_ok_below_limit():
    alerts = check_doses(
        _dose([_row("ibuprofen", 800, ["Brufen"])]),
        Patient(age_years=40, egfr=90),
    )
    assert alerts == []


def test_cetirizine_renal_mild_lower_limit():
    # mild_moderate cap 5 mg; 10 mg exceeds
    alerts = check_doses(
        _dose([_row("cetirizine", 10, ["Okacet"])]),
        Patient(age_years=40, egfr=45),
    )
    assert len(alerts) == 1
    assert alerts[0]["tier"] == "critical"


def test_elderly_note_appended_on_overdose():
    alerts = check_doses(
        _dose([_row("tramadol", 500, ["Ultram"])]),
        Patient(age_years=70),
    )
    assert alerts[0]["tier"] == "critical"
    assert "Elderly" in alerts[0]["reason"] or "elderly" in alerts[0]["reason"].lower()


def test_unknown_ingredient_no_alert():
    alerts = check_doses(
        _dose([_row("zzzzfake", 99999, ["X"])]),
        Patient(age_years=30),
    )
    assert alerts == []


def test_non_mg_unit_skipped():
    row = {
        "ingredient": "paracetamol",
        "total_mg_per_day": 5000,
        "unit": "IU",
        "contributions": [{"brand": "X", "mg_per_day": 5000}],
    }
    assert check_doses(_dose([row]), Patient(age_years=30)) == []


def test_alert_shape_and_draft():
    alerts = check_doses(
        _dose([_row("paracetamol", 4500)]),
        Patient(age_years=25),
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
    assert a["type"] == "dose"
    assert "Draft rule, pending pharmacist verification" in a["reason"]


def test_child_80_percent_review():
    # 18*60=1080; 80% = 864
    alerts = check_doses(
        _dose([_row("paracetamol", 900, ["Dolo"])]),
        Patient(age_years=5, weight_kg=18),
    )
    assert len(alerts) == 1
    assert alerts[0]["tier"] == "review"
    assert "18 kg x 60" in alerts[0]["reason"]


def test_no_false_alarm_therapeutic_doses():
    alerts = check_doses(
        _dose(
            [
                _row("paracetamol", 1500, ["Dolo"]),
                _row("pantoprazole", 20, ["Pantocid"]),
                _row("amlodipine", 5, ["Amlong"]),
            ]
        ),
        Patient(age_years=35),
    )
    assert alerts == []
