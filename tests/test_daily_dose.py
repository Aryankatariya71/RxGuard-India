"""Tests for src.daily_dose — resolve + daily ingredient totals."""

from __future__ import annotations

import pytest

from src.daily_dose import (
    clear_daily_dose_caches,
    daily_dose_by_ingredient,
    resolve_prescription,
)
from src.patient import Patient
from src.resolver import clear_brand_index_cache
from src.rx_parser import parse_prescription


@pytest.fixture(scope="module", autouse=True)
def _warm_indexes():
    clear_brand_index_cache()
    clear_daily_dose_caches()
    resolve_prescription(parse_prescription("Tab Dolo 650 TDS"))
    yield
    clear_brand_index_cache()
    clear_daily_dose_caches()


def _para(rows: list[dict], name: str) -> dict:
    for row in rows:
        if row["ingredient"] == name:
            return row
    raise AssertionError(f"{name} not in {rows}")


def test_dolo_650_tds_plus_crocin_advance_bd_paracetamol_2950():
    """650×3 + 500×2 = 2950 mg/day paracetamol from two brands."""
    items = parse_prescription("Tab Dolo 650 TDS\nTab Crocin Advance BD")
    out = resolve_prescription(items)
    assert out["needs_confirmation"] == []
    assert len(out["resolved"]) == 2

    dose = daily_dose_by_ingredient(out["resolved"], Patient(age_years=30))
    para = _para(dose["by_ingredient"], "paracetamol")
    assert para["unit"] == "mg"
    assert para["total_mg_per_day"] == 2950
    assert len(para["contributions"]) == 2
    brands = {c["brand"] for c in para["contributions"]}
    assert any("Dolo 650" in b for b in brands)
    assert any("Crocin" in b for b in brands)
    contrib_totals = sorted(c["mg_per_day"] for c in para["contributions"])
    assert contrib_totals == [1000.0, 1950.0]


def test_combiflam_1_0_1_counts_ibuprofen_and_paracetamol():
    items = parse_prescription("Tab Combiflam 1-0-1")
    out = resolve_prescription(items)
    assert len(out["resolved"]) == 1
    dose = daily_dose_by_ingredient(out["resolved"])
    ibuprofen = _para(dose["by_ingredient"], "ibuprofen")
    para = _para(dose["by_ingredient"], "paracetamol")
    # Combiflam tablet: Ibu 400 + Para 325, twice daily
    assert ibuprofen["total_mg_per_day"] == 800
    assert para["total_mg_per_day"] == 650


def test_ascoril_ls_syrup_5ml_tds_per_5ml_scaling():
    items = parse_prescription("Syp Ascoril LS 5ml TDS")
    out = resolve_prescription(items)
    assert len(out["resolved"]) == 1
    assert out["resolved"][0]["brand_name"] == "Ascoril LS Syrup"
    dose = daily_dose_by_ingredient(out["resolved"])
    ambroxol = _para(dose["by_ingredient"], "ambroxol")
    levalbuterol = _para(dose["by_ingredient"], "levalbuterol")
    # 30mg/5ml * 5ml * 3 = 90; 1mg/5ml * 5ml * 3 = 3
    assert ambroxol["total_mg_per_day"] == 90
    assert levalbuterol["total_mg_per_day"] == 3


def test_syrup_per_unit_missing_goes_to_strength_unclear():
    fake = {
        "drug_text": "Mystery Cough",
        "brand_name": "Mystery Cough Syrup",
        "dose_amount": 5,
        "dose_unit": "ml",
        "times_per_day": 3,
        "prn": False,
        "duration_days": None,
        "ingredients": [
            {
                "ingredient": "ambroxol",
                "strength_value": 30.0,
                "unit": "mg",
                "per_value": None,
                "per_unit": None,
                "per_unit_missing": True,
                "strength_missing": False,
                "raw": "Ambroxol (30mg)",
                "parse_error": False,
            }
        ],
    }
    dose = daily_dose_by_ingredient([fake])
    assert dose["by_ingredient"] == []
    assert len(dose["strength_unclear"]) == 1
    assert dose["strength_unclear"][0]["ingredient"] == "ambroxol"
    assert dose["strength_unclear"][0]["brand"] == "Mystery Cough Syrup"
    assert dose["strength_unclear"][0]["reason"] == "per_unit_missing"


def test_augmentin_625_duo_1_0_1_amox_and_clav():
    items = parse_prescription("Tab Augmentin 625 Duo 1-0-1")
    out = resolve_prescription(items)
    assert len(out["resolved"]) == 1
    dose = daily_dose_by_ingredient(out["resolved"])
    amox = _para(dose["by_ingredient"], "amoxicillin")
    clav = _para(dose["by_ingredient"], "clavulanic acid")
    assert amox["total_mg_per_day"] == 1000
    assert clav["total_mg_per_day"] == 250


def test_ambiguous_brand_goes_to_needs_confirmation():
    items = parse_prescription("Tab dolo")  # short stem -> ambiguous
    out = resolve_prescription(items)
    assert out["resolved"] == []
    assert len(out["needs_confirmation"]) == 1
    assert out["needs_confirmation"][0]["resolve_status"] == "ambiguous"
    assert out["needs_confirmation"][0]["candidates"]


