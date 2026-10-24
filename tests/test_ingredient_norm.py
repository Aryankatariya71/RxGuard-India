"""Tests for salt stripping and ingredient normalization."""

from __future__ import annotations

from src.composition import normalize_ingredient, parse_composition
from src.ingredient_norm import (
    PROTECTED_NAMES,
    normalize_ingredient_parts,
    strip_salt_suffix,
)


def test_metoprolol_succinate_strips_to_metoprolol():
    parts = normalize_ingredient_parts("Metoprolol Succinate")
    assert parts["ingredient_full"] == "metoprolol succinate"
    assert parts["ingredient"] == "metoprolol"


def test_escitalopram_oxalate_strips():
    assert normalize_ingredient("Escitalopram Oxalate") == "escitalopram"


def test_cefpodoxime_proxetil_strips():
    assert normalize_ingredient("Cefpodoxime Proxetil") == "cefpodoxime"


def test_amlodipine_besilate_strips():
    assert normalize_ingredient("Amlodipine Besilate") == "amlodipine"


def test_nandrolone_decanoate_strips():
    assert normalize_ingredient("Nandrolone Decanoate") == "nandrolone"


def test_protected_mefenamic_acid_not_stripped():
    parts = normalize_ingredient_parts("Mefenamic Acid")
    assert parts["ingredient"] == "mefenamic acid"
    assert parts["ingredient_full"] == "mefenamic acid"
    assert "mefenamic acid" in PROTECTED_NAMES


def test_protected_clavulanic_acid_stays():
    assert normalize_ingredient("Clavulanic Acid") == "clavulanic acid"
    assert strip_salt_suffix("clavulanic acid") == "clavulanic acid"


def test_potassium_clavulanate_maps_to_clavulanic_acid():
    parts = normalize_ingredient_parts("Potassium Clavulanate")
    assert parts["ingredient"] == "clavulanic acid"
    assert parts["ingredient_full"] == "potassium clavulanate"


def test_clavulanate_maps_to_clavulanic_acid():
    assert normalize_ingredient("Clavulanate") == "clavulanic acid"


def test_diclofenac_sodium_maps_to_diclofenac():
    parts = normalize_ingredient_parts("Diclofenac Sodium")
    assert parts["ingredient"] == "diclofenac"
    assert parts["ingredient_full"] == "diclofenac sodium"


def test_diclofenac_diethylamine_maps_to_diclofenac():
    assert normalize_ingredient("Diclofenac Diethylamine") == "diclofenac"


def test_parse_composition_sets_ingredient_full():
    r = parse_composition("Metoprolol Succinate (50mg)")
    assert r["ingredient"] == "metoprolol"
    assert r["ingredient_full"] == "metoprolol succinate"
    assert r["strength_value"] == 50.0


def test_amoxicillin_not_damaged():
    assert normalize_ingredient("Amoxicillin") == "amoxicillin"
    assert normalize_ingredient("Amoxycillin") == "amoxicillin"


def test_chlorpheniramine_maleate_strips_then_synonym():
    parts = normalize_ingredient_parts("Chlorpheniramine Maleate")
    assert parts["ingredient_full"] == "chlorpheniramine maleate"
    assert parts["ingredient"] == "chlorphenamine"
