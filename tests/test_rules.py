"""Tests for src.rules — loaders, schema, interaction & max-dose lookup."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from src.composition import normalize_ingredient
from src.rules import (
    CLASSES_SCHEMA,
    CURATED_SCHEMA,
    MAX_DOSE_SCHEMA,
    clear_rules_cache,
    get_interaction,
    get_max_dose,
    load_classes,
    load_curated_interactions,
    load_ddinter_pairs,
    load_max_dose,
)

ROOT = Path(__file__).resolve().parent.parent
RULES = ROOT / "data" / "rules"


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_rules_cache()
    yield
    clear_rules_cache()


def test_curated_schema_validates():
    data = json.loads((RULES / "curated_interactions.json").read_text())
    jsonschema.validate(data, CURATED_SCHEMA)
    assert len(data) == 30


def test_max_dose_schema_validates():
    data = json.loads((RULES / "max_dose.json").read_text())
    jsonschema.validate(data, MAX_DOSE_SCHEMA)
    assert len(data) >= 20


def test_classes_schema_validates():
    data = json.loads((RULES / "classes.json").read_text())
    jsonschema.validate(data, CLASSES_SCHEMA)
    for required in (
        "nsaid",
        "ace_inhibitor",
        "arb",
        "ppi",
        "statin",
        "ssri",
        "beta_blocker",
        "fluoroquinolone",
        "cephalosporin",
        "penicillin",
        "macrolide",
        "opioid",
        "sulfonylurea",
    ):
        assert required in data
        assert len(data[required]) >= 1


def test_loaders_return_data():
    assert len(load_curated_interactions()) == 30
    assert "nsaid" in load_classes()
    assert len(load_max_dose()) >= 20
    df = load_ddinter_pairs()
    assert not df.empty
    assert set(df.columns) >= {"ing_a", "ing_b", "level", "tier", "source"}


def test_every_rule_is_draft_unverified():
    for row in load_curated_interactions():
        assert row["verified_by_pharmacist"] is False
        assert row["status"] == "DRAFT"
        assert row["source_url"]
    for row in load_max_dose():
        assert row["verified_by_pharmacist"] is False
        assert row["status"] == "DRAFT"
        assert row["source_url"]


def test_curated_overrides_ddinter():
    """Warfarin+aspirin is curated critical; must win over any DDInter row."""
    hit = get_interaction("warfarin", "aspirin")
    assert hit is not None
    assert hit["source"] == "curated"
    assert hit["id"] == "CUR-INT-001"
    assert hit["tier"] == "critical"


def test_unordered_lookup_symmetric():
    a = get_interaction("warfarin", "ibuprofen")
    b = get_interaction("ibuprofen", "warfarin")
    assert a is not None and b is not None
    assert a["id"] == b["id"]
    assert a["tier"] == b["tier"]


def test_aspirin_acetylsalicylic_acid_alias():
    assert normalize_ingredient("acetylsalicylic acid") == "aspirin"
    hit = get_interaction("warfarin", "acetylsalicylic acid")
    assert hit is not None
    assert hit["id"] == "CUR-INT-001"
    assert get_max_dose("acetylsalicylic acid") is not None
    assert get_max_dose("acetylsalicylic acid")["ingredient"] == "aspirin"


def test_acetaminophen_paracetamol_alias():
    assert normalize_ingredient("acetaminophen") == "paracetamol"
    assert get_max_dose("acetaminophen")["ingredient"] == "paracetamol"


def test_class_level_nsaid_pair():
    """Two NSAIDs not explicitly curated as that exact pair still match via class."""
    # naproxen + ketorolac: both nsaid; may or may not be curated
    hit = get_interaction("naproxen", "ketorolac")
    assert hit is not None
    assert hit["tier"] in ("critical", "review", "info")
    # Prefer class or curated
    assert hit.get("source") in ("curated", "class", "DDInter 2.0") or hit.get("source") == "curated"
    if hit.get("source") == "class":
        assert "NSAID" in hit["mechanism"].upper() or "nsaid" in hit.get("source_label", "")


def test_class_level_nsaid_ace():
    hit = get_interaction("etoricoxib", "lisinopril")
    assert hit is not None
    assert hit["tier"] == "review"
    assert hit.get("source") in ("curated", "class", "DDInter 2.0")


def test_null_adult_limit_handled():
    rule = get_max_dose("amoxicillin")
    assert rule is not None
    assert rule["adult_max_mg_day"] is None
    assert "UNSURE" in rule["notes"]


def test_null_pediatric_limit_ok():
    rule = get_max_dose("atorvastatin")
    assert rule is not None
    assert rule["pediatric_mg_per_kg_day"] is None


def test_unknown_ingredient_returns_none():
    assert get_interaction("zzzznotadrug", "yyyyalsomadeup") is None
    assert get_max_dose("zzzznotadrug123") is None


def test_same_ingredient_no_interaction():
    assert get_interaction("paracetamol", "paracetamol") is None
    assert get_interaction("aspirin", "acetylsalicylic acid") is None


def test_paracetamol_max_dose_known():
    rule = get_max_dose("paracetamol")
    assert rule is not None
    assert rule["adult_max_mg_day"] == 4000
    assert rule["pediatric_mg_per_kg_day"] == 60


def test_ibuprofen_renal_avoid_severe():
    rule = get_max_dose("ibuprofen")
    assert rule["renal_adjustment"]["severe"] == "avoid"
    assert rule["renal_adjustment"]["kidney_failure"] == "avoid"


def test_ddinter_pair_exists_for_brand_ingredients():
    df = load_ddinter_pairs()
    assert (df["tier"] == "critical").any()
    # Sample a Major/critical row and look it up
    crit = df[df["tier"] == "critical"].iloc[0]
    hit = get_interaction(crit["ing_a"], crit["ing_b"])
    assert hit is not None
    # May be curated override with higher specificity
    assert hit["tier"] in ("critical", "review", "info")


def test_get_interaction_includes_mechanism_and_action():
    hit = get_interaction("tramadol", "ondansetron")
    assert hit is not None
    assert hit["mechanism"]
    assert hit["recommended_action"]
    assert hit["source_rule_id"] or hit["id"]


def test_clopidogrel_omeprazole_curated():
    hit = get_interaction("clopidogrel", "omeprazole")
    assert hit is not None
    assert hit["source"] == "curated"
    assert hit["tier"] in ("critical", "review")


def test_ramipril_spironolactone_curated():
    hit = get_interaction("ramipril", "spironolactone")
    assert hit is not None
    assert hit["source"] == "curated"


def test_enalapril_spironolactone_curated():
    hit = get_interaction("enalapril", "spironolactone")
    assert hit is not None
    assert hit["source"] == "curated"


def test_cache_clears():
    _ = get_max_dose("paracetamol")
    clear_rules_cache()
    assert get_max_dose("paracetamol")["adult_max_mg_day"] == 4000