def test_not_found_goes_to_needs_confirmation():
    items = parse_prescription("Tab Xyzzyfoobarquin 999 OD")
    out = resolve_prescription(items)
    assert out["resolved"] == []
    assert len(out["needs_confirmation"]) == 1
    assert out["needs_confirmation"][0]["resolve_status"] == "not_found"


def test_sos_assumes_four_doses_marked_assumed_max():
    items = parse_prescription("Tab Dolo 650 SOS")
    out = resolve_prescription(items)
    assert len(out["resolved"]) == 1
    dose = daily_dose_by_ingredient(out["resolved"])
    para = _para(dose["by_ingredient"], "paracetamol")
    assert para["total_mg_per_day"] == 650 * 4
    assert para["contributions"][0]["assumed_max"] is True


def test_duration_days_included_but_not_in_daily_total():
    items = parse_prescription("Tab Dolo 650 TDS x 5 days")
    out = resolve_prescription(items)
    dose = daily_dose_by_ingredient(out["resolved"])
    para = _para(dose["by_ingredient"], "paracetamol")
    assert para["total_mg_per_day"] == 1950  # not multiplied by 5
    assert para["contributions"][0]["duration_days"] == 5


def test_g_to_mg_conversion():
    fake = {
        "brand_name": "Big Dose Tablet",
        "dose_amount": 1,
        "dose_unit": "tab",
        "times_per_day": 2,
        "prn": False,
        "ingredients": [
            {
                "ingredient": "metformin",
                "strength_value": 1.0,
                "unit": "g",
                "per_value": None,
                "per_unit": None,
                "per_unit_missing": False,
                "strength_missing": False,
                "parse_error": False,
            }
        ],
    }
    dose = daily_dose_by_ingredient([fake])
    met = _para(dose["by_ingredient"], "metformin")
    assert met["unit"] == "mg"
    assert met["total_mg_per_day"] == 2000


def test_mcg_to_mg_conversion():
    fake = {
        "brand_name": "Folate Tab",
        "dose_amount": 1,
        "dose_unit": "tab",
        "times_per_day": 1,
        "prn": False,
        "ingredients": [
            {
                "ingredient": "folic acid",
                "strength_value": 400.0,
                "unit": "mcg",
                "per_value": None,
                "per_unit": None,
                "per_unit_missing": False,
                "strength_missing": False,
                "parse_error": False,
            }
        ],
    }
    dose = daily_dose_by_ingredient([fake])
    folic = _para(dose["by_ingredient"], "folic acid")
    assert folic["unit"] == "mg"
    assert folic["total_mg_per_day"] == pytest.approx(0.4)


def test_iu_kept_as_own_unit():
    fake = {
        "brand_name": "Vitamin D Cap",
        "dose_amount": 1,
        "dose_unit": "cap",
        "times_per_day": 1,
        "prn": False,
        "ingredients": [
            {
                "ingredient": "cholecalciferol",
                "strength_value": 60000.0,
                "unit": "iu",
                "per_value": None,
                "per_unit": None,
                "per_unit_missing": False,
                "strength_missing": False,
                "parse_error": False,
            }
        ],
    }
    dose = daily_dose_by_ingredient([fake])
    vit = _para(dose["by_ingredient"], "cholecalciferol")
    assert vit["unit"] == "iu"
    assert vit["total_mg_per_day"] == 60000


def test_resolve_does_not_silently_skip_mixed_list():
    items = parse_prescription("Tab Dolo 650 TDS\nTab dolo\nTab Pantop 40 OD")
    out = resolve_prescription(items)
    assert len(out["resolved"]) >= 2
    assert len(out["needs_confirmation"]) >= 1
    assert sum(len(out["resolved"]) for _ in [0]) + len(out["needs_confirmation"]) >= 3


def test_sum_across_brands_same_ingredient():
    items = parse_prescription("Tab Dolo 650 OD\nTab Calpol 500 OD")
    out = resolve_prescription(items)
    dose = daily_dose_by_ingredient(out["resolved"])
    para = _para(dose["by_ingredient"], "paracetamol")
    assert para["total_mg_per_day"] == 1150
    assert len(para["contributions"]) == 2


def test_patient_argument_accepted():
    items = parse_prescription("Tab Dolo 650 OD")
    out = resolve_prescription(items)
    p = Patient(age_years=70, weight_kg=60, sex="F", creatinine_mg_dl=1.2)
    dose = daily_dose_by_ingredient(out["resolved"], p)
    assert _para(dose["by_ingredient"], "paracetamol")["total_mg_per_day"] == 650


def test_resolved_item_has_ingredients_from_expand_brand():
    items = parse_prescription("Tab Augmentin 625 Duo BD")
    out = resolve_prescription(items)
    ings = {i["ingredient"] for i in out["resolved"][0]["ingredients"]}
    assert "amoxicillin" in ings
    assert "clavulanic acid" in ings
