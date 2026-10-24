"""Merge, dedupe, and rank safety alerts into a report."""

from __future__ import annotations

from typing import Any

TIER_RANK = {"critical": 3, "review": 2, "info": 1}


def _tier_max(a: str, b: str) -> str:
    return a if TIER_RANK.get(a, 0) >= TIER_RANK.get(b, 0) else b


def _norm_ings(ings: list[str] | None) -> tuple[str, ...]:
    return tuple(sorted(str(i).lower() for i in (ings or []) if i))


def _alert_fingerprint(alert: dict) -> tuple:
    return (
        alert.get("type"),
        _norm_ings(alert.get("ingredients")),
        alert.get("title"),
        alert.get("reason"),
    )


def _merge_duplicate_and_dose(
    duplicate_alerts: list[dict],
    dose_alerts: list[dict],
) -> list[dict]:
    """
    Merge a duplicate alert and a dose alert about the same single ingredient
    into one alert (highest tier, combined reason).
    """
    dose_by_ing: dict[str, dict] = {}
    multi_dose: list[dict] = []
    for d in dose_alerts:
        ings = d.get("ingredients") or []
        if len(ings) == 1:
            dose_by_ing[str(ings[0]).lower()] = d
        else:
            multi_dose.append(d)

    used_dose: set[str] = set()
    merged: list[dict] = []

    for dup in duplicate_alerts:
        ings = dup.get("ingredients") or []
        # Only merge single-ingredient duplicate with matching dose
        if len(ings) == 1:
            key = str(ings[0]).lower()
            dose = dose_by_ing.get(key)
            if dose is not None:
                used_dose.add(key)
                brands = list(dict.fromkeys((dup.get("brands") or []) + (dose.get("brands") or [])))
                brand_str = ", ".join(brands)
                total = dose.get("total_mg_per_day", dup.get("total_mg_per_day"))
                limit = dose.get("limit_mg_day")
                pct = dose.get("percent")
                name = ings[0]
                tier = _tier_max(dup.get("tier", "review"), dose.get("tier", "review"))

                if total is not None and limit is not None and pct is not None:
                    reason = (
                        f"{str(name).title()} in {brand_str}: {total:g} mg/day vs "
                        f"adult limit {limit:g} mg/day ({pct:.0f}%)"
                    )
                else:
                    reason = (
                        f"{str(name).title()} in {brand_str}: "
                        f"{dose.get('reason', dup.get('reason', ''))}"
                    )
                # Keep draft note if either had it
                if "Draft rule" in (dose.get("reason") or "") and "Draft rule" not in reason:
                    reason = reason.rstrip(".") + ". Draft rule, pending pharmacist verification."

                merged.append(
                    {
                        "id": f"MERGED-DUP-DOSE-{key}",
                        "type": "duplicate_dose",
                        "tier": tier,
                        "title": f"{str(name).title()} duplication and dose",
                        "reason": reason,
                        "suggested_action": dose.get("suggested_action")
                        or dup.get("suggested_action"),
                        "ingredients": [name],
                        "brands": brands,
                        "source_rule_id": dose.get("source_rule_id")
                        or dup.get("source_rule_id"),
                        "source_label": "merged:duplicate+dose",
                        "total_mg_per_day": total,
                        "limit_mg_day": limit,
                        "percent": pct,
                    }
                )
                continue

        merged.append(dict(dup))

    for key, dose in dose_by_ing.items():
        if key not in used_dose:
            merged.append(dict(dose))
    merged.extend(dict(d) for d in multi_dose)
    return merged


def _merge_interaction_pairs(alerts: list[dict]) -> list[dict]:
    """Collapse multiple interaction alerts for the same ingredient pair."""
    by_pair: dict[tuple[str, ...], dict] = {}
    others: list[dict] = []
    for a in alerts:
        if a.get("type") != "interaction":
            others.append(a)
            continue
        key = _norm_ings(a.get("ingredients"))
        if len(key) != 2:
            others.append(a)
            continue
        existing = by_pair.get(key)
        if existing is None:
            by_pair[key] = dict(a)
        else:
            existing["tier"] = _tier_max(existing.get("tier", "info"), a.get("tier", "info"))
            # Prefer longer / curated reason
            if len(a.get("reason") or "") > len(existing.get("reason") or ""):
                existing["reason"] = a["reason"]
                existing["suggested_action"] = a.get("suggested_action")
                existing["source_rule_id"] = a.get("source_rule_id")
                existing["source_label"] = a.get("source_label")
            brands = list(dict.fromkeys((existing.get("brands") or []) + (a.get("brands") or [])))
            existing["brands"] = brands
    return others + list(by_pair.values())


