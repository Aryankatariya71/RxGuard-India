"""Tests for src.rx_parser — 40 cases."""

from __future__ import annotations

from src.rx_parser import parse_line, parse_prescription


def _by_drug(items: list[dict], needle: str) -> dict:
    for item in items:
        if needle.lower() in item["drug_text"].lower():
            return item
    raise AssertionError(f"no item containing {needle!r}: {items}")


# ---------------------------------------------------------------------------
# Examples from the prompt
# ---------------------------------------------------------------------------


def test_tab_dolo_650_pattern_duration():
    items = parse_prescription("Tab Dolo 650 1-0-1 x 5 days")
    assert len(items) == 1
    i = items[0]
    assert i["drug_text"] == "Dolo 650"
    assert i["form_hint"] == "tablet"
    assert i["dose_amount"] == 1
    assert i["dose_unit"] == "tab"
    assert i["frequency_code"] == "1-0-1"
    assert i["times_per_day"] == 2
    assert i["duration_days"] == 5
    assert i["timing"] is None
    assert i["prn"] is False
    assert i["parse_error"] is None


def test_syp_ascoril_ls_ml_tds():
    i = parse_prescription("Syp Ascoril LS 5ml TDS x 5d")[0]
    assert i["drug_text"] == "Ascoril LS"
    assert i["form_hint"] == "syrup"
    assert i["dose_amount"] == 5
    assert i["dose_unit"] == "ml"
    assert i["frequency_code"] == "TDS"
    assert i["times_per_day"] == 3
    assert i["duration_days"] == 5


def test_tab_pantop_40_od_ac():
    i = parse_prescription("Tab Pantop 40 OD AC")[0]
    assert i["drug_text"] == "Pantop 40"
    assert i["frequency_code"] == "OD"
    assert i["times_per_day"] == 1
    assert i["timing"] == "AC"
    assert i["parse_error"] is None


def test_tab_crocin_sos():
    i = parse_prescription("Tab Crocin SOS")[0]
    assert i["drug_text"] == "Crocin"
    assert i["prn"] is True
    assert i["frequency_code"] == "SOS"
    assert i["times_per_day"] is None
    assert i["parse_error"] is None


def test_cap_omez_20_pattern_week():
    i = parse_prescription("Cap Omez 20 1-0-0 for 1 week")[0]
    assert i["drug_text"] == "Omez 20"
    assert i["form_hint"] == "capsule"
    assert i["dose_unit"] == "cap"
    assert i["frequency_code"] == "1-0-0"
    assert i["times_per_day"] == 1
    assert i["dose_amount"] == 1
    assert i["duration_days"] == 7


def test_inj_ceftriaxone_1g_bd():
    i = parse_prescription("Inj Ceftriaxone 1g BD")[0]
    assert i["drug_text"].lower().startswith("ceftriaxone")
    assert "1g" in i["drug_text"].lower().replace(" ", "")
    assert i["form_hint"] == "injection"
    assert i["dose_unit"] == "inj"
    assert i["frequency_code"] == "BD"
    assert i["times_per_day"] == 2


# ---------------------------------------------------------------------------
# Tricky / required extras
# ---------------------------------------------------------------------------


def test_tab_dolo_650_tds_no_duration():
    i = parse_prescription("Tab Dolo 650 TDS")[0]
    assert i["drug_text"] == "Dolo 650"
    assert i["frequency_code"] == "TDS"
    assert i["times_per_day"] == 3
    assert i["duration_days"] is None


def test_calpol_qid_pattern():
    i = parse_prescription("Tab Calpol 500 1-1-1-1 x 3 days")[0]
    assert i["drug_text"] == "Calpol 500"
    assert i["frequency_code"] == "1-1-1-1"
    assert i["times_per_day"] == 4
    assert i["dose_amount"] == 1
    assert i["duration_days"] == 3


def test_strength_not_confused_with_dose_dolo():
    i = parse_prescription("Tab Dolo 650 1-0-1")[0]
    assert i["drug_text"] == "Dolo 650"
    assert i["frequency_code"] == "1-0-1"


def test_strength_not_confused_pantop_40():
    i = parse_prescription("Tab Pantop 40 OD")[0]
    assert i["drug_text"] == "Pantop 40"
    assert i["dose_amount"] == 1


def test_half_tablet_pattern():
    i = parse_prescription("Tab Warf 5 0.5-0-0.5 x 7 days")[0]
    assert i["drug_text"] == "Warf 5"
    assert i["frequency_code"] == "0.5-0-0.5"
    assert i["times_per_day"] == 1
    assert i["dose_amount"] == 0.5
    assert i["duration_days"] == 7


def test_fraction_half_pattern():
    i = parse_prescription("Tab Foo 1/2-0-1/2")[0]
    assert i["times_per_day"] == 1
    assert i["dose_amount"] == 0.5
    assert i["frequency_code"] == "1/2-0-1/2"


def test_pattern_0_0_1_hs_night():
    i = parse_prescription("Tab Amitone 0-0-1")[0]
    assert i["frequency_code"] == "0-0-1"
    assert i["times_per_day"] == 1
    assert i["dose_amount"] == 1


def test_pattern_0_1_0():
    i = parse_prescription("Tab Something 0-1-0")[0]
    assert i["frequency_code"] == "0-1-0"
    assert i["times_per_day"] == 1


def test_pattern_1_1_1():
    i = parse_prescription("Tab Bar 10 1-1-1 x 5 days")[0]
    assert i["drug_text"] == "Bar 10"
    assert i["times_per_day"] == 3
    assert i["duration_days"] == 5


