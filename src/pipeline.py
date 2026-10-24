"""End-to-end prescription analysis: parse → resolve → dose → checks → alerts."""

from __future__ import annotations

from typing import Any

from checks.dose import check_doses
from checks.duplicate import check_duplicates
from checks.interaction import check_interactions
from src.alerts import build_report_alerts
from src.daily_dose import daily_dose_by_ingredient, resolve_prescription
from src.patient import Patient
from src.rx_parser import parse_prescription


def analyze(prescription_text: str, patient: Patient) -> dict[str, Any]:
    """
    Full safety analysis for a prescription text + patient.

    Unresolved/ambiguous brands appear under needs_confirmation (never skipped).
    """
    items = parse_prescription(prescription_text or "")
    if not items:
        return {
            "empty": True,
            "items": [],
            "daily_doses": {"by_ingredient": [], "strength_unclear": []},
            "alerts": [],
            "counts": {"critical": 0, "review": 0, "info": 0},
            "verdict": "clear",
            "needs_confirmation": [],
        }

    resolved_bundle = resolve_prescription(items)
    resolved = resolved_bundle["resolved"]
    needs_confirmation = resolved_bundle["needs_confirmation"]

    daily = daily_dose_by_ingredient(resolved, patient)
    dup_alerts = check_duplicates(daily)
    dose_alerts = check_doses(daily, patient)
    int_alerts = check_interactions(daily)

    report = build_report_alerts(
        dup_alerts,
        dose_alerts,
        int_alerts,
        strength_unclear=daily.get("strength_unclear"),
        needs_confirmation=needs_confirmation,
    )

    # Line-level items for UI / API
    line_items: list[dict[str, Any]] = []
    for r in resolved:
        line_items.append(
            {
                "line": r.get("raw") or r.get("drug_text"),
                "matched_brand": r.get("brand_name"),
                "status": r.get("resolve_status"),
                "ingredients": r.get("ingredients") or [],
                "brand_id": r.get("brand_id"),
                "resolved": True,
            }
        )
    for n in needs_confirmation:
        line_items.append(
            {
                "line": n.get("raw") or n.get("drug_text"),
                "matched_brand": None,
                "status": n.get("resolve_status") or "needs_confirmation",
                "ingredients": [],
                "candidates": n.get("candidates") or [],
                "resolved": False,
                "reason": n.get("reason"),
            }
        )

    return {
        "empty": False,
        "items": line_items,
        "resolved": resolved,
        "needs_confirmation": needs_confirmation,
        "daily_doses": daily,
        "alerts": report["alerts"],
        "counts": report["counts"],
        "verdict": report["verdict"],
        "patient": {
            "age_years": patient.age_years,
            "weight_kg": patient.weight_kg,
            "sex": patient.sex,
            "egfr": patient.egfr,
            "creatinine_mg_dl": patient.creatinine_mg_dl,
        },
    }
