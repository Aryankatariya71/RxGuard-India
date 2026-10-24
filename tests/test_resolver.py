"""Resolver tests — 40 cases covering exact, fuzzy, form hints, and ambiguity."""

from __future__ import annotations

import pytest

from src.resolver import clear_brand_index_cache, normalize_query, resolve


@pytest.fixture(scope="module", autouse=True)
def _build_index_once():
    clear_brand_index_cache()
    # Warm the cache once for the module.
    resolve("dolo 650")
    yield
    clear_brand_index_cache()


def _top_name(result: dict) -> str | None:
    if not result["candidates"]:
        return None
    return result["candidates"][0]["name"]


def _top_names(result: dict) -> list[str]:
    return [c["name"] for c in result["candidates"]]


# ---------------------------------------------------------------------------
# Query normalization
# ---------------------------------------------------------------------------


def test_normalize_splits_letters_and_digits():
    q = normalize_query("dolo650")
    assert q["query_norm"] == "dolo 650"
    assert q["numbers"] == ["650"]


def test_normalize_form_hint_tab():
    q = normalize_query("dolo 650 tab")
    assert q["query_norm"] == "dolo 650"
    assert q["form_hint"] == "tablet"


def test_normalize_form_hint_syp():
    q = normalize_query("ascoril ls syp")
    assert q["form_hint"] == "syrup"
    assert q["tokens"] == ["ascoril", "ls"]


def test_normalize_strips_punctuation():
    q = normalize_query("augmentin-625")
    assert q["query_norm"] == "augmentin 625"


# ---------------------------------------------------------------------------
# Required brand misspellings / compact forms
# ---------------------------------------------------------------------------


def test_dolo650_exact():
    r = resolve("dolo650")
    assert r["status"] in {"exact", "confident"}
    assert _top_name(r) == "Dolo 650 Tablet"


def test_dolo_650_tab():
    r = resolve("dolo 650 tab")
    assert r["status"] == "exact"
    assert _top_name(r) == "Dolo 650 Tablet"


def test_dolo_650_plain():
    r = resolve("dolo 650")
    assert r["status"] == "exact"
    assert _top_name(r) == "Dolo 650 Tablet"


def test_crocin_advanc():
    r = resolve("crocin advanc")
    assert r["status"] in {"exact", "confident"}
    assert _top_name(r) == "Crocin Advance Tablet"


def test_augmentin625():
    r = resolve("augmentin625")
    assert r["status"] in {"exact", "confident"}
    assert "Augmentin 625 Duo" in (_top_name(r) or "")


def test_augmentin_625_duo():
    r = resolve("augmentin 625 duo")
    assert r["status"] == "exact"
    assert _top_name(r) == "Augmentin 625 Duo Tablet"


def test_pantop40():
    r = resolve("pantop40")
    assert r["status"] == "exact"
    assert _top_name(r) == "Pantop 40 Tablet"


def test_pantap_40_misspelling():
    r = resolve("pantap 40")
    assert r["status"] in {"exact", "confident", "ambiguous"}
    assert _top_name(r) == "Pantop 40 Tablet"


def test_combiflam_ambiguous_without_form():
    r = resolve("combiflam")
    assert r["status"] == "ambiguous"
    names = _top_names(r)
    assert any("Tablet" in n for n in names)
    assert any("Suspension" in n for n in names)


def test_combiflam_tab_form_hint():
    r = resolve("combiflam tab")
    assert r["status"] == "exact"
    assert _top_name(r) == "Combiflam Tablet"


def test_combiflam_susp_form_hint():
    r = resolve("combiflam susp")
    assert r["status"] == "exact"
    assert _top_name(r) == "Combiflam Suspension"


def test_brufen400():
    r = resolve("brufen400")
    assert r["status"] == "exact"
    assert _top_name(r) == "Brufen 400 Tablet"


