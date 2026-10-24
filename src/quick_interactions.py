"""Minimal Major-only DDInter pair lookup for the Streamlit demo."""

from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from pathlib import Path
from typing import Iterable

import pandas as pd

from src.composition import normalize_ingredient

ROOT = Path(__file__).resolve().parent.parent
DDINTER_DIR = ROOT / "data" / "ddinter"

_EXTRA_ALIASES = {
    "acetylsalicylic acid": "aspirin",
    "acetaminophen": "paracetamol",
}


def _norm_ddinter_name(name: str) -> str:
    base = normalize_ingredient(str(name))
    return _EXTRA_ALIASES.get(base, base)


@lru_cache(maxsize=1)
def load_major_pairs() -> frozenset[tuple[str, str]]:
    """
    Load Major DDInter pairs once.

    Returns unordered (sorted) normalized ingredient pairs.
    """
    paths = sorted(DDINTER_DIR.glob("ddinter_downloads_code_*.csv"))
    if not paths:
        return frozenset()

    frames = [pd.read_csv(p, usecols=["Drug_A", "Drug_B", "Level"]) for p in paths]
    df = pd.concat(frames, ignore_index=True)
    major = df[df["Level"].astype(str).str.strip().str.lower() == "major"].copy()

    pairs: set[tuple[str, str]] = set()
    for a_raw, b_raw in zip(major["Drug_A"], major["Drug_B"], strict=False):
        a = _norm_ddinter_name(a_raw)
        b = _norm_ddinter_name(b_raw)
        if not a or not b or a == b:
            continue
        pairs.add(tuple(sorted((a, b))))
    return frozenset(pairs)


def major_pair_count() -> int:
    return len(load_major_pairs())


def check_major_interactions(ingredient_names: Iterable[str]) -> list[dict]:
    """
    Return Major DDInter hits among DISTINCT prescription ingredients.

    Each hit: {ing_a, ing_b, level: "Major", source: "DDInter 2.0"}
    """
    names = sorted(
        {
            _norm_ddinter_name(n)
            for n in ingredient_names
            if n is not None and str(n).strip()
        }
    )
    # Drop empty after normalize
    names = [n for n in names if n]
    if len(names) < 2:
        return []

    catalog = load_major_pairs()
    hits: list[dict] = []
    for a, b in combinations(names, 2):
        key = tuple(sorted((a, b)))
        if key in catalog:
            hits.append(
                {
                    "ing_a": key[0],
                    "ing_b": key[1],
                    "level": "Major",
                    "source": "DDInter 2.0",
                }
            )
    return hits