# ---------------------------------------------------------------------------
# Frequency codes & typos
# ---------------------------------------------------------------------------


def test_bd_with_dots():
    i = parse_prescription("Tab Augmentin 625 B.D")[0]
    assert i["frequency_code"] == "BD"
    assert i["times_per_day"] == 2
    assert "Augmentin 625" in i["drug_text"]


def test_tds_with_trailing_dot():
    i = parse_prescription("Tab Combiflam tds.")[0]
    assert i["frequency_code"] == "TDS"
    assert i["times_per_day"] == 3


def test_bid_alias():
    i = parse_prescription("Cap Amox BID")[0]
    assert i["frequency_code"] == "BD"
    assert i["times_per_day"] == 2


def test_qid():
    i = parse_prescription("Tab Paracetamol QID")[0]
    assert i["frequency_code"] == "QID"
    assert i["times_per_day"] == 4


def test_q6h():
    i = parse_prescription("Tab Painkill Q6H")[0]
    assert i["frequency_code"] == "Q6H"
    assert i["times_per_day"] == 4


def test_q8h():
    i = parse_prescription("Inj Antibiotic Q8H")[0]
    assert i["frequency_code"] == "Q8H"
    assert i["times_per_day"] == 3


def test_q12h():
    i = parse_prescription("Tab Slowrelease Q12H")[0]
    assert i["times_per_day"] == 2


def test_q4h():
    i = parse_prescription("Tab Fever Q4H")[0]
    assert i["times_per_day"] == 6


def test_once_daily_phrase():
    i = parse_prescription("Tab Telmisartan 40 once daily")[0]
    assert i["frequency_code"] == "OD"
    assert i["times_per_day"] == 1
    assert i["drug_text"] == "Telmisartan 40"


def test_twice_daily_phrase():
    i = parse_prescription("Tab Metformin 500 twice daily")[0]
    assert i["frequency_code"] == "BD"
    assert i["times_per_day"] == 2


def test_thrice_daily_phrase():
    i = parse_prescription("Syp Cough thrice daily")[0]
    assert i["frequency_code"] == "TDS"
    assert i["times_per_day"] == 3


def test_hs_sets_timing_and_once():
    i = parse_prescription("Tab Zolpidem 10 HS")[0]
    assert i["frequency_code"] == "HS"
    assert i["times_per_day"] == 1
    assert i["timing"] == "HS"


def test_od_pc_timing():
    i = parse_prescription("Tab Metformin 500 OD PC")[0]
    assert i["timing"] == "PC"
    assert i["frequency_code"] == "OD"


# ---------------------------------------------------------------------------
# Duration variants
# ---------------------------------------------------------------------------


def test_duration_two_weeks():
    i = parse_prescription("Tab Iron OD x 2 weeks")[0]
    assert i["duration_days"] == 14


def test_duration_one_month():
    i = parse_prescription("Tab Calcium OD for 1 month")[0]
    assert i["duration_days"] == 30


def test_duration_5d_compact():
    i = parse_prescription("Tab Dolo 650 TDS 5d")[0]
    assert i["duration_days"] == 5


# ---------------------------------------------------------------------------
# Multi-line, bullets, headers, errors
# ---------------------------------------------------------------------------


def test_multiline_skips_rx_and_blanks():
    text = """
Rx
1. Tab Dolo 650 1-0-1 x 5 days
2) Syp Ascoril LS 5ml TDS x 5d

- Tab Pantop 40 OD AC
"""
    items = parse_prescription(text)
    assert len(items) == 3
    assert items[0]["drug_text"] == "Dolo 650"
    assert items[1]["drug_text"] == "Ascoril LS"
    assert items[2]["drug_text"] == "Pantop 40"


def test_frequency_missing_keeps_line():
    i = parse_prescription("Tab Unknownzyme 10")[0]
    assert i["drug_text"] == "Unknownzyme 10"
    assert i["times_per_day"] is None
    assert i["frequency_code"] is None
    assert i["parse_error"] == "frequency missing"


def test_prn_if_needed():
    i = parse_prescription("Tab Crocin if needed")[0]
    assert i["prn"] is True
    assert i["times_per_day"] is None
    assert i["parse_error"] is None


def test_extra_spaces_case_insensitive():
    i = parse_prescription("  TAB   dolo   650   tds   x   5   DAYS  ")[0]
    assert i["drug_text"].lower() == "dolo 650"
    assert i["frequency_code"] == "TDS"
    assert i["duration_days"] == 5


def test_ml_dose_with_space():
    i = parse_prescription("Syp Ascoril LS 10 ml BD x 3 days")[0]
    assert i["dose_amount"] == 10
    assert i["dose_unit"] == "ml"
    assert i["drug_text"] == "Ascoril LS"


def test_never_drop_unknown_but_marked():
    items = parse_prescription("Totally weird line without structure")
    assert len(items) == 1
    assert items[0]["parse_error"] == "frequency missing"
    assert items[0]["drug_text"]


def test_raw_preserved():
    raw = "Tab Dolo 650 1-0-1 x 5 days"
    i = parse_prescription(raw)[0]
    assert i["raw"] == raw


def test_parse_line_skips_header():
    assert parse_line("Rx") is None
    assert parse_line("  ") is None


def test_susp_form_and_qid_code():
    i = parse_prescription("Susp Combiflam 5ml QID x 2 days")[0]
    assert i["form_hint"] == "suspension"
    assert i["dose_amount"] == 5
    assert i["dose_unit"] == "ml"
    assert i["frequency_code"] == "QID"
    assert i["times_per_day"] == 4
    assert i["duration_days"] == 2
    assert i["drug_text"] == "Combiflam"