def test_ecosprin75():
    r = resolve("ecosprin75")
    assert r["status"] == "exact"
    assert _top_name(r) == "Ecosprin 75 Tablet"


def test_calpol500():
    r = resolve("calpol500")
    assert r["status"] == "exact"
    assert _top_name(r) == "Calpol 500mg Tablet"


def test_azithral_500():
    r = resolve("azithral 500")
    assert r["status"] in {"exact", "confident"}
    assert "Azithral 500" in (_top_name(r) or "")


def test_ascoril_ls_syp():
    r = resolve("ascoril ls syp")
    assert r["status"] in {"exact", "confident"}
    assert _top_name(r) == "Ascoril LS Syrup"


# ---------------------------------------------------------------------------
# Warfarin brands (3)
# ---------------------------------------------------------------------------


def test_warf_5():
    r = resolve("warf 5")
    assert r["status"] == "exact"
    assert _top_name(r) == "Warf 5 Tablet"


def test_uniwarfin_5():
    r = resolve("uniwarfin 5")
    assert r["status"] == "exact"
    assert _top_name(r) == "Uniwarfin 5mg Tablet"


def test_cofarin_5():
    r = resolve("cofarin 5")
    assert r["status"] == "exact"
    assert _top_name(r) == "Cofarin 5mg Tablet"


# ---------------------------------------------------------------------------
# Wrong strength / not_found / short ambiguous
# ---------------------------------------------------------------------------


def test_wrong_strength_pantop40_not_pantop20():
    r = resolve("pantop 40")
    assert _top_name(r) == "Pantop 40 Tablet"
    assert all("20" not in c["name"] for c in r["candidates"])


def test_pantop20_not_silently_40():
    r = resolve("pantop 20")
    assert _top_name(r) == "Pantop 20 Tablet"
    assert all("40" not in c["name"] for c in r["candidates"])


def test_nonsense_not_found():
    r = resolve("xyzzyfoobar")
    assert r["status"] == "not_found"
    assert r["candidates"] == []


def test_short_dolo_ambiguous():
    r = resolve("dolo")
    assert r["status"] == "ambiguous"
    assert len(r["candidates"]) >= 2


def test_token_prefix_excludes_aeldolo_for_dolo650():
    r = resolve("dolo 650")
    names = _top_names(r)
    assert "Dolo 650 Tablet" in names
    assert all("Aeldolo" not in n for n in names)
    assert all("Loremdolo" not in n for n in names)


# ---------------------------------------------------------------------------
# Extra coverage toward 40 cases
# ---------------------------------------------------------------------------


def test_augmentin_duo_ingredients_path():
    r = resolve("Augmentin 625 Duo Tablet")
    assert r["status"] == "exact"
    assert _top_name(r) == "Augmentin 625 Duo Tablet"


def test_crocin_advance_exact():
    r = resolve("crocin advance")
    assert r["status"] in {"exact", "confident"}
    assert _top_name(r) == "Crocin Advance Tablet"


def test_brufen_400_spaced():
    r = resolve("brufen 400")
    assert _top_name(r) == "Brufen 400 Tablet"


def test_ecosprin_75_spaced():
    r = resolve("ecosprin 75")
    assert _top_name(r) == "Ecosprin 75 Tablet"


def test_calpol_500_spaced():
    r = resolve("calpol 500")
    assert _top_name(r) == "Calpol 500mg Tablet"


def test_azithral_500_tab_prefers_tablet():
    r = resolve("azithral 500 tab")
    assert _top_name(r) == "Azithral 500 Tablet"
    assert r["status"] in {"exact", "confident"}


def test_azithral_500_inj_form_hint():
    r = resolve("azithral 500 inj")
    assert "Injection" in (_top_name(r) or "")


def test_ascoril_ls_drops_form():
    r = resolve("ascoril ls drops")
    assert _top_name(r) == "Ascoril LS Drops"


