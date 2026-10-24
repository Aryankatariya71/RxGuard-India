"""Brand-name resolver for Indian medicines (rapidfuzz + deterministic rules)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
from rapidfuzz import fuzz, process
from rapidfuzz.distance import Levenshtein

ROOT = Path(__file__).resolve().parent.parent
PARQUET_PATH = ROOT / "data" / "brands_clean.parquet"

_WHITESPACE_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_LETTER_DIGIT_RE = re.compile(r"([a-z])(\d)", re.IGNORECASE)
_DIGIT_LETTER_RE = re.compile(r"(\d)([a-z])", re.IGNORECASE)
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")

FORM_WORD_TO_HINT: dict[str, str] = {
    "tab": "tablet",
    "tablet": "tablet",
    "cap": "capsule",
    "capsule": "capsule",
    "syp": "syrup",
    "syrup": "syrup",
    "inj": "injection",
    "injection": "injection",
    "susp": "suspension",
    "suspension": "suspension",
    "drops": "drops",
    "oint": "cream",
    "ointment": "cream",
    "cream": "cream",
}

FORM_TOKENS = frozenset(FORM_WORD_TO_HINT.keys()) | frozenset(FORM_WORD_TO_HINT.values())
UNIT_TOKENS = frozenset({"mg", "mcg", "ml", "gm", "g", "iu", "kg"})

CONFIDENT_MIN = 85.0
NOT_FOUND_MAX = 55.0
CLOSE_SCORE_GAP = 3.0


@dataclass(frozen=True)
class BrandRecord:
    brand_id: int
    name: str
    name_norm: str
    name_core: str
    tokens: tuple[str, ...]
    core_tokens: tuple[str, ...]
    form: str
    is_discontinued: bool
    numbers: tuple[str, ...]
    ingredients_key: tuple[str, ...]


def _collapse(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def _split_letter_digit(text: str) -> str:
    text = _LETTER_DIGIT_RE.sub(r"\1 \2", text)
    text = _DIGIT_LETTER_RE.sub(r"\1 \2", text)
    return _collapse(text)


def _tokenize(text: str) -> list[str]:
    return [t for t in _collapse(text).split(" ") if t]


def _extract_numbers(tokens: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    found: list[str] = []
    for tok in tokens:
        found.extend(_NUMBER_RE.findall(tok))
    return tuple(found)


def _strip_trailing_form(tokens: list[str]) -> list[str]:
    out = list(tokens)
    while out and out[-1] in FORM_TOKENS:
        out.pop()
    return out


def _content_tokens(tokens: list[str] | tuple[str, ...]) -> list[str]:
    return [t for t in tokens if t not in FORM_TOKENS and t not in UNIT_TOKENS]


def normalize_query(query: str) -> dict[str, Any]:
    """Normalize a user query and extract form_hint + tokens."""
    q = str(query).lower()
    q = _PUNCT_RE.sub(" ", q)
    q = _split_letter_digit(q)
    tokens = _tokenize(q)

    form_hint: str | None = None
    kept: list[str] = []
    for tok in tokens:
        if tok in FORM_WORD_TO_HINT:
            form_hint = FORM_WORD_TO_HINT[tok]
            continue
        if tok in UNIT_TOKENS:
            continue
        kept.append(tok)

    return {
        "query_norm": " ".join(kept),
        "tokens": kept,
        "form_hint": form_hint,
        "numbers": list(_extract_numbers(kept)),
    }


def _ingredient_key(comp1: Any, comp2: Any) -> tuple[str, ...]:
    parts: list[str] = []
    for value in (comp1, comp2):
        if value is None or (isinstance(value, float) and pd.isna(value)):
            continue
        text = _collapse(str(value)).lower()
        if text:
            parts.append(text)
    return tuple(parts)


def _prepare_name(name_norm: str) -> tuple[str, tuple[str, ...], tuple[str, ...], str]:
    cleaned = _PUNCT_RE.sub(" ", name_norm.lower())
    split = _split_letter_digit(cleaned)
    tokens = tuple(_tokenize(split))
    core_toks = tuple(_content_tokens(_strip_trailing_form(list(tokens))))
    core = " ".join(core_toks)
    return split, tokens, core_toks, core


@lru_cache(maxsize=1)
def get_brand_index(parquet_path: str | None = None) -> dict[str, Any]:
    """Load parquet once and build in-memory lookup structures."""
    path = Path(parquet_path) if parquet_path else PARQUET_PATH
    df = pd.read_parquet(path)

    records: list[BrandRecord] = []
    by_norm: dict[str, list[BrandRecord]] = {}
    by_core: dict[str, list[BrandRecord]] = {}
    by_first: dict[str, list[BrandRecord]] = {}
    core_choices: list[str] = []
    core_to_records: dict[str, list[BrandRecord]] = {}

    for row in df.itertuples(index=False):
        name_norm = str(row.name_norm)
        split, tokens, core_toks, core = _prepare_name(name_norm)
        rec = BrandRecord(
            brand_id=int(row.id),
            name=str(row.name),
            name_norm=name_norm,
            name_core=core,
            tokens=tokens,
            core_tokens=core_toks,
            form=str(row.form),
            is_discontinued=bool(row.is_discontinued),
            numbers=_extract_numbers(tokens),
            ingredients_key=_ingredient_key(
                getattr(row, "short_composition1", None),
                getattr(row, "short_composition2", None),
            ),
        )
        records.append(rec)
        by_norm.setdefault(name_norm, []).append(rec)
        by_norm.setdefault(split, []).append(rec)
        if core:
            by_core.setdefault(core, []).append(rec)
            if core not in core_to_records:
                core_choices.append(core)
            core_to_records.setdefault(core, []).append(rec)
        if core_toks:
            by_first.setdefault(core_toks[0], []).append(rec)

    return {
        "records": records,
        "by_norm": by_norm,
        "by_core": by_core,
        "by_first": by_first,
        "core_choices": core_choices,
        "core_to_records": core_to_records,
    }


def clear_brand_index_cache() -> None:
    get_brand_index.cache_clear()


def _combined_score(a: str, b: str, **_kwargs: Any) -> float:
    """Blend WRatio + token_set; add plain ratio to reduce short-string bias."""
    return (
        float(fuzz.WRatio(a, b))
        + float(fuzz.token_set_ratio(a, b))
        + float(fuzz.ratio(a, b))
    ) / 3.0


def _first_token_score(query_token: str, candidate_token: str) -> float:
    """First-token similarity with length penalty (prefer substitution over truncation)."""
    base = float(fuzz.ratio(query_token, candidate_token))
    penalty = abs(len(query_token) - len(candidate_token)) * 10.0
    return max(0.0, base - penalty)


def _first_token_edit(query_token: str, candidate_token: str) -> int:
    return int(Levenshtein.distance(query_token, candidate_token))


def _numbers_compatible(query_numbers: list[str], candidate_numbers: tuple[str, ...]) -> bool:
    if not query_numbers:
        return True
    cand = set(candidate_numbers)
    return all(n in cand for n in query_numbers)


def _sort_key(rec: BrandRecord, score: float, form_hint: str | None) -> tuple:
    form_rank = 0 if (form_hint and rec.form == form_hint) else 1
    disc_rank = 0 if not rec.is_discontinued else 1
    return (-score, form_rank, disc_rank, rec.brand_id)


def _dedupe_keep_best(
    scored: list[tuple[BrandRecord, float]],
    form_hint: str | None,
) -> list[tuple[BrandRecord, float]]:
    best: dict[int, tuple[BrandRecord, float]] = {}
    for rec, score in scored:
        prev = best.get(rec.brand_id)
        if prev is None or _sort_key(rec, score, form_hint) < _sort_key(
            prev[0], prev[1], form_hint
        ):
            best[rec.brand_id] = (rec, score)
    return sorted(best.values(), key=lambda x: _sort_key(x[0], x[1], form_hint))


def _candidate_dicts(scored: list[tuple[BrandRecord, float]], top_n: int) -> list[dict]:
    return [
        {
            "brand_id": rec.brand_id,
            "name": rec.name,
            "score": round(float(score), 2),
        }
        for rec, score in scored[:top_n]
    ]


def _different_ingredients(a: BrandRecord, b: BrandRecord) -> bool:
    return a.ingredients_key != b.ingredients_key


def _is_token_prefix(query_tokens: list[str], rec: BrandRecord) -> bool:
    if not query_tokens:
        return False
    name_toks = list(rec.core_tokens)
    if len(query_tokens) > len(name_toks):
        return False
    return name_toks[: len(query_tokens)] == query_tokens


def _decide_status(
    scored: list[tuple[BrandRecord, float]],
    *,
    matched_exact: bool,
) -> str:
    if not scored:
        return "not_found"

    best_score = scored[0][1]
    if best_score < NOT_FOUND_MAX:
        return "not_found"
    if best_score < CONFIDENT_MIN:
        return "ambiguous"

    if len(scored) >= 2:
        gap = best_score - scored[1][1]
        if gap <= CLOSE_SCORE_GAP and _different_ingredients(scored[0][0], scored[1][0]):
            return "ambiguous"

    if matched_exact:
        return "exact"
    return "confident"


def _prefer_form(
    scored: list[tuple[BrandRecord, float]],
    form_hint: str | None,
) -> list[tuple[BrandRecord, float]]:
    if not form_hint:
        return scored
    matching = [(r, s) for r, s in scored if r.form == form_hint]
    return matching if matching else scored


def resolve(query: str, top_n: int = 3, parquet_path: str | None = None) -> dict:
    """
    Resolve a free-text brand query to catalog candidates.

    Returns:
      {status: exact|confident|ambiguous|not_found,
       candidates: [{brand_id, name, score}]}
    """
    index = get_brand_index(parquet_path)
    q = normalize_query(query)
    tokens: list[str] = q["tokens"]
    query_norm: str = q["query_norm"]
    form_hint: str | None = q["form_hint"]
    numbers: list[str] = q["numbers"]

    if not tokens:
        return {"status": "not_found", "candidates": []}

    # ------------------------------------------------------------------
    # 1) Exact match on name_norm / core (with or without trailing form)
    # ------------------------------------------------------------------
    exact_hits: list[BrandRecord] = []
    exact_hits.extend(index["by_norm"].get(query_norm, []))
    exact_hits.extend(index["by_core"].get(query_norm, []))
    # Also try with a reconstructed full name_norm ending in form_hint
    if form_hint:
        exact_hits.extend(index["by_norm"].get(f"{query_norm} {form_hint}", []))

    exact_scored = [
        (rec, 100.0)
        for rec in exact_hits
        if _numbers_compatible(numbers, rec.numbers)
    ]
    exact_scored = _dedupe_keep_best(exact_scored, form_hint)
    exact_scored = _prefer_form(exact_scored, form_hint)

    # ------------------------------------------------------------------
    # 2) Exact token-prefix match (before fuzzy)
    # ------------------------------------------------------------------
    prefix_pool: list[BrandRecord] = list(index["by_first"].get(tokens[0], []))
    prefix_scored = [
        (rec, 100.0)
        for rec in prefix_pool
        if _is_token_prefix(tokens, rec) and _numbers_compatible(numbers, rec.numbers)
    ]
    prefix_scored = _dedupe_keep_best(prefix_scored, form_hint)
    prefix_scored = _prefer_form(prefix_scored, form_hint)

    # Merge exact + prefix so short stems like "dolo" surface sibling strengths.
    stem_scored = _dedupe_keep_best(exact_scored + prefix_scored, form_hint)
    stem_scored = _prefer_form(stem_scored, form_hint)

    # Prefer exact core-token equality when the query is specific enough
    # (2+ tokens or has a strength number). Bare stems like "dolo" stay broad.
    if stem_scored and (len(tokens) >= 2 or numbers):
        exact_core = [
            (rec, score)
            for rec, score in stem_scored
            if list(rec.core_tokens) == tokens
        ]
        if exact_core:
            stem_scored = _prefer_form(
                _dedupe_keep_best(exact_core, form_hint),
                form_hint,
            )

    if stem_scored:
        matched_exact = bool(exact_scored) and len(stem_scored) == 1
        if (
            not matched_exact
            and exact_scored
            and len(tokens) >= 2
            and list(stem_scored[0][0].core_tokens) == tokens
        ):
            # Unique exact core among filtered hits (possibly same ingredients, multi-form)
            close_diff = [
                other
                for other in stem_scored[1:]
                if (stem_scored[0][1] - other[1]) <= CLOSE_SCORE_GAP
                and _different_ingredients(stem_scored[0][0], other[0])
            ]
            matched_exact = not close_diff

        status = _decide_status(stem_scored, matched_exact=matched_exact)
        return {
            "status": status,
            "candidates": _candidate_dicts(stem_scored, top_n),
        }

    # ------------------------------------------------------------------
    # 3) Fuzzy (WRatio + token_set_ratio), with number constraints
    # ------------------------------------------------------------------
    # Near first-token lookup (ratio, not WRatio — WRatio matches tiny substrings).
    first_tokens = list(index["by_first"].keys())
    near = process.extract(
        tokens[0],
        first_tokens,
        scorer=fuzz.ratio,
        limit=40,
        score_cutoff=70,
    )
    fuzzy_pool_recs: list[BrandRecord] = []
    seen_ids: set[int] = set()
    q0 = tokens[0]
    for tok, _score, _ in near:
        # Drop extreme length mismatches (blocks "a"/"pan" false friends).
        if abs(len(tok) - len(q0)) > 2:
            continue
        for rec in index["by_first"].get(tok, []):
            if rec.brand_id not in seen_ids:
                fuzzy_pool_recs.append(rec)
                seen_ids.add(rec.brand_id)

    # Number hard-filter + first-token gate (blocks substring false friends).
    filtered: list[BrandRecord] = []
    for rec in fuzzy_pool_recs:
        if not _numbers_compatible(numbers, rec.numbers):
            continue
        if not rec.core_tokens:
            continue
        if _first_token_score(tokens[0], rec.core_tokens[0]) < 70.0:
            continue
        filtered.append(rec)
    fuzzy_pool_recs = filtered
    if not fuzzy_pool_recs:
        return {"status": "not_found", "candidates": []}

    # Deduplicate by name_core for extract, then map back
    core_map: dict[str, list[BrandRecord]] = {}
    for rec in fuzzy_pool_recs:
        core_map.setdefault(rec.name_core, []).append(rec)
    choices = list(core_map.keys())

    extracted = process.extract(
        query_norm,
        choices,
        scorer=_combined_score,
        limit=max(top_n * 5, 15),
        score_cutoff=NOT_FOUND_MAX,
    )

    fuzzy_scored: list[tuple[BrandRecord, float]] = []
    for core, score, _ in extracted:
        for rec in core_map[core]:
            ft = _first_token_score(tokens[0], rec.core_tokens[0])
            ed = _first_token_edit(tokens[0], rec.core_tokens[0])
            len_diff = abs(len(tokens[0]) - len(rec.core_tokens[0]))
            # Penalize truncation/length mismatch harder than substitution.
            adj = float(score) - (ed * 3.0) - (len_diff * 10.0)
            adj = 0.5 * adj + 0.5 * ft
            # Near-miss brand stems with matching strength should clear the
            # confident threshold (user rule: <85 => ambiguous).
            if ed <= 1 and len_diff <= 1 and numbers:
                adj = max(adj, 90.0)
            fuzzy_scored.append((rec, adj))

    # Tie-break: lower first-token edit distance, then equal length, then score.
    fuzzy_scored = _dedupe_keep_best(fuzzy_scored, form_hint)

    def _fuzzy_tie_key(item: tuple[BrandRecord, float]) -> tuple:
        rec, score = item
        ed = _first_token_edit(tokens[0], rec.core_tokens[0])
        len_diff = abs(len(tokens[0]) - len(rec.core_tokens[0]))
        form_rank = 0 if (form_hint and rec.form == form_hint) else 1
        disc_rank = 0 if not rec.is_discontinued else 1
        return (ed, len_diff, -score, form_rank, disc_rank, rec.brand_id)

    fuzzy_scored = sorted(fuzzy_scored, key=_fuzzy_tie_key)
    fuzzy_scored = _prefer_form(fuzzy_scored, form_hint)

    if not fuzzy_scored:
        return {"status": "not_found", "candidates": []}

    status = _decide_status(fuzzy_scored, matched_exact=False)
    return {
        "status": status,
        "candidates": _candidate_dicts(fuzzy_scored, top_n),
    }
