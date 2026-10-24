"""Tests for src.composition — at least 25 cases."""

from __future__ import annotations

import pandas as pd
import pytest

from src.composition import (
    expand_brand,
    load_combo_overrides,
    load_synonyms,
    normalize_ingredient,
    parse_composition,
)


# ---------------------------------------------------------------------------
# parse_composition — unit / synonym / edge cases
# ---------------------------------------------------------------------------


def test_amoxycillin_500mg_maps_to_amoxicillin():
    r = parse_composition("Amoxycillin (500mg)")
    assert r["ingredient"] == "amoxicillin"
    assert r["strength_value"] == 500.0
    assert r["unit"] == "mg"
    assert r["per_value"] is None
    assert r["per_unit"] is None
    assert r["parse_error"] is False
    assert r["strength_missing"] is False


def test_ambroxol_per_5ml():
    r = parse_composition("Ambroxol (30mg/5ml)")
    assert r["ingredient"] == "ambroxol"
    assert r["strength_value"] == 30.0
    assert r["unit"] == "mg"
    assert r["per_value"] == 5.0
    assert r["per_unit"] == "ml"
    assert r["parse_error"] is False


def test_double_space_before_brackets():
    r = parse_composition("Amoxycillin  (400mg/5ml)")
    assert r["ingredient"] == "amoxicillin"
    assert r["strength_value"] == 400.0
    assert r["unit"] == "mg"
    assert r["per_value"] == 5.0
    assert r["per_unit"] == "ml"


def test_decimal_strength_clavulanic_acid():
    r = parse_composition("Clavulanic Acid (28.5mg)")
    assert r["ingredient"] == "clavulanic acid"
    assert r["strength_value"] == 28.5
    assert r["unit"] == "mg"


def test_vitamin_d3_iu_synonym():
    r = parse_composition("Vitamin D3 (60000IU)")
    assert r["ingredient"] == "cholecalciferol"
    assert r["strength_value"] == 60000.0
    assert r["unit"] == "iu"


def test_salicylic_acid_percent():
    r = parse_composition("Salicylic Acid (2%)")
    assert r["ingredient"] == "salicylic acid"
    assert r["strength_value"] == 2.0
    assert r["unit"] == "%"


def test_insulin_iu_per_ml():
    r = parse_composition("Insulin (100IU/ml)")
    assert r["ingredient"] == "insulin"
    assert r["strength_value"] == 100.0
    assert r["unit"] == "iu"
    assert r["per_value"] is None
    assert r["per_unit"] == "ml"


def test_folic_acid_mcg():
    r = parse_composition("Folic Acid (400mcg)")
    assert r["ingredient"] == "folic acid"
    assert r["strength_value"] == 400.0
    assert r["unit"] == "mcg"


def test_cholecalciferol_fractional_mcg():
    r = parse_composition("Cholecalciferol (0.25mcg)")
    assert r["ingredient"] == "cholecalciferol"
    assert r["strength_value"] == 0.25
    assert r["unit"] == "mcg"


def test_gm_alias_maps_to_g():
    r = parse_composition("Sodium Chloride (1gm)")
    assert r["parse_error"] is False
    assert r["strength_value"] == 1.0
    assert r["unit"] == "g"
    r2 = parse_composition("Disodium Hydrogen Citrate (1.4gm/5ml)")
    assert r2["unit"] == "g"
    assert r2["per_value"] == 5.0
    assert r2["per_unit"] == "ml"


def test_percent_w_w():
    r = parse_composition("Beclometasone (0.025% w/w)")
    assert r["ingredient"] == "beclomethasone"
    assert r["strength_value"] == 0.025
    assert r["unit"] == "%"
    assert r["parse_error"] is False


def test_no_brackets_strength_missing_not_error():
    r = parse_composition("Herbal Extract Blend")
    assert r["ingredient"] == "herbal extract blend"
    assert r["strength_value"] is None
    assert r["strength_missing"] is True
    assert r["parse_error"] is False


def test_na_strength_is_strength_missing():
    r = parse_composition("Ambroxol (NA)")
    assert r["ingredient"] == "ambroxol"
    assert r["strength_value"] is None
    assert r["strength_missing"] is True
    assert r["parse_error"] is False


