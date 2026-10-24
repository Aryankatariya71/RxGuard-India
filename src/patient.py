"""Patient demographics and renal/age helpers for decision support."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Patient:
    age_years: float
    weight_kg: float | None = None
    sex: str | None = None  # "M" / "F"
    creatinine_mg_dl: float | None = None
    egfr: float | None = None
    pregnant: bool | None = None
    conditions: list[str] = field(default_factory=list)


def estimate_crcl(patient: Patient) -> float | None:
    """
    Cockcroft-Gault creatinine clearance (mL/min).

    CrCl = ((140 - age) * weight_kg * [0.85 if female else 1]) / (72 * Scr)
    Returns None if age, weight, sex, or creatinine is missing.
    """
    if (
        patient.age_years is None
        or patient.weight_kg is None
        or patient.sex is None
        or patient.creatinine_mg_dl is None
    ):
        return None
    if patient.creatinine_mg_dl <= 0 or patient.weight_kg <= 0:
        return None

    sex = str(patient.sex).strip().upper()
    if sex in {"F", "FEMALE"}:
        sex_factor = 0.85
    elif sex in {"M", "MALE"}:
        sex_factor = 1.0
    else:
        return None

    return ((140.0 - float(patient.age_years)) * float(patient.weight_kg) * sex_factor) / (
        72.0 * float(patient.creatinine_mg_dl)
    )


def renal_band(patient: Patient) -> str:
    """
    Renal function band from eGFR (preferred) or estimated CrCl.

    normal >= 60 | mild_moderate 30-59 | severe 15-29 | kidney_failure < 15 | unknown
    """
    value: float | None
    if patient.egfr is not None:
        value = float(patient.egfr)
    else:
        value = estimate_crcl(patient)

    if value is None:
        return "unknown"
    if value >= 60:
        return "normal"
    if value >= 30:
        return "mild_moderate"
    if value >= 15:
        return "severe"
    return "kidney_failure"


def age_group(patient: Patient) -> str:
    """
    Age band for pediatric/adult dosing rules.

    neonate < 1 month | infant < 1 year | child 1-<12 | adolescent 12-<18
    | adult 18-<65 | elderly >= 65
    """
    age = float(patient.age_years)
    month = 1.0 / 12.0
    if age < month:
        return "neonate"
    if age < 1.0:
        return "infant"
    if age < 12.0:
        return "child"
    if age < 18.0:
        return "adolescent"
    if age < 65.0:
        return "adult"
    return "elderly"
