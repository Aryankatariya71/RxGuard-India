"""Tests for src.patient."""

from __future__ import annotations

import pytest

from src.patient import Patient, age_group, estimate_crcl, renal_band


def test_cockcroft_gault_male_example():
    # Classic example: 65y male, 70 kg, Scr 1.0
    # CrCl = ((140-65)*70*1)/(72*1) = 72.916...
    p = Patient(age_years=65, weight_kg=70, sex="M", creatinine_mg_dl=1.0)
    crcl = estimate_crcl(p)
    assert crcl is not None
    assert crcl == pytest.approx(72.9167, rel=1e-3)


def test_cockcroft_gault_female_applies_0_85():
    p = Patient(age_years=65, weight_kg=70, sex="F", creatinine_mg_dl=1.0)
    male = estimate_crcl(Patient(age_years=65, weight_kg=70, sex="M", creatinine_mg_dl=1.0))
    female = estimate_crcl(p)
    assert female == pytest.approx(male * 0.85, rel=1e-6)


def test_cockcroft_gault_missing_returns_none():
    assert estimate_crcl(Patient(age_years=40, weight_kg=70, sex="M")) is None
    assert estimate_crcl(Patient(age_years=40, sex="M", creatinine_mg_dl=1.0)) is None
    assert estimate_crcl(Patient(age_years=40, weight_kg=70, creatinine_mg_dl=1.0)) is None


def test_renal_band_prefers_egfr_over_crcl():
    # CrCl would be high, but eGFR forces severe
    p = Patient(
        age_years=40,
        weight_kg=70,
        sex="M",
        creatinine_mg_dl=1.0,
        egfr=20,
    )
    assert renal_band(p) == "severe"


def test_renal_band_boundaries():
    def band(egfr: float) -> str:
        return renal_band(Patient(age_years=40, egfr=egfr))

    assert band(60) == "normal"
    assert band(59.9) == "mild_moderate"
    assert band(30) == "mild_moderate"
    assert band(29.9) == "severe"
    assert band(15) == "severe"
    assert band(14.9) == "kidney_failure"
    assert band(0) == "kidney_failure"


def test_renal_band_unknown_without_data():
    assert renal_band(Patient(age_years=40)) == "unknown"


def test_renal_band_from_crcl_when_no_egfr():
    # CrCl ≈ 72.9 -> normal
    p = Patient(age_years=65, weight_kg=70, sex="M", creatinine_mg_dl=1.0)
    assert renal_band(p) == "normal"


def test_age_group_boundaries():
    assert age_group(Patient(age_years=0.0)) == "neonate"
    assert age_group(Patient(age_years=1 / 12 - 1e-6)) == "neonate"
    assert age_group(Patient(age_years=1 / 12)) == "infant"
    assert age_group(Patient(age_years=0.99)) == "infant"
    assert age_group(Patient(age_years=1.0)) == "child"
    assert age_group(Patient(age_years=11.9)) == "child"
    assert age_group(Patient(age_years=12.0)) == "adolescent"
    assert age_group(Patient(age_years=17.9)) == "adolescent"
    assert age_group(Patient(age_years=18.0)) == "adult"
    assert age_group(Patient(age_years=64.9)) == "adult"
    assert age_group(Patient(age_years=65.0)) == "elderly"
    assert age_group(Patient(age_years=90)) == "elderly"


def test_patient_conditions_default_empty():
    p = Patient(age_years=30)
    assert p.conditions == []
    assert p.pregnant is None