def test_empty_brackets_strength_missing():
    r = parse_composition("Mystery Drug ()")
    assert r["strength_missing"] is True
    assert r["parse_error"] is False


def test_unparseable_strength_is_parse_error():
    r = parse_composition("Weird Molecule (???)")
    assert r["parse_error"] is True
    assert r["strength_missing"] is True
    assert r["ingredient"] == "weird molecule"


def test_acetaminophen_synonym():
    r = parse_composition("Acetaminophen (500mg)")
    assert r["ingredient"] == "paracetamol"


def test_paracetamol_slash_acetaminophen_synonym():
    assert normalize_ingredient("Paracetamol/Acetaminophen") == "paracetamol"


def test_rifampicin_frusemide_salbutamol_synonyms():
    assert normalize_ingredient("Rifampicin") == "rifampin"
    assert normalize_ingredient("Frusemide") == "furosemide"
    assert normalize_ingredient("Salbutamol") == "albuterol"


def test_tazobactum_spelling():
    r = parse_composition("Tazobactum (500mg)")
    assert r["ingredient"] == "tazobactam"
    assert r["strength_value"] == 500.0


def test_synonyms_file_has_at_least_40_entries():
    assert len(load_synonyms()) >= 40


# ---------------------------------------------------------------------------
# expand_brand — real brand rows
# ---------------------------------------------------------------------------


def test_augmentin_625_duo():
    row = {
        "name": "Augmentin 625 Duo Tablet",
        "name_norm": "augmentin 625 duo tablet",
        "form": "tablet",
        "pack_size_label": "strip of 10 tablets",
        "short_composition1": "Amoxycillin (500mg)",
        "short_composition2": "Clavulanic Acid (125mg)",
    }
    items = expand_brand(row)
    assert len(items) == 2
    assert items[0]["ingredient"] == "amoxicillin"
    assert items[0]["strength_value"] == 500.0
    assert items[1]["ingredient"] == "clavulanic acid"
    assert items[1]["strength_value"] == 125.0
    assert all(not i["per_unit_missing"] for i in items)


def test_combiflam_tablet():
    row = {
        "name": "Combiflam Tablet",
        "name_norm": "combiflam tablet",
        "form": "tablet",
        "pack_size_label": "strip of 20 tablets",
        "short_composition1": "Ibuprofen (400mg)",
        "short_composition2": "Paracetamol (325mg)",
    }
    items = expand_brand(row)
    assert [(i["ingredient"], i["strength_value"]) for i in items] == [
        ("ibuprofen", 400.0),
        ("paracetamol", 325.0),
    ]


def test_dolo_650():
    row = {
        "name": "Dolo 650 Tablet",
        "name_norm": "dolo 650 tablet",
        "form": "tablet",
        "pack_size_label": "strip of 15 tablets",
        "short_composition1": "Paracetamol (650mg)",
        "short_composition2": None,
    }
    items = expand_brand(row)
    assert len(items) == 1
    assert items[0]["ingredient"] == "paracetamol"
    assert items[0]["strength_value"] == 650.0


def test_ascoril_ls_syrup():
    row = {
        "name": "Ascoril LS Syrup",
        "name_norm": "ascoril ls syrup",
        "form": "syrup",
        "pack_size_label": "bottle of 100 ml Syrup",
        "short_composition1": "Ambroxol (30mg/5ml)",
        "short_composition2": "Levosalbutamol (1mg/5ml)",
    }
    items = expand_brand(row)
    assert len(items) == 2
    assert items[0]["ingredient"] == "ambroxol"
    assert items[0]["per_value"] == 5.0
    assert items[0]["per_unit"] == "ml"
    assert items[1]["ingredient"] == "levalbuterol"
    assert items[1]["strength_value"] == 1.0
    assert all(i["per_unit_missing"] is False for i in items)


def test_syrup_missing_per_unit_flagged():
    row = {
        "name": "Mystery Cough Syrup",
        "name_norm": "mystery cough syrup",
        "form": "syrup",
        "pack_size_label": "bottle of 100 ml Syrup",
        "short_composition1": "Ambroxol (30mg)",
        "short_composition2": "Guaifenesin (50mg)",
    }
    items = expand_brand(row)
    assert len(items) == 2
    assert all(i["per_unit"] is None for i in items)
    assert all(i["per_unit_missing"] is True for i in items)


