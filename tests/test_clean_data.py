"""Tests for src.clean_data."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

from src.clean_data import OUT_PARQUET, clean_brands, collapse_whitespace, detect_form

ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = ROOT / "data" / "Extensive_A_Z_medicines_dataset_of_India.csv"


@pytest.fixture(scope="module")
def cleaned_df() -> pd.DataFrame:
    if OUT_PARQUET.exists():
        return pd.read_parquet(OUT_PARQUET)
    raw = pd.read_csv(RAW_CSV)
    cleaned, _ = clean_brands(raw)
    return cleaned


def test_no_duplicate_ids(cleaned_df: pd.DataFrame) -> None:
    assert cleaned_df["id"].isna().sum() == 0
    assert cleaned_df["id"].duplicated().sum() == 0


def test_no_null_names(cleaned_df: pd.DataFrame) -> None:
    assert cleaned_df["name"].isna().sum() == 0
    assert (cleaned_df["name"].astype(str).str.len() == 0).sum() == 0


def test_form_never_null(cleaned_df: pd.DataFrame) -> None:
    assert cleaned_df["form"].isna().sum() == 0
    allowed = {"tablet", "capsule", "syrup", "suspension", "drops", "injection", "cream", "other"}
    assert set(cleaned_df["form"].unique()).issubset(allowed)


def test_composition_no_leading_trailing_or_double_spaces(cleaned_df: pd.DataFrame) -> None:
    double_space = re.compile(r"  ")
    for col in ("short_composition1", "short_composition2", "name"):
        series = cleaned_df[col].dropna().astype(str)
        assert (series != series.str.strip()).sum() == 0, f"{col} has leading/trailing spaces"
        assert series.map(lambda s: bool(double_space.search(s))).sum() == 0, (
            f"{col} has double spaces"
        )


def test_collapse_whitespace() -> None:
    assert collapse_whitespace("  Foo   Bar  ") == "Foo Bar"
    assert pd.isna(collapse_whitespace(None))
    assert pd.isna(collapse_whitespace(float("nan")))


def test_detect_form_prefers_pack_size_label() -> None:
    assert detect_form("bottle of 100 ml Syrup", "Something Tablet") == "syrup"
    assert detect_form("strip of 10 capsules", "Mystery Med") == "capsule"
    assert detect_form("unknown pack", "Brufen Cream") == "cream"
    assert detect_form("mystery", "Mystery Med") == "other"
