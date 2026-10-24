"""Daily dose vs max_dose.json checks (adult, pediatric, renal, elderly)."""

from __future__ import annotations

from typing import Any

from src.patient import Patient, age_group, renal_band
from src.rules import get_max_dose


def _draft_suffix(rule: dict) -> str:
    if rule.get("verified_by_pharmacist") is True:
        return ""
    return " Draft rule, pending pharmacist verification."


def _brands(row: dict) -> list[str]:
    out: list[str] = []
    for c in row.get("contributions") or []:
        b = c.get("brand")
        if b and b not in out:
            out.append(str(b))
    return out


def _assumed_note(row: dict) -> str:
    if any(c.get("assumed_max") for c in (row.get("contributions") or [])):
        return " (assumed at max frequency)"
    return ""


def _effective_limit_mg(
    rule: dict,
    patient: Patient,
    *,
    is_pediatric: bool,
) -> tuple[float | None, str, str | None]:
    """
    Return (limit_mg, basis, info_reason).

    info_reason set => emit info alert instead of numeric compare (e.g. need weight).
    """
    band = renal_band(patient)
    renal = rule.get("renal_adjustment") or {}
    renal_val = renal.get(band) if band != "unknown" else None

    if renal_val == "avoid":
        return 0.0, f"renal_{band}_avoid", None

    if isinstance(renal_val, (int, float)) and float(renal_val) > 0:
        return float(renal_val), f"renal_{band}", None

    if is_pediatric:
        ped = rule.get("pediatric_mg_per_kg_day")
        if ped is None:
            return None, "pediatric_null", None
        if patient.weight_kg is None or float(patient.weight_kg) <= 0:
            return None, "need_weight", (
                f"Weight needed to check {rule['ingredient']} pediatric dose "
                f"({ped:g} mg/kg/day)."
            )
        w = float(patient.weight_kg)
        limit = w * float(ped)
        return limit, "pediatric_mg_per_kg", None

    adult = rule.get("adult_max_mg_day")
    if adult is None:
        return None, "adult_null", None
    return float(adult), "adult_max", None


def check_doses(daily_dose_result: dict, patient: Patient) -> list[dict]:
    """
    Compare per-ingredient daily totals to max_dose.json.

    Adults: >100% critical, 80–100% review.
    Children: limit = weight × mg/kg (formula in reason); missing weight → info.
    Renal 'avoid' → critical; numeric renal cap replaces adult limit.
    Null limits skipped. SOS totals note assumed max frequency.
    """
    alerts: list[dict] = []
    group = age_group(patient)
    is_pediatric = group in {"neonate", "infant", "child", "adolescent"}
    is_elderly = group == "elderly"

    for row in daily_dose_result.get("by_ingredient") or []:
        name = str(row.get("ingredient") or "")
        unit = str(row.get("unit") or "").lower()
        if not name or unit != "mg":
            continue

        rule = get_max_dose(name)
        if rule is None:
            continue

        total = float(row.get("total_mg_per_day") or 0)
        brands = _brands(row)
        assumed = _assumed_note(row)
        draft = _draft_suffix(rule)

        limit, basis, info_reason = _effective_limit_mg(
            rule, patient, is_pediatric=is_pediatric
        )

        if info_reason:
            alerts.append(
                {
                    "id": f"DOSE-WT-{name}",
                    "type": "dose",
                    "tier": "info",
                    "title": f"Weight needed for {name}",
                    "reason": info_reason + draft,
                    "suggested_action": "Enter patient weight (kg) to evaluate pediatric dose.",
                    "ingredients": [name],
                    "brands": brands,
                    "source_rule_id": rule["id"],
                    "source_label": f"max_dose:{rule['id']}",
                }
            )
            continue

        if limit is None:
            # Null adult/pediatric limit — skip numeric check
            continue

        # Renal avoid: any exposure is critical
        if basis.endswith("_avoid"):
            if total > 0:
                alerts.append(
                    {
                        "id": f"DOSE-RENAL-{name}",
                        "type": "dose",
                        "tier": "critical",
                        "title": f"{name.title()} contraindicated for renal band",
                        "reason": (
                            f"{name.title()} {total:g} mg/day{assumed}: rule marks "
                            f"{renal_band(patient)} renal function as avoid.{draft}"
                        ),
                        "suggested_action": (
                            "Do not use this NSAID/agent in severe renal impairment; "
                            "choose an alternative with clinician advice."
                        ),
                        "ingredients": [name],
                        "brands": brands,
                        "source_rule_id": rule["id"],
                        "source_label": f"max_dose:{rule['id']}",
                    }
                )
            continue

        if limit <= 0:
            continue

        percent = (total / limit) * 100.0
        ped = rule.get("pediatric_mg_per_kg_day")

        if is_pediatric and basis == "pediatric_mg_per_kg" and ped is not None:
            formula = (
                f"{float(patient.weight_kg):g} kg x {float(ped):g} mg/kg = "
                f"{limit:g} mg/day"
            )
            if total > limit:
                tier = "critical"
                reason = (
                    f"{name.title()} total {total:g} mg/day{assumed} exceeds pediatric "
                    f"limit ({formula}; {percent:.0f}% of limit).{draft}"
                )
            elif percent >= 80.0:
                tier = "review"
                reason = (
                    f"{name.title()} total {total:g} mg/day{assumed} is {percent:.0f}% of "
                    f"pediatric limit ({formula}).{draft}"
                )
            else:
                # Still surface elderly_note? not for pediatric
                continue
            alerts.append(
                {
                    "id": f"DOSE-{name}",
                    "type": "dose",
                    "tier": tier,
                    "title": f"{name.title()} daily dose",
                    "reason": reason,
                    "suggested_action": (
                        "Reduce dose or frequency; confirm weight-based dosing with "
                        "prescriber."
                    ),
                    "ingredients": [name],
                    "brands": brands,
                    "source_rule_id": rule["id"],
                    "source_label": f"max_dose:{rule['id']}",
                    "total_mg_per_day": total,
                    "limit_mg_day": limit,
                    "percent": percent,
                }
            )
            continue

        # Adult / elderly / renal numeric
        if total > limit:
            tier = "critical"
            reason = (
                f"{name.title()} total {total:g} mg/day{assumed} exceeds "
                f"{'renal-adjusted ' if basis.startswith('renal_') else ''}"
                f"limit {limit:g} mg/day ({percent:.0f}%).{draft}"
            )
        elif percent >= 80.0:
            tier = "review"
            reason = (
                f"{name.title()} total {total:g} mg/day{assumed} is {percent:.0f}% of "
                f"limit {limit:g} mg/day.{draft}"
            )
        else:
            continue

        if is_elderly and rule.get("elderly_note"):
            reason = reason + f" Elderly: {rule['elderly_note']}"

        alerts.append(
            {
                "id": f"DOSE-{name}",
                "type": "dose",
                "tier": tier,
                "title": f"{name.title()} daily dose",
                "reason": reason,
                "suggested_action": (
                    "Reduce total daily dose or remove duplicate sources; "
                    "confirm with prescriber."
                ),
                "ingredients": [name],
                "brands": brands,
                "source_rule_id": rule["id"],
                "source_label": f"max_dose:{rule['id']}",
                "total_mg_per_day": total,
                "limit_mg_day": limit,
                "percent": percent,
            }
        )

    return alerts
