"""Synthetic prescription stress test — in-memory only, never persists reports."""

from __future__ import annotations

import time
from collections import Counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.app.core.config import get_settings
from backend.app.models.entities import Product, ProductIngredient
from backend.app.services.dosage_engine import evaluate_dosage
from backend.app.services.duplicate_detector import detect_duplicates
from backend.app.services.interaction_engine import evaluate_interactions

MAX_N = 2000
DEFAULT_N = 500
ALLOWED_N = (100, 500, 1000, 2000)
FREQUENCIES = (
    ("OD", 1.0, "per_day"),
    ("BD", 2.0, "per_day"),
    ("TDS", 3.0, "per_day"),
    ("QID", 4.0, "per_day"),
    ("HS", 1.0, "per_day"),
    ("SOS", None, "prn"),
)
CAPTION = (
    "Synthetic data, for performance and alert-load demonstration only. "
    "Not clinical accuracy."
)


class _Rng:
    """Minimal deterministic RNG (avoids global random state)."""

    def __init__(self, seed: int) -> None:
        self._s = seed % (2**31 - 1)
        if self._s <= 0:
            self._s = 1

    def randint(self, a: int, b: int) -> int:
        # Park–Miller LCG
        self._s = (self._s * 48271) % 2147483647
        return a + (self._s % (b - a + 1))

    def choice(self, seq: list[Any]) -> Any:
        return seq[self.randint(0, len(seq) - 1)]

    def sample(self, seq: list[Any], k: int) -> list[Any]:
        pool = list(seq)
        out: list[Any] = []
        for _ in range(min(k, len(pool))):
            i = self.randint(0, len(pool) - 1)
            out.append(pool.pop(i))
        return out

    def uniform(self, a: float, b: float) -> float:
        self._s = (self._s * 48271) % 2147483647
        t = self._s / 2147483647.0
        return a + (b - a) * t


def _product_pool(db: Session, limit: int = 800) -> list[Product]:
    rows = list(
        db.scalars(
            select(Product)
            .options(
                joinedload(Product.ingredients).joinedload(ProductIngredient.ingredient)
            )
            .where(Product.is_discontinued.is_(False))
            .limit(limit)
        )
        .unique()
        .all()
    )
    return [p for p in rows if p.ingredients]


def _payload_from_product(product: Product, freq: tuple) -> dict[str, Any]:
    code, fval, funit = freq
    ings = []
    dose_amount = None
    dose_unit = None
    for pi in product.ingredients or []:
        if not pi.ingredient or not pi.active_flag:
            continue
        ings.append({"id": pi.ingredient_id, "name": pi.ingredient.canonical_name})
        if dose_amount is None and pi.strength_value is not None:
            dose_amount = pi.strength_value
            dose_unit = pi.strength_unit or "mg"
    return {
        "item_id": product.id,
        "product_id": product.id,
        "brand_name": product.brand_name,
        "identity_status": "VERIFIED_CATALOGUE_MATCH",
        "resolution_status": "resolved",
        "ingredients": ings,
        "dose_amount": dose_amount,
        "dose_unit": dose_unit,
        "frequency_value": fval,
        "frequency_unit": funit if fval is not None else "prn",
        "duration_value": 5.0,
        "duration_unit": "day",
        "route": product.route or "oral",
        "frequency_code": code,
    }


