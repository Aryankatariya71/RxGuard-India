"""Tests for src.alerts.build_report_alerts."""

from __future__ import annotations

from src.alerts import build_report_alerts


def _dup(ing: str, brands: list[str], tier: str = "review", total: float = 3000) -> dict:
    return {
        "id": f"DUP-{ing}",
        "type": "duplicate",
        "tier": tier,
        "title": f"Duplicate {ing}",
        "reason": f"{ing} in {', '.join(brands)}",
        "suggested_action": "Use one product",
        "ingredients": [ing],
        "brands": brands,
        "source_rule_id": "DUP",
        "source_label": "duplicate_ingredient",
        "total_mg_per_day": total,
    }


def _dose(
    ing: str,
    tier: str,
    total: float,
    limit: float,
    brands: list[str] | None = None,
) -> dict:
    pct = (total / limit) * 100
    return {
        "id": f"DOSE-{ing}",
        "type": "dose",
        "tier": tier,
        "title": f"{ing} dose",
        "reason": f"{ing} {total} vs {limit}. Draft rule, pending pharmacist verification.",
        "suggested_action": "Reduce dose",
        "ingredients": [ing],
        "brands": brands or ["Brand"],
        "source_rule_id": "MAX",
        "source_label": "max_dose",
        "total_mg_per_day": total,
        "limit_mg_day": limit,
        "percent": pct,
    }


def _int(a: str, b: str, tier: str = "critical") -> dict:
    ings = sorted([a, b])
    return {
        "id": f"INT-{ings[0]}+{ings[1]}",
        "type": "interaction",
        "tier": tier,
        "title": f"Interaction: {ings[0]} + {ings[1]}",
        "reason": f"{a} interacts with {b}",
        "suggested_action": "Review",
        "ingredients": ings,
        "brands": ["X", "Y"],
        "source_rule_id": "CUR",
        "source_label": "curated",
    }


def test_merge_duplicate_and_dose_counts_once():
    dups = [_dup("paracetamol", ["Dolo 650", "Crocin Advance", "Combiflam"], "review", 5575)]
    doses = [_dose("paracetamol", "critical", 5575, 4000, ["Dolo 650", "Crocin Advance", "Combiflam"])]
    report = build_report_alerts(dups, doses, [])
    para = [a for a in report["alerts"] if "paracetamol" in (a.get("ingredients") or [])]
    assert len(para) == 1
    assert para[0]["tier"] == "critical"
    assert para[0]["type"] == "duplicate_dose"
    assert "5575" in para[0]["reason"]
    assert "4000" in para[0]["reason"]
    assert report["counts"]["critical"] == 1


def test_critical_sorted_first():
    report = build_report_alerts(
        [],
        [_dose("paracetamol", "review", 3200, 4000)],
        [_int("warfarin", "aspirin", "critical"), _int("a", "b", "info")],
    )
    tiers = [a["tier"] for a in report["alerts"]]
    assert tiers[0] == "critical"
    assert tiers[-1] == "info" or "info" in tiers


def test_naive_many_alerts_collapse():
    """10+ naive alerts collapse to fewer after merge/dedupe."""
    dups = [
        _dup("paracetamol", ["Dolo", "Crocin"], "review", 5000),
        _dup("paracetamol", ["Dolo", "Crocin"], "review", 5000),  # identical
    ]
    doses = [
        _dose("paracetamol", "critical", 5000, 4000, ["Dolo", "Crocin"]),
        _dose("paracetamol", "critical", 5000, 4000, ["Dolo", "Crocin"]),  # identical
    ]
    interactions = [
        _int("warfarin", "aspirin"),
        _int("aspirin", "warfarin"),  # same pair reverse — merge
        _int("warfarin", "ibuprofen"),
        _int("ibuprofen", "diclofenac", "review"),
        _int("ibuprofen", "diclofenac", "review"),  # dup
    ]
    unclear = [
        {"ingredient": "x", "brand": "Syp", "reason": "strength_missing"},
        {"ingredient": "x", "brand": "Syp", "reason": "strength_missing"},
    ]
    needs = [
        {"drug_text": "UnkownBrand", "resolve_status": "not_found", "candidates": []},
    ]
    naive_count = len(dups) + len(doses) + len(interactions) + len(unclear) + len(needs)
    assert naive_count >= 10
    report = build_report_alerts(dups, doses, interactions, unclear, needs)
    assert len(report["alerts"]) < naive_count
    # paracetamol merged once
    para = [a for a in report["alerts"] if a.get("ingredients") == ["paracetamol"]]
    assert len(para) == 1
    assert report["alerts"][0]["tier"] == "critical"


