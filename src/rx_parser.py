"""Parse typed Indian outpatient prescriptions into structured line items."""

from __future__ import annotations

import re
from typing import Any

_WHITESPACE_RE = re.compile(r"\s+")

# Leading bullets / numbering: "1.", "1)", "-", "*", "•"
_BULLET_RE = re.compile(r"^\s*(?:[-*•]+|\d+[.)\]])\s*")

_HEADER_RE = re.compile(
    r"^(?:rx|prescription|medicines?|drugs?|rx:)\s*$",
    re.IGNORECASE,
)

_FORM_RE = re.compile(
    r"^(?P<form>tab(?:let)?s?|cap(?:sule)?s?|syp|syrup|inj(?:ection)?s?|"
    r"susp(?:ension)?|drops?|oint(?:ment)?)\b[\s.:\-]*",
    re.IGNORECASE,
)

_FORM_HINT = {
    "tab": "tablet",
    "tablet": "tablet",
    "tablets": "tablet",
    "cap": "capsule",
    "capsule": "capsule",
    "capsules": "capsule",
    "syp": "syrup",
    "syrup": "syrup",
    "inj": "injection",
    "injection": "injection",
    "injections": "injection",
    "susp": "suspension",
    "suspension": "suspension",
    "drop": "drops",
    "drops": "drops",
    "oint": "cream",
    "ointment": "cream",
}

_DOSE_UNIT = {
    "tablet": "tab",
    "capsule": "cap",
    "syrup": "ml",
    "suspension": "ml",
    "drops": "ml",
    "injection": "inj",
    "cream": "tab",  # unused for cream dosing here
}

# Duration: x 5 days | for 1 week | 5d | x 2 weeks | 1 month | for 10 days
_DURATION_RE = re.compile(
    r"(?P<full>"
    r"(?:\b(?:x|for)\s*)?"
    r"(?P<num>\d+(?:\.\d+)?)\s*"
    r"(?P<unit>days?|d\b|weeks?|wks?|w\b|months?|mths?|m\b)"
    r")\s*$",
    re.IGNORECASE,
)

_DURATION_DAYS = {
    "d": 1,
    "day": 1,
    "days": 1,
    "w": 7,
    "wk": 7,
    "wks": 7,
    "week": 7,
    "weeks": 7,
    "m": 30,
    "mth": 30,
    "mths": 30,
    "month": 30,
    "months": 30,
}

# Timing tokens (standalone; HS also doubles as frequency)
_TIMING_RE = re.compile(r"\b(?P<timing>AC|PC|HS)\b", re.IGNORECASE)

# Explicit PRN / SOS
_PRN_RE = re.compile(
    r"\b(?P<code>SOS|PRN|STAT)\b|\bif\s+needed\b|\bas\s+needed\b",
    re.IGNORECASE,
)

# Classic frequency codes (allow optional dots already stripped)
_FREQ_CODE_RE = re.compile(
    r"\b(?P<code>"
    r"QID|QDS|TDS|TID|BID|BD|OD|"
    r"Q4H|Q6H|Q8H|Q12H|"
    r"ONCE\s+DAILY|TWICE\s+DAILY|THRICE\s+DAILY|THREE\s+TIMES\s+DAILY|"
    r"TWICE\s+A\s+DAY|ONCE\s+A\s+DAY"
    r")\b",
    re.IGNORECASE,
)

_FREQ_TIMES = {
    "od": 1,
    "bd": 2,
    "bid": 2,
    "tds": 3,
    "tid": 3,
    "qid": 4,
    "qds": 4,
    "q4h": 6,
    "q6h": 4,
    "q8h": 3,
    "q12h": 2,
    "once daily": 1,
    "once a day": 1,
    "twice daily": 2,
    "twice a day": 2,
    "thrice daily": 3,
    "three times daily": 3,
    "hs": 1,
}

# Dose schedule patterns: 1-0-1, 1-1-1-1, 0.5-0-0.5, 1/2-0-1/2
# Fractions must win over bare digits so "1/2-0-1/2" is not read as "1/2-0-1".
_SLOT_RE = r"(?:\d+\s*/\s*\d+|\d+(?:\.\d+)?)"
_PATTERN_RE = re.compile(
    rf"(?<![\w./])(?P<pat>{_SLOT_RE}\s*-\s*{_SLOT_RE}\s*-\s*{_SLOT_RE}"
    rf"(?:\s*-\s*{_SLOT_RE})?)(?![\w./])"
)

