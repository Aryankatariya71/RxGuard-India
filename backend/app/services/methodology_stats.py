"""Live methodology / evaluation stats for the Methodology page.

Never invent counts. Missing data → null (JSON null), not 0 or placeholders.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from backend.app.core.config import ROOT, get_settings
from backend.app.models.entities import (
    DoseRule,
    Ingredient,
    InteractionRule,
    Product,
    ProductIngredient,
)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
GOLD_PATH = ROOT / "tests" / "gold_prescriptions.json"
EVAL_REPORT_PATH = ROOT / "docs" / "EVAL_REPORT.md"


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _status_breakdown(rows: list[Any]) -> dict[str, int | None]:
    if not rows:
        return {
            "DEMO_ILLUSTRATIVE": 0,
            "REVIEW_PENDING": 0,
            "CLINICALLY_REVIEWED": 0,
            "other": 0,
            "total": 0,
        }
    c = Counter(getattr(r, "status", None) or "other" for r in rows)
    return {
        "DEMO_ILLUSTRATIVE": int(c.get("DEMO_ILLUSTRATIVE", 0)),
        "REVIEW_PENDING": int(c.get("REVIEW_PENDING", 0)),
        "CLINICALLY_REVIEWED": int(c.get("CLINICALLY_REVIEWED", 0)),
        "other": int(
            sum(
                v
                for k, v in c.items()
                if k
                not in {
                    "DEMO_ILLUSTRATIVE",
                    "REVIEW_PENDING",
                    "CLINICALLY_REVIEWED",
                }
            )
        ),
        "total": int(sum(c.values())),
    }


def _tier_breakdown(rows: list[InteractionRule]) -> dict[str, int]:
    c = Counter((r.severity or "unknown").lower() for r in rows)
    return {k: int(v) for k, v in sorted(c.items())}


def _count_tests_live() -> dict[str, int | None]:
    """Prefer generated meta; fall back to counting test files on disk."""
    meta = _read_json(DATA_DIR / "methodology_build_meta.json")
    if meta and meta.get("backend_test_function_count") is not None:
        return {
            "backend_test_function_count": meta.get("backend_test_function_count"),
            "backend_test_file_count": meta.get("backend_test_file_count"),
        }
    n = 0
    files = 0
    for root in (ROOT / "tests", ROOT / "backend" / "tests"):
        if not root.exists():
            continue
        for p in root.rglob("test_*.py"):
            files += 1
            text = p.read_text(encoding="utf-8", errors="ignore")
            n += len(re.findall(r"^def test_", text, re.M))
            n += len(re.findall(r"^async def test_", text, re.M))
    if files == 0:
        return {"backend_test_function_count": None, "backend_test_file_count": None}
    return {"backend_test_function_count": n, "backend_test_file_count": files}


def _catalogue_file_stats() -> dict[str, int | None]:
    cached = _read_json(DATA_DIR / "catalogue_file_stats.json") or {}
    out = {
        "source_csv_rows": cached.get("source_csv_rows"),
        "cleaned_parquet_rows": cached.get("cleaned_parquet_rows"),
        "ddinter_pairs_loaded": cached.get("ddinter_pairs_loaded"),
    }
    # Live refresh when files exist (null stays null if missing)
    csv = ROOT / "data" / "Extensive_A_Z_medicines_dataset_of_India.csv"
    if csv.exists():
        try:
            with csv.open("rb") as f:
                lines = sum(1 for _ in f)
            out["source_csv_rows"] = max(0, lines - 1)
        except OSError:
            pass
    pq = ROOT / "data" / "brands_clean.parquet"
    if pq.exists() and out.get("cleaned_parquet_rows") is None:
        try:
            import pandas as pd

            out["cleaned_parquet_rows"] = int(len(pd.read_parquet(pq)))
        except Exception:
            pass
    dd = ROOT / "data" / "rules" / "ddinter_pairs.parquet"
    if dd.exists() and out.get("ddinter_pairs_loaded") is None:
        try:
            import pandas as pd

            out["ddinter_pairs_loaded"] = int(len(pd.read_parquet(dd)))
        except Exception:
            pass
    return out


def _gold_stats() -> dict[str, Any]:
    if not GOLD_PATH.exists():
        return {
            "gold_case_count": None,
            "developer_labeled_count": None,
            "pharmacist_verified_count": None,
            "composition": None,
        }
    try:
        gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "gold_case_count": None,
            "developer_labeled_count": None,
            "pharmacist_verified_count": None,
            "composition": None,
        }
    if not isinstance(gold, list):
        return {
            "gold_case_count": None,
            "developer_labeled_count": None,
            "pharmacist_verified_count": None,
            "composition": None,
        }
    developer = sum(1 for g in gold if (g.get("labeled_by") or "developer") == "developer")
    verified = sum(1 for g in gold if g.get("verified_by"))
    by_prefix: Counter[str] = Counter()
    for g in gold:
        gid = str(g.get("id") or "")
        prefix = gid.split("-")[0] if "-" in gid else "other"
        by_prefix[prefix] += 1
    return {
        "gold_case_count": len(gold),
        "developer_labeled_count": developer,
        "pharmacist_verified_count": verified,
        "composition": dict(by_prefix),
    }


def _parse_eval_report() -> dict[str, Any] | None:
    if not EVAL_REPORT_PATH.exists():
        return None
    try:
        text = EVAL_REPORT_PATH.read_text(encoding="utf-8")
    except OSError:
        return None
    out: dict[str, Any] = {"report_path": "docs/EVAL_REPORT.md", "raw_available": True}
    m = re.search(r"Cases:\s*(\d+)", text)
    out["cases"] = int(m.group(1)) if m else None
    m = re.search(r"Brand-resolution accuracy:\s*([\d.]+)\s*\((\d+)/(\d+)\)", text)
    if m:
        out["brand_resolution_accuracy"] = float(m.group(1))
        out["brand_resolution_hits"] = int(m.group(2))
        out["brand_resolution_total"] = int(m.group(3))
    else:
        out["brand_resolution_accuracy"] = None
        out["brand_resolution_hits"] = None
        out["brand_resolution_total"] = None
    m = re.search(
        r"False-alarm rate on clean prescriptions[^:]*:\s*([\d.]+)\s*\((\d+)/(\d+)\)",
        text,
    )
    if m:
        out["false_alarm_rate_clean"] = float(m.group(1))
        out["false_alarm_count"] = int(m.group(2))
        out["clean_case_count"] = int(m.group(3))
    else:
        out["false_alarm_rate_clean"] = None
        out["false_alarm_count"] = None
        out["clean_case_count"] = None
    m = re.search(r"Average alerts per prescription:\s*([\d.]+)", text)
    out["avg_alerts_per_prescription"] = float(m.group(1)) if m else None
    # Parse precision/recall table rows
    per_type: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 6 or parts[0] in {"type", "---"}:
            continue
        try:
            per_type.append(
                {
                    "type": parts[0],
                    "precision": float(parts[1]),
                    "recall": float(parts[2]),
                    "tp": int(parts[3]),
                    "fp": int(parts[4]),
                    "fn": int(parts[5]),
                }
            )
        except ValueError:
            continue
    out["precision_recall_by_type"] = per_type or None
    out["disclaimer"] = (
        "Labels were written by the development team from the same rule set, "
        "so these figures show internal consistency, not clinical accuracy. "
        "Pharmacist verification is the next step."
    )
    return out


def composition_examples(db: Session, limit: int = 3) -> list[dict[str, Any]] | None:
    """Real brand → ingredient expansions from the local DB."""
    q = (
        select(Product)
        .options(selectinload(Product.ingredients).selectinload(ProductIngredient.ingredient))
        .where(Product.is_synthetic.is_(False))
        .limit(80)
    )
    products = list(db.scalars(q).unique().all())
    if not products:
        # fall back to any products including synthetic
        products = list(
            db.scalars(
                select(Product)
                .options(
                    selectinload(Product.ingredients).selectinload(ProductIngredient.ingredient)
                )
                .limit(80)
            ).unique().all()
        )
    examples: list[dict[str, Any]] = []
    for p in products:
        links = [l for l in (p.ingredients or []) if l.active_flag]
        if not links:
            continue
        parts = []
        for link in links:
            ing = link.ingredient
            name = ing.canonical_name if ing else "?"
            if link.strength_value is not None:
                unit = link.strength_unit or ""
                parts.append(f"{name} {link.strength_value}{unit}".strip())
            else:
                parts.append(name)
        examples.append(
            {
                "brand_name": p.brand_name,
                "strength_label": p.strength_label,
                "dosage_form": p.dosage_form,
                "before": p.brand_name
                + (f" ({p.strength_label})" if p.strength_label else ""),
                "after": parts,
                "ingredient_count": len(parts),
                "incomplete_flag": any(l.incomplete_flag for l in links),
                "source": p.source,
                "verification_status": p.verification_status,
            }
        )
        if len(examples) >= limit:
            break
    return examples or None


def build_methodology_stats(db: Session) -> dict[str, Any]:
    settings = get_settings()
    products = int(db.scalar(select(func.count()).select_from(Product)) or 0)
    ingredients = int(db.scalar(select(func.count()).select_from(Ingredient)) or 0)
    incomplete = int(
        db.scalar(
            select(func.count())
            .select_from(ProductIngredient)
            .where(ProductIngredient.incomplete_flag.is_(True))
        )
        or 0
    )

    interactions = list(db.scalars(select(InteractionRule)).all())
    doses = list(db.scalars(select(DoseRule)).all())
    file_stats = _catalogue_file_stats()
    tests = _count_tests_live()
    gold = _gold_stats()
    evaluation = _parse_eval_report()

    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "engine_version": settings.engine_version,
        "dataset_version": settings.dataset_version,
        "catalogue_version": settings.catalogue_version,
        "rule_set_version": settings.rule_set_version,
        "demo_mode": settings.demo_mode,
        "products_in_db": products if products > 0 else None,
        "ingredients_in_db": ingredients if ingredients > 0 else None,
        "incomplete_composition_links": incomplete if products > 0 else None,
        "catalogue_files": file_stats,
        "interaction_rules": {
            "by_status": _status_breakdown(interactions),
            "by_severity": _tier_breakdown(interactions) if interactions else None,
            "active": sum(1 for r in interactions if r.active),
            "synthetic": sum(1 for r in interactions if r.is_synthetic),
        },
        "dose_rules": {
            "by_status": _status_breakdown(doses),
            "active": sum(1 for r in doses if r.active),
            "synthetic": sum(1 for r in doses if r.is_synthetic),
        },
        "ddinter_pairs_loaded": file_stats.get("ddinter_pairs_loaded"),
        "tests": tests,
        "gold": gold,
        "evaluation": evaluation,
        "composition_examples": composition_examples(db, 3),
        "alert_fatigue": {
            "naive_alert_count": None,
            "merged_alert_count": None,
            "note": "Run POST /api/stress-test to measure naive vs merged alert counts.",
            "stress_test_path": "/stress-test",
        },
        "disclaimer": (
            "RxGuard India is a prescription-review support prototype. "
            "It does not replace a doctor or pharmacist. "
            "A missing alert does not prove a prescription is safe. "
            "Verify findings with a qualified healthcare professional."
        ),
        "rule_status_note": (
            "Today most rules are REVIEW_PENDING or DEMO_ILLUSTRATIVE. "
            "CLINICALLY_REVIEWED counts reflect pharmacist verification when present."
        ),
    }


def build_meta(db: Session) -> dict[str, Any]:
    stats = build_methodology_stats(db)
    return {
        "app_name": stats["app_name"],
        "app_version": stats["app_version"],
        "engine_version": stats["engine_version"],
        "dataset_version": stats["dataset_version"],
        "catalogue_version": stats["catalogue_version"],
        "rule_set_version": stats["rule_set_version"],
        "demo_mode": stats["demo_mode"],
        "products_in_db": stats["products_in_db"],
        "ingredients_in_db": stats["ingredients_in_db"],
        "ddinter_pairs_loaded": stats["ddinter_pairs_loaded"],
        "interaction_rules_total": (stats["interaction_rules"]["by_status"] or {}).get(
            "total"
        ),
        "dose_rules_total": (stats["dose_rules"]["by_status"] or {}).get("total"),
        "backend_test_function_count": (stats["tests"] or {}).get(
            "backend_test_function_count"
        ),
        "disclaimer": stats["disclaimer"],
    }


def build_evaluation(db: Session) -> dict[str, Any]:
    stats = build_methodology_stats(db)
    return {
        "gold": stats["gold"],
        "evaluation": stats["evaluation"],
        "tests": stats["tests"],
        "disclaimer": (
            "Labels were written by the development team from the same rule set, "
            "so these figures show internal consistency, not clinical accuracy. "
            "Pharmacist verification is the next step."
        ),
    }