def test_verdict_action_needed():
    report = build_report_alerts([], [_dose("paracetamol", "critical", 5000, 4000)], [])
    assert report["verdict"] == "action_needed"


def test_verdict_review():
    report = build_report_alerts([_dup("paracetamol", ["A", "B"])], [], [])
    assert report["verdict"] == "review"
    assert report["counts"]["critical"] == 0


def test_verdict_clear():
    report = build_report_alerts([], [], [])
    assert report["verdict"] == "clear"
    assert report["counts"] == {"critical": 0, "review": 0, "info": 0}


def test_strength_unclear_to_info():
    report = build_report_alerts(
        [],
        [],
        [],
        strength_unclear=[{"ingredient": "azithromycin", "brand": "Azithral Syp", "reason": "per_unit_missing"}],
    )
    assert report["counts"]["info"] == 1
    assert "Strength unclear" in report["alerts"][0]["title"]


def test_needs_confirmation_ambiguous_review():
    report = build_report_alerts(
        [],
        [],
        [],
        needs_confirmation=[
            {
                "drug_text": "Mywarf",
                "resolve_status": "ambiguous",
                "candidates": [{"name": "Mywarf 1"}, {"name": "Mywarf 2"}],
            }
        ],
    )
    assert report["alerts"][0]["tier"] == "review"
    assert "Confirm brand" in report["alerts"][0]["title"]


def test_needs_confirmation_not_found_info():
    report = build_report_alerts(
        [],
        [],
        [],
        needs_confirmation=[{"drug_text": "FakeBrandXYZ", "resolve_status": "not_found", "candidates": []}],
    )
    assert report["alerts"][0]["tier"] == "info"


def test_interaction_pair_merged_once():
    report = build_report_alerts(
        [],
        [],
        [_int("warfarin", "aspirin"), _int("aspirin", "warfarin")],
    )
    ints = [a for a in report["alerts"] if a["type"] == "interaction"]
    assert len(ints) == 1


def test_class_duplicate_not_merged_with_unrelated_dose():
    class_dup = {
        "id": "DUP-CLASS-nsaid",
        "type": "duplicate",
        "tier": "review",
        "title": "Duplicate nsaid",
        "reason": "two nsaids",
        "suggested_action": "one nsaid",
        "ingredients": ["ibuprofen", "diclofenac"],
        "brands": ["A", "B"],
        "source_rule_id": "CLASS",
        "source_label": "class_duplicate:nsaid",
    }
    report = build_report_alerts(
        [class_dup],
        [_dose("paracetamol", "critical", 5000, 4000)],
        [],
    )
    assert len(report["alerts"]) == 2


def test_each_alert_one_reason_one_action():
    report = build_report_alerts(
        [_dup("paracetamol", ["A", "B"])],
        [_dose("paracetamol", "critical", 5000, 4000, ["A", "B"])],
        [_int("warfarin", "aspirin")],
    )
    for a in report["alerts"]:
        assert a["reason"]
        assert a["suggested_action"]
        assert isinstance(a["reason"], str)


def test_identical_removed():
    d = _dose("ibuprofen", "review", 2800, 3200)
    report = build_report_alerts([], [d, dict(d), dict(d)], [])
    assert len(report["alerts"]) == 1


def test_counts_sum_matches_alerts():
    report = build_report_alerts(
        [_dup("paracetamol", ["A", "B"])],
        [],
        [_int("w", "a"), _int("x", "y", "info")],
        strength_unclear=[{"ingredient": "z", "brand": "B", "reason": "x"}],
    )
    c = report["counts"]
    assert c["critical"] + c["review"] + c["info"] == len(report["alerts"])