def test_suspension_missing_per_unit_flagged():
    row = {
        "name": "Combiflam Suspension",
        "name_norm": "combiflam suspension",
        "form": "suspension",
        "pack_size_label": "bottle of 60 ml Oral Suspension",
        "short_composition1": "Ibuprofen (100mg)",
        "short_composition2": "Paracetamol (162.5mg)",
    }
    items = expand_brand(row)
    assert all(i["per_unit_missing"] is True for i in items)


def test_drops_with_per_ml_ok():
    row = {
        "name": "Ascoril LS Drops",
        "name_norm": "ascoril ls drops",
        "form": "drops",
        "pack_size_label": "bottle of 15 ml Oral Drops",
        "short_composition1": "Ambroxol (7.5mg/ml)",
        "short_composition2": "Levosalbutamol (0.25mg/ml)",
    }
    items = expand_brand(row)
    assert items[0]["per_unit"] == "ml"
    assert items[0]["per_unit_missing"] is False


def test_dry_syrup_missing_per_unit():
    row = {
        "name": "Arclav DS Dry Syrup",
        "name_norm": "arclav ds dry syrup",
        "form": "syrup",
        "pack_size_label": "bottle of 30 ml Dry Syrup",
        "short_composition1": "Amoxycillin (400mg/5ml)",
        "short_composition2": "Clavulanic Acid (57mg/5ml)",
    }
    items = expand_brand(row)
    assert items[0]["ingredient"] == "amoxicillin"
    assert items[0]["per_unit_missing"] is False


def test_null_composition2_skipped():
    row = {
        "name": "Solo Tablet",
        "name_norm": "solo tablet",
        "form": "tablet",
        "pack_size_label": "strip of 10 tablets",
        "short_composition1": "Metformin (500mg)",
        "short_composition2": pd.NA,
    }
    items = expand_brand(row)
    assert len(items) == 1


def test_combo_override_checked_first():
    overrides = {
        "test triple tonic syrup": [
            {
                "ingredient": "ambroxol",
                "strength_value": 30.0,
                "unit": "mg",
                "per_value": 5.0,
                "per_unit": "ml",
                "per_unit_missing": False,
                "strength_missing": False,
                "raw": "Ambroxol (30mg/5ml)",
                "parse_error": False,
            },
            {
                "ingredient": "guaifenesin",
                "strength_value": 50.0,
                "unit": "mg",
                "per_value": 5.0,
                "per_unit": "ml",
                "per_unit_missing": False,
                "strength_missing": False,
                "raw": "Guaifenesin (50mg/5ml)",
                "parse_error": False,
            },
            {
                "ingredient": "terbutaline",
                "strength_value": 1.25,
                "unit": "mg",
                "per_value": 5.0,
                "per_unit": "ml",
                "per_unit_missing": False,
                "strength_missing": False,
                "raw": "Terbutaline (1.25mg/5ml)",
                "parse_error": False,
            },
        ]
    }
    row = {
        "name": "Test Triple Tonic Syrup",
        "name_norm": "test triple tonic syrup",
        "form": "syrup",
        "pack_size_label": "bottle of 100 ml Syrup",
        # Intentionally incomplete vs override:
        "short_composition1": "Ambroxol (30mg/5ml)",
        "short_composition2": "Guaifenesin (50mg/5ml)",
    }
    items = expand_brand(row, overrides=overrides)
    assert len(items) == 3
    assert [i["ingredient"] for i in items] == ["ambroxol", "guaifenesin", "terbutaline"]


def test_overrides_file_loads_empty_list():
    assert load_combo_overrides() == {}


def test_tablet_does_not_flag_per_unit_missing():
    row = {
        "name": "Plain Tablet",
        "name_norm": "plain tablet",
        "form": "tablet",
        "pack_size_label": "strip of 10 tablets",
        "short_composition1": "Ibuprofen (400mg)",
        "short_composition2": None,
    }
    items = expand_brand(row)
    assert items[0]["per_unit_missing"] is False