def _dedupe_identical(alerts: list[dict]) -> list[dict]:
    seen: set[tuple] = set()
    out: list[dict] = []
    for a in alerts:
        fp = _alert_fingerprint(a)
        if fp in seen:
            continue
        seen.add(fp)
        out.append(a)
    return out


def _from_strength_unclear(items: list[dict] | None) -> list[dict]:
    alerts: list[dict] = []
    for i, row in enumerate(items or []):
        ing = row.get("ingredient") or "unknown"
        brand = row.get("brand") or "unknown"
        reason_code = row.get("reason") or "unclear"
        alerts.append(
            {
                "id": f"STRENGTH-{i}-{ing}",
                "type": "strength_unclear",
                "tier": "info",
                "title": "Strength unclear, check label",
                "reason": (
                    f"Could not compute daily dose for {ing} in {brand} "
                    f"({reason_code}). Check the product label."
                ),
                "suggested_action": "Confirm strength on the pack and re-enter if needed.",
                "ingredients": [ing] if ing != "unknown" else [],
                "brands": [brand] if brand != "unknown" else [],
                "source_rule_id": "STRENGTH-UNCLEAR",
                "source_label": "strength_unclear",
            }
        )
    return alerts


def _from_needs_confirmation(items: list[dict] | None) -> list[dict]:
    alerts: list[dict] = []
    for i, row in enumerate(items or []):
        drug = row.get("drug_text") or row.get("resolve_query") or "unknown"
        status = row.get("resolve_status") or row.get("reason") or "unresolved"
        candidates = row.get("candidates") or []
        cand_names = [c.get("name") for c in candidates[:3] if c.get("name")]
        extra = f" Candidates: {', '.join(cand_names)}." if cand_names else ""
        tier = "review" if status == "ambiguous" else "info"
        alerts.append(
            {
                "id": f"CONFIRM-{i}-{drug}",
                "type": "needs_confirmation",
                "tier": tier,
                "title": "Confirm brand",
                "reason": f"Brand '{drug}' needs confirmation ({status}).{extra}",
                "suggested_action": "Pick the correct brand from candidates or fix spelling.",
                "ingredients": [],
                "brands": cand_names,
                "source_rule_id": "NEEDS-CONFIRMATION",
                "source_label": "needs_confirmation",
            }
        )
    return alerts


def build_report_alerts(
    duplicate_alerts: list[dict],
    dose_alerts: list[dict],
    interaction_alerts: list[dict],
    strength_unclear: list[dict] | None = None,
    needs_confirmation: list[dict] | None = None,
) -> dict[str, Any]:
    """
    Merge duplicate+dose for same ingredient, dedupe, merge interaction pairs,
    convert confirmation/strength rows, sort critical > review > info.

    Returns {alerts, counts: {critical, review, info}, verdict}.
    """
    merged = _merge_duplicate_and_dose(duplicate_alerts, dose_alerts)
    all_alerts = merged + [dict(a) for a in interaction_alerts]
    all_alerts = _merge_interaction_pairs(all_alerts)
    all_alerts.extend(_from_strength_unclear(strength_unclear))
    all_alerts.extend(_from_needs_confirmation(needs_confirmation))
    all_alerts = _dedupe_identical(all_alerts)

    # Ensure one reason / one action
    for a in all_alerts:
        a["reason"] = str(a.get("reason") or "").strip()
        a["suggested_action"] = str(a.get("suggested_action") or "").strip()

    all_alerts.sort(
        key=lambda a: (-TIER_RANK.get(a.get("tier", "info"), 0), a.get("type", ""), a.get("id", ""))
    )

    counts = {"critical": 0, "review": 0, "info": 0}
    for a in all_alerts:
        t = a.get("tier", "info")
        if t in counts:
            counts[t] += 1

    if counts["critical"] > 0:
        verdict = "action_needed"
    elif counts["review"] > 0:
        verdict = "review"
    else:
        verdict = "clear"

    return {"alerts": all_alerts, "counts": counts, "verdict": verdict}