def _merge_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Dedupe + tier collapse similar to report merging (same category+ingredients)."""
    by_key: dict[str, dict[str, Any]] = {}
    severity_rank = {
        "CRITICAL": 3,
        "HIGH": 2,
        "MODERATE": 1,
        "INFORMATIONAL": 0,
        "LOW": 0,
    }
    for f in findings:
        ings = tuple(sorted(f.get("affected_ingredient_ids") or []))
        key = f"{f.get('category')}|{ings}|{f.get('finding_code')}"
        if key not in by_key:
            by_key[key] = dict(f)
            continue
        cur = by_key[key]
        if severity_rank.get(f.get("severity"), 0) > severity_rank.get(
            cur.get("severity"), 0
        ):
            by_key[key] = dict(f)
    return list(by_key.values())


def run_stress_test(
    db: Session,
    *,
    n: int = DEFAULT_N,
    seed: int | None = None,
) -> dict[str, Any]:
    if n not in ALLOWED_N:
        n = min(ALLOWED_N, key=lambda x: abs(x - n))
    n = min(max(n, 1), MAX_N)

    if seed is None:
        seed = int(time.time()) % (2**31 - 1)
    rng = _Rng(int(seed))

    pool = _product_pool(db)
    if len(pool) < 2:
        return {
            "ok": False,
            "error": "Need at least 2 catalogue products to stress-test",
            "seed": seed,
            "n": n,
            "caption": CAPTION,
        }

    settings = get_settings()
    rule_ver = settings.rule_set_version

    t0 = time.perf_counter()
    had_dup = 0
    had_int = 0
    had_dose = 0
    had_unresolved = 0
    had_check_not_run = 0
    naive_hist: Counter[int] = Counter()
    merged_hist: Counter[int] = Counter()

    # Process in chunks so a long run yields between batches (cooperative)
    chunk = 50
    for start in range(0, n, chunk):
        end = min(start + chunk, n)
        for _ in range(start, end):
            k = rng.randint(2, min(6, len(pool)))
            picks = rng.sample(pool, k)
            payloads = []
            for p in picks:
                freq = rng.choice(list(FREQUENCIES))
                payloads.append(_payload_from_product(p, freq))

            age = float(rng.randint(1, 90))
            # ~5% inject an unresolved synthetic line
            unresolved_items: list[dict[str, Any]] = []
            if rng.randint(1, 20) == 1:
                unresolved_items.append(
                    {
                        "item_id": "unresolved-synth",
                        "product_id": None,
                        "brand_name": "Unknown Brand Synth",
                        "identity_status": "UNRESOLVED",
                        "resolution_status": "unresolved",
                        "ingredients": [],
                        "dose_amount": None,
                        "dose_unit": None,
                        "frequency_value": 1.0,
                        "frequency_unit": "per_day",
                    }
                )
                had_unresolved += 1

            resolved = [p for p in payloads if p["resolution_status"] == "resolved"]
            findings: list[dict[str, Any]] = []
            findings.extend(detect_duplicates(resolved))
            findings.extend(evaluate_interactions(db, resolved, rule_ver))
            findings.extend(
                evaluate_dosage(db, resolved, age_years=age, rule_set_version=rule_ver)
            )
            for u in unresolved_items:
                findings.append(
                    {
                        "finding_code": "UNRESOLVED",
                        "category": "UNRESOLVED_PRODUCT",
                        "severity": "INFORMATIONAL",
                        "affected_ingredient_ids": [],
                        "evaluation_status": "UNRESOLVED",
                    }
                )

            naive_n = len(findings)
            merged = _merge_findings(findings)
            merged_n = len(merged)
            naive_hist[naive_n] += 1
            merged_hist[merged_n] += 1

            cats = {f.get("category") for f in findings}
            if "DUPLICATE_INGREDIENT" in cats:
                had_dup += 1
            if "DRUG_DRUG_INTERACTION" in cats:
                had_int += 1
            if any(
                c
                in {
                    "DOSE_OUTSIDE_CONFIGURED_RANGE",
                    "FREQUENCY_OUTSIDE_CONFIGURED_RANGE",
                    "DURATION_OUTSIDE_CONFIGURED_RANGE",
                    "UNIT_MISMATCH",
                    "INSUFFICIENT_DOSAGE_INFORMATION",
                }
                for c in cats
            ):
                had_dose += 1
            if any(
                f.get("evaluation_status")
                in {"NOT_EVALUATED", "INSUFFICIENT_DATA", "UNRESOLVED"}
                or f.get("category") == "CHECK_NOT_RUN"
                for f in findings
            ):
                had_check_not_run += 1

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    pps = (n / (elapsed_ms / 1000.0)) if elapsed_ms > 0 else 0.0

    def _hist_to_series(counter: Counter[int], max_bin: int = 20) -> list[dict[str, int]]:
        return [{"alerts": k, "count": counter[k]} for k in range(0, max_bin + 1) if counter[k]]

    return {
        "ok": True,
        "seed": seed,
        "n": n,
        "elapsed_ms": round(elapsed_ms, 2),
        "prescriptions_per_second": round(pps, 2),
        "had_duplicates": had_dup,
        "had_interactions": had_int,
        "had_dose_rule_matches": had_dose,
        "had_unresolved_items": had_unresolved,
        "had_check_not_run": had_check_not_run,
        "alerts_per_prescription": {
            "naive": _hist_to_series(naive_hist),
            "rxguard_merged": _hist_to_series(merged_hist),
            "naive_mean": round(sum(k * v for k, v in naive_hist.items()) / n, 3),
            "merged_mean": round(sum(k * v for k, v in merged_hist.items()) / n, 3),
        },
        "caption": CAPTION,
        "note": "Reports are not persisted. Seed is reproducible when passed back.",
    }
