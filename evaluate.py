"""Evaluate pipeline.analyze against tests/gold_prescriptions.json."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from src.patient import Patient
from src.pipeline import analyze
from src.resolver import clear_brand_index_cache
from src.rules import clear_rules_cache

ROOT = Path(__file__).resolve().parent
GOLD_PATH = ROOT / "tests" / "gold_prescriptions.json"
REPORT_PATH = ROOT / "docs" / "EVAL_REPORT.md"


def _patient_from(d: dict) -> Patient:
    return Patient(
        age_years=float(d["age_years"]),
        weight_kg=d.get("weight_kg"),
        sex=d.get("sex"),
        creatinine_mg_dl=d.get("creatinine_mg_dl"),
        egfr=d.get("egfr"),
        pregnant=d.get("pregnant"),
        conditions=list(d.get("conditions") or []),
    )


def _brand_hit(expected_substr: str, resolved: list[dict]) -> bool:
    needle = expected_substr.lower()
    for r in resolved:
        name = str(r.get("brand_name") or "").lower()
        if needle in name:
            return True
    return False


def _alert_match(expected: dict, actual: dict) -> bool:
    if expected.get("type") and actual.get("type") != expected["type"]:
        # Allow duplicate_dose to satisfy duplicate or dose expectations
        if not (
            actual.get("type") == "duplicate_dose"
            and expected["type"] in {"duplicate", "dose", "duplicate_dose"}
        ):
            return False
    if expected.get("tier") and actual.get("tier") != expected["tier"]:
        return False
    exp_ings = sorted(str(i).lower() for i in (expected.get("ingredients") or []))
    if exp_ings:
        act_ings = sorted(str(i).lower() for i in (actual.get("ingredients") or []))
        if exp_ings != act_ings and not set(exp_ings).issubset(set(act_ings)):
            return False
    return True


def _find_expected(expected: dict, alerts: list[dict]) -> bool:
    return any(_alert_match(expected, a) for a in alerts)


def evaluate() -> dict[str, Any]:
    clear_rules_cache()
    clear_brand_index_cache()
    gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))

    brand_ok = 0
    brand_total = 0
    # per alert type: predicted vs labeled
    tp: dict[str, int] = defaultdict(int)
    fp: dict[str, int] = defaultdict(int)
    fn: dict[str, int] = defaultdict(int)

    clean_false_alarms = 0
    clean_n = 0
    alert_totals = 0
    failures: list[dict] = []
    verified_failures: list[dict] = []
    developer_n = 0
    verified_n = 0

    for case in gold:
        cid = case["id"]
        if case.get("verified_by"):
            verified_n += 1
        else:
            developer_n += 1

        report = analyze(case["prescription_text"], _patient_from(case["patient"]))
        resolved = report.get("resolved") or []
        alerts = report.get("alerts") or []
        alert_totals += len(alerts)

        # Brand resolution: each expected substring must appear in some resolved brand
        exp_brands = case.get("expected_resolved_brands") or []
        for b in exp_brands:
            brand_total += 1
            if _brand_hit(b, resolved):
                brand_ok += 1
            else:
                failures.append(
                    {
                        "id": cid,
                        "kind": "brand",
                        "expected": b,
                        "actual": [r.get("brand_name") for r in resolved],
                    }
                )

        expected_alerts = case.get("expected_alerts") or []
        matched_actual: set[int] = set()

        for exp in expected_alerts:
            typ = exp.get("type") or "unknown"
            found_idx = None
            for i, act in enumerate(alerts):
                if i in matched_actual:
                    continue
                if _alert_match(exp, act):
                    found_idx = i
                    break
            if found_idx is not None:
                matched_actual.add(found_idx)
                tp[typ] += 1
            else:
                fn[typ] += 1
                entry = {
                    "id": cid,
                    "kind": "alert_missing",
                    "expected": exp,
                    "actual": [
                        {
                            "type": a.get("type"),
                            "tier": a.get("tier"),
                            "ingredients": a.get("ingredients"),
                        }
                        for a in alerts
                    ],
                }
                (verified_failures if case.get("verified_by") else failures).append(entry)

        # Unmatched actual alerts of types we track in this case → FP when expected list
        # is non-empty OR case is clean (expected_no_alerts_for includes critical)
        track_types = {e.get("type") for e in expected_alerts if e.get("type")}
        no_crit = "critical" in (case.get("expected_no_alerts_for") or [])
        if cid.startswith("clean") or no_crit:
            clean_n += 1
            if report["counts"].get("critical", 0) > 0:
                clean_false_alarms += 1
                failures.append(
                    {
                        "id": cid,
                        "kind": "clean_critical",
                        "expected": "0 critical",
                        "actual": report["counts"],
                    }
                )

        for i, act in enumerate(alerts):
            if i in matched_actual:
                continue
            typ = act.get("type") or "unknown"
            # Only count FP for types that were expected in this case,
            # or any critical on clean cases
            if typ in track_types:
                fp[typ] += 1
                failures.append(
                    {
                        "id": cid,
                        "kind": "alert_extra",
                        "expected": expected_alerts,
                        "actual": {
                            "type": act.get("type"),
                            "tier": act.get("tier"),
                            "ingredients": act.get("ingredients"),
                        },
                    }
                )

    def _prf(t: str) -> dict[str, float]:
        ttp, tfp, tfn = tp[t], fp[t], fn[t]
        prec = ttp / (ttp + tfp) if (ttp + tfp) else 0.0
        rec = ttp / (ttp + tfn) if (ttp + tfn) else 0.0
        return {
            "precision": round(prec, 3),
            "recall": round(rec, 3),
            "tp": ttp,
            "fp": tfp,
            "fn": tfn,
        }

    types = sorted(set(list(tp) + list(fp) + list(fn)))
    metrics = {
        "brand_resolution_accuracy": round(brand_ok / brand_total, 3) if brand_total else 0.0,
        "brand_ok": brand_ok,
        "brand_total": brand_total,
        "per_type": {t: _prf(t) for t in types},
        "false_alarm_rate_clean": round(clean_false_alarms / clean_n, 3) if clean_n else 0.0,
        "clean_n": clean_n,
        "clean_false_alarms": clean_false_alarms,
        "average_alerts_per_prescription": round(alert_totals / len(gold), 3) if gold else 0.0,
        "n_cases": len(gold),
        "developer_labeled": developer_n,
        "pharmacist_verified": verified_n,
        "failures": failures,
        "verified_failures": verified_failures,
    }
    return metrics


def write_report(metrics: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Evaluation report")
    lines.append("")
    lines.append(
        "> **developer-labeled, pending pharmacist verification; entries with "
        "`verified_by` set are reported separately**"
    )
    lines.append("")
    lines.append(f"- Cases: {metrics['n_cases']} (developer-labeled: {metrics['developer_labeled']}, "
                 f"pharmacist-verified: {metrics['pharmacist_verified']})")
    lines.append(
        f"- Brand-resolution accuracy: {metrics['brand_resolution_accuracy']} "
        f"({metrics['brand_ok']}/{metrics['brand_total']})"
    )
    lines.append(
        f"- False-alarm rate on clean prescriptions (any critical): "
        f"{metrics['false_alarm_rate_clean']} "
        f"({metrics['clean_false_alarms']}/{metrics['clean_n']})"
    )
    lines.append(
        f"- Average alerts per prescription: {metrics['average_alerts_per_prescription']}"
    )
    lines.append("")
    lines.append("## Precision / recall by alert type")
    lines.append("")
    lines.append("| type | precision | recall | tp | fp | fn |")
    lines.append("|---|---|---|---|---|---|")
    for t, m in metrics["per_type"].items():
        lines.append(
            f"| {t} | {m['precision']} | {m['recall']} | {m['tp']} | {m['fp']} | {m['fn']} |"
        )
    lines.append("")
    lines.append("## Failed cases (developer-labeled)")
    lines.append("")
    if not metrics["failures"]:
        lines.append("_None._")
    else:
        for f in metrics["failures"]:
            lines.append(f"### `{f['id']}` — {f['kind']}")
            lines.append("")
            lines.append(f"- Expected: `{json.dumps(f['expected'], ensure_ascii=False)}`")
            lines.append(f"- Actual: `{json.dumps(f['actual'], ensure_ascii=False)}`")
            lines.append("")
    lines.append("## Failed cases (pharmacist-verified subset)")
    lines.append("")
    if not metrics["verified_failures"]:
        lines.append("_None (no verified_by entries yet, or all passed)._")
    else:
        for f in metrics["verified_failures"]:
            lines.append(f"### `{f['id']}` — {f['kind']}")
            lines.append("")
            lines.append(f"- Expected: `{json.dumps(f['expected'], ensure_ascii=False)}`")
            lines.append(f"- Actual: `{json.dumps(f['actual'], ensure_ascii=False)}`")
            lines.append("")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")


def main() -> None:
    metrics = evaluate()
    print("Brand accuracy:", metrics["brand_resolution_accuracy"])
    print("False-alarm (clean):", metrics["false_alarm_rate_clean"])
    print("Avg alerts:", metrics["average_alerts_per_prescription"])
    for t, m in metrics["per_type"].items():
        print(f"  {t}: P={m['precision']} R={m['recall']} tp={m['tp']} fp={m['fp']} fn={m['fn']}")
    print("Failures:", len(metrics["failures"]))
    write_report(metrics)


if __name__ == "__main__":
    main()