# Volume dose for syrups: 5ml, 10 ml (not 650mg / 1g strength)
_ML_DOSE_RE = re.compile(
    r"(?<![A-Za-z])(?P<amt>\d+(?:\.\d+)?)\s*ml\b",
    re.IGNORECASE,
)


def _collapse(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def _normalize_rx_typos(text: str) -> str:
    """Handle B.D, tds., O.D., etc."""
    s = text
    # Collapse letter-dot-letter abbreviations: B.D / B.D. -> BD
    s = re.sub(r"\b([A-Za-z])\.(?=[A-Za-z])", r"\1", s)
    # Trailing dot on short alpha tokens: tds. -> tds
    s = re.sub(r"\b([A-Za-z]{1,8})\.(?=\s|$)", r"\1", s)
    return _collapse(s)


def _parse_slot(token: str) -> float:
    token = token.strip()
    if "/" in token:
        num, den = token.split("/", 1)
        return float(num.strip()) / float(den.strip())
    return float(token)


def _parse_duration(text: str) -> tuple[str, int | None]:
    match = _DURATION_RE.search(text)
    if not match:
        return text, None
    num = float(match.group("num"))
    unit_raw = match.group("unit").lower().rstrip(".")
    # Normalize unit key
    unit = unit_raw
    if unit_raw in _DURATION_DAYS:
        mult = _DURATION_DAYS[unit_raw]
    else:
        # strip plural already handled; fallback
        mult = _DURATION_DAYS.get(unit_raw.rstrip("s"), 1)
        if unit_raw.endswith("s") and unit_raw[:-1] in _DURATION_DAYS:
            mult = _DURATION_DAYS[unit_raw[:-1]]
    days = int(num * mult) if num * mult == int(num * mult) else int(round(num * mult))
    cleaned = _collapse(text[: match.start()] + " " + text[match.end() :])
    return cleaned, days


def _extract_form(text: str) -> tuple[str, str | None, str]:
    """Return (remainder, form_hint, dose_unit)."""
    match = _FORM_RE.match(text)
    if not match:
        return text, None, "tab"
    key = match.group("form").lower()
    hint = _FORM_HINT.get(key, _FORM_HINT.get(key.rstrip("s"), None))
    unit = _DOSE_UNIT.get(hint or "", "tab")
    rest = text[match.end() :]
    return _collapse(rest), hint, unit


def _extract_prn(text: str) -> tuple[str, bool, str | None]:
    match = _PRN_RE.search(text)
    if not match:
        return text, False, None
    code = match.group("code")
    if code:
        code = code.upper()
    elif re.search(r"if\s+needed|as\s+needed", match.group(0), re.IGNORECASE):
        code = "PRN"
    else:
        code = "PRN"
    cleaned = _collapse(text[: match.start()] + " " + text[match.end() :])
    return cleaned, True, code


def _extract_timing(text: str) -> tuple[str, str | None]:
    # Prefer AC/PC over HS when multiple; HS handled with frequency too.
    timing = None
    cleaned = text
    for match in list(_TIMING_RE.finditer(text)):
        tok = match.group("timing").upper()
        if tok in {"AC", "PC"}:
            timing = tok
            cleaned = _collapse(cleaned[: match.start()] + " " + cleaned[match.end() :])
        elif tok == "HS" and timing is None:
            # Leave HS in text for frequency extraction unless AC/PC already set
            pass
    return cleaned, timing


def _extract_pattern(text: str) -> tuple[str, str | None, float | None, float | None]:
    match = _PATTERN_RE.search(text)
    if not match:
        return text, None, None, None
    parts = [p.strip() for p in re.split(r"\s*-\s*", match.group("pat")) if p.strip()]
    values = [_parse_slot(p) for p in parts]
    times = float(sum(values))
    dose = float(max(values)) if values else 1.0
    code = "-".join(re.sub(r"\s+", "", p) for p in parts)
    cleaned = _collapse(text[: match.start()] + " " + text[match.end() :])
    return cleaned, code, times, dose


def _extract_freq_code(text: str) -> tuple[str, str | None, float | None, str | None]:
    """Extract OD/BD/TDS/... or HS. Returns timing override for HS."""
    match = _FREQ_CODE_RE.search(text)
    timing_from_freq = None
    if not match:
        # HS as frequency
        hs = re.search(r"\bHS\b", text, re.IGNORECASE)
        if hs:
            cleaned = _collapse(text[: hs.start()] + " " + text[hs.end() :])
            return cleaned, "HS", 1.0, "HS"
        return text, None, None, None

    code_raw = _collapse(match.group("code")).upper()
    code_key = code_raw.lower()
    times = _FREQ_TIMES.get(code_key)
    cleaned = _collapse(text[: match.start()] + " " + text[match.end() :])
    # Canonical short codes
    canon = {
        "once daily": "OD",
        "once a day": "OD",
        "twice daily": "BD",
        "twice a day": "BD",
        "thrice daily": "TDS",
        "three times daily": "TDS",
        "bid": "BD",
        "tid": "TDS",
        "qds": "QID",
    }.get(code_key, code_raw)
    return cleaned, canon, float(times) if times is not None else None, timing_from_freq


def _extract_ml_dose(text: str) -> tuple[str, float | None]:
    match = _ML_DOSE_RE.search(text)
    if not match:
        return text, None
    amt = float(match.group("amt"))
    cleaned = _collapse(text[: match.start()] + " " + text[match.end() :])
    return cleaned, amt


def _empty_item(raw: str, **overrides: Any) -> dict:
    base = {
        "raw": raw,
        "drug_text": "",
        "form_hint": None,
        "dose_amount": 1.0,
        "dose_unit": "tab",
        "frequency_code": None,
        "times_per_day": None,
        "duration_days": None,
        "timing": None,
        "prn": False,
        "parse_error": None,
    }
    base.update(overrides)
    return base


def parse_line(line: str) -> dict | None:
    """Parse a single prescription line. Returns None for blank/header lines."""
    raw = line.rstrip("\n")
    text = _BULLET_RE.sub("", raw).strip()
    if not text:
        return None
    if _HEADER_RE.match(text):
        return None

    text = _normalize_rx_typos(text)
    rest, form_hint, dose_unit = _extract_form(text)

    if not rest:
        return _empty_item(
            raw,
            form_hint=form_hint,
            dose_unit=dose_unit,
            parse_error="drug name missing",
        )

    rest, duration_days = _parse_duration(rest)
    rest, prn, prn_code = _extract_prn(rest)
    rest, timing = _extract_timing(rest)

    # Pattern before word codes so "1-0-1" wins over stray digits
    rest, pattern_code, pattern_times, pattern_dose = _extract_pattern(rest)
    freq_code = pattern_code
    times_per_day = pattern_times
    dose_amount = 1.0
    if pattern_dose is not None and pattern_dose > 0:
        dose_amount = pattern_dose

    if freq_code is None:
        rest, code, times, hs_timing = _extract_freq_code(rest)
        freq_code = code
        times_per_day = times
        if hs_timing and timing is None:
            timing = hs_timing

    if prn:
        freq_code = freq_code or prn_code or "PRN"
        times_per_day = None

    rest, ml_dose = _extract_ml_dose(rest)
    if ml_dose is not None:
        dose_amount = ml_dose
        dose_unit = "ml"

    drug_text = _collapse(rest)

    parse_error = None
    if not drug_text:
        parse_error = "drug name missing"
    elif freq_code is None and not prn:
        parse_error = "frequency missing"

    # Normalize integer-looking floats for cleaner output
    def _num(v: float | None) -> float | int | None:
        if v is None:
            return None
        if isinstance(v, float) and v == int(v):
            return int(v)
        return v

    return {
        "raw": raw,
        "drug_text": drug_text,
        "form_hint": form_hint,
        "dose_amount": _num(dose_amount) if dose_amount is not None else 1,
        "dose_unit": dose_unit,
        "frequency_code": freq_code,
        "times_per_day": _num(times_per_day),
        "duration_days": duration_days,
        "timing": timing,
        "prn": prn,
        "parse_error": parse_error,
    }


def parse_prescription(text: str) -> list[dict]:
    """
    Parse a multi-line typed prescription into structured medicine items.

    Never drops a medicine line: missing frequency becomes parse_error.
    Blank lines and Rx headers are skipped.
    """
    if text is None:
        return []
    items: list[dict] = []
    for line in str(text).splitlines():
        parsed = parse_line(line)
        if parsed is not None:
            items.append(parsed)
    return items