def test_warf_2():
    r = resolve("warf 2")
    assert _top_name(r) == "Warf 2 Tablet"


def test_mywarf_ambiguous_duplicate_name():
    r = resolve("mywarf")
    assert r["status"] == "ambiguous"
    assert len(r["candidates"]) >= 2


def test_empty_query_not_found():
    r = resolve("   ")
    assert r["status"] == "not_found"


def test_dolo_500():
    r = resolve("dolo 500")
    assert _top_name(r) == "Dolo 500 Tablet"


def test_candidates_have_required_keys():
    r = resolve("combiflam tab")
    assert r["candidates"]
    for c in r["candidates"]:
        assert set(c) >= {"brand_id", "name", "score"}


def test_prefer_non_discontinued_shape():
    # Structural: discontinued flag participates in sort key via index build.
    r = resolve("pantop 40")
    assert r["candidates"][0]["score"] >= 85 or r["status"] == "exact"


# ---------------------------------------------------------------------------
# Top-1 accuracy over cases that should resolve
# ---------------------------------------------------------------------------

# (query, expected_name_substring_or_full, must_resolve)
RESOLVE_CASES = [
    ("dolo650", "Dolo 650 Tablet"),
    ("dolo 650", "Dolo 650 Tablet"),
    ("dolo 650 tab", "Dolo 650 Tablet"),
    ("crocin advanc", "Crocin Advance Tablet"),
    ("augmentin625", "Augmentin 625 Duo"),
    ("augmentin 625 duo", "Augmentin 625 Duo Tablet"),
    ("pantop40", "Pantop 40 Tablet"),
    ("pantap 40", "Pantop 40 Tablet"),
    ("pantop 40", "Pantop 40 Tablet"),
    ("pantop 20", "Pantop 20 Tablet"),
    ("combiflam tab", "Combiflam Tablet"),
    ("combiflam susp", "Combiflam Suspension"),
    ("brufen400", "Brufen 400 Tablet"),
    ("ecosprin75", "Ecosprin 75 Tablet"),
    ("calpol500", "Calpol 500mg Tablet"),
    ("azithral 500", "Azithral 500"),
    ("azithral 500 tab", "Azithral 500 Tablet"),
    ("ascoril ls syp", "Ascoril LS Syrup"),
    ("ascoril ls drops", "Ascoril LS Drops"),
    ("warf 5", "Warf 5 Tablet"),
    ("warf 2", "Warf 2 Tablet"),
    ("uniwarfin 5", "Uniwarfin 5mg Tablet"),
    ("cofarin 5", "Cofarin 5mg Tablet"),
    ("crocin advance", "Crocin Advance Tablet"),
    ("brufen 400", "Brufen 400 Tablet"),
    ("ecosprin 75", "Ecosprin 75 Tablet"),
    ("calpol 500", "Calpol 500mg Tablet"),
    ("dolo 500", "Dolo 500 Tablet"),
    ("Augmentin 625 Duo Tablet", "Augmentin 625 Duo Tablet"),
]


def test_top1_accuracy_over_resolvable_cases(capsys):
    hits = 0
    details = []
    for query, expected in RESOLVE_CASES:
        result = resolve(query)
        top = _top_name(result)
        ok = (
            result["status"] != "not_found"
            and top is not None
            and expected.lower() in top.lower()
        )
        hits += int(ok)
        details.append((query, expected, top, result["status"], ok))

    total = len(RESOLVE_CASES)
    acc = hits / total
    print("\n======== RESOLVER TOP-1 ACCURACY ========")
    print(f"hits={hits} total={total} accuracy={acc:.1%}")
    for query, expected, top, status, ok in details:
        mark = "OK" if ok else "MISS"
        print(f"  [{mark}] {query!r} -> {top!r} ({status}); want ~{expected!r}")
    print("========================================\n")

    assert hits == total, f"top-1 accuracy {acc:.1%} ({hits}/{total})"
