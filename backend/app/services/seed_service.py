"""Idempotent seed: synthetic demo, optional catalogue, optional rules import."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.core.constants import (
    CATALOGUE_SOURCE_LABEL,
    DDINTER_SOURCE_LABEL,
    map_legacy_rule_status,
)
from backend.app.models.entities import (
    ApplicationSetting,
    DoseRule,
    Ingredient,
    InteractionRule,
    Product,
    ProductIngredient,
)

ROOT = Path(__file__).resolve().parents[3]
SEED_DIR = ROOT / "backend" / "seed"
DATA_DIR = ROOT / "data"

INCOMPLETE_NAME_HINTS = re.compile(
    r"\b(plus|forte|cold|d3|d-3|forte|mr|er|sr|xr|combo)\b",
    re.IGNORECASE,
)


def _load_json(name: str) -> Any:
    return json.loads((SEED_DIR / name).read_text(encoding="utf-8"))


def _set_setting(db: Session, key: str, value: str) -> None:
    row = db.scalars(
        select(ApplicationSetting).where(ApplicationSetting.setting_key == key)
    ).first()
    if row:
        row.setting_value = value
    else:
        db.add(ApplicationSetting(setting_key=key, setting_value=value))


def seed_demo(db: Session) -> dict[str, int]:
    """Load synthetic demo ingredients/products/rules. Idempotent by stable IDs / rule_code."""
    counts = {"ingredients": 0, "products": 0, "links": 0, "interactions": 0, "dose_rules": 0}

    for row in _load_json("demo_ingredients.json"):
        existing = db.get(Ingredient, row["id"])
        if existing:
            continue
        db.add(
            Ingredient(
                id=row["id"],
                canonical_name=row["canonical_name"],
                normalized_name=row["normalized_name"],
                synonyms=row.get("synonyms"),
                status=row.get("status", "DEMO_ILLUSTRATIVE"),
                source=row.get("source"),
                dataset_version=row.get("dataset_version", "demo-1.0"),
                is_synthetic=True,
            )
        )
        counts["ingredients"] += 1

    for row in _load_json("demo_medicines.json"):
        existing = db.get(Product, row["id"])
        if existing:
            continue
        db.add(
            Product(
                id=row["id"],
                brand_name=row["brand_name"],
                normalized_name=row["normalized_name"],
                manufacturer=row.get("manufacturer"),
                strength_label=row.get("strength_label"),
                dosage_form=row.get("dosage_form"),
                route=row.get("route"),
                identity_status=row.get("identity_status", "VERIFIED_CATALOGUE_MATCH"),
                source=row.get("source"),
                source_version=row.get("source_version", "demo-1.0"),
                is_synthetic=True,
            )
        )
        counts["products"] += 1
        for link in row.get("ingredients") or []:
            exists_link = db.scalars(
                select(ProductIngredient).where(
                    ProductIngredient.product_id == row["id"],
                    ProductIngredient.ingredient_id == link["ingredient_id"],
                )
            ).first()
            if exists_link:
                continue
            db.add(
                ProductIngredient(
                    product_id=row["id"],
                    ingredient_id=link["ingredient_id"],
                    strength_value=link.get("strength_value"),
                    strength_unit=link.get("strength_unit"),
                    active_flag=True,
                    source="Synthetic demo dataset",
                    incomplete_flag=bool(link.get("incomplete_flag")),
                )
            )
            counts["links"] += 1

    for row in _load_json("demo_interactions.json"):
        a, b = sorted([row["ingredient_a_id"], row["ingredient_b_id"]])
        exists = db.scalars(
            select(InteractionRule).where(InteractionRule.rule_code == row["rule_code"])
        ).first()
        if exists:
            continue
        db.add(
            InteractionRule(
                rule_code=row["rule_code"],
                ingredient_a_id=a,
                ingredient_b_id=b,
                category=row.get("category", "drug_drug"),
                severity=row["severity"],
                description=row["description"],
                action=row["action"],
                evidence_source=row.get("evidence_source"),
                evidence_reference=row.get("evidence_reference"),
                version=row.get("version", "demo-1.0"),
                status="DEMO_ILLUSTRATIVE",
                reviewed_at=None,
                active=True,
                is_synthetic=True,
            )
        )
        counts["interactions"] += 1

    for row in _load_json("demo_dose_rules.json"):
        exists = db.scalars(
            select(DoseRule).where(DoseRule.rule_code == row["rule_code"])
        ).first()
        if exists:
            continue
        db.add(
            DoseRule(
                rule_code=row["rule_code"],
                scope_type=row.get("scope_type", "ingredient"),
                ingredient_id=row.get("ingredient_id"),
                patient_criteria_json=json.dumps(row.get("patient_criteria") or {}),
                dose_criteria_json=json.dumps(row.get("dose_criteria") or {}),
                required_fields_json=json.dumps(row.get("required_fields") or []),
                result_type=row.get("result_type", "unable_to_assess_if_missing"),
                explanation=row["explanation"],
                source=row.get("source"),
                version=row.get("version", "demo-1.0"),
                status="DEMO_ILLUSTRATIVE",
                dose_max=row.get("dose_max"),
                dose_unit=row.get("dose_unit"),
                severity=row.get("severity", "INFORMATIONAL"),
                active=True,
                is_synthetic=True,
            )
        )
        counts["dose_rules"] += 1

    settings = get_settings()
    _set_setting(db, "demo_mode", "true" if settings.demo_mode else "false")
    _set_setting(db, "dataset_version", settings.dataset_version)
    _set_setting(db, "engine_version", settings.engine_version)
    db.commit()
    return counts


def _maybe_incomplete(brand_name: str) -> bool:
    return bool(INCOMPLETE_NAME_HINTS.search(brand_name or ""))


def seed_catalogue(db: Session, *, limit: int | None = None) -> dict[str, int]:
    """Import brands_clean.parquet into products/ingredients. Idempotent by external id prefix."""
    import pandas as pd

    from src.composition import expand_brand, load_combo_overrides

    path = DATA_DIR / "brands_clean.parquet"
    if not path.exists():
        return {"skipped": 1, "products": 0, "ingredients": 0, "links": 0}

    df = pd.read_parquet(path)
    if limit is not None:
        df = df.head(limit)

    overrides = load_combo_overrides()

    counts = {"products": 0, "ingredients": 0, "links": 0}
    ing_cache: dict[str, str] = {}

    for ing in db.scalars(select(Ingredient)).all():
        ing_cache[ing.normalized_name] = ing.id

    for _, row in df.iterrows():
        ext_id = f"cat-{row.get('id')}"
        if db.get(Product, ext_id):
            continue

        brand = str(row.get("name") or "").strip()
        if not brand:
            continue
        name_norm = str(row.get("name_norm") or brand.lower()).strip()
        incomplete = _maybe_incomplete(brand)

        try:
            comps = expand_brand(row, overrides)
        except Exception:
            comps = []

        db.add(
            Product(
                id=ext_id,
                brand_name=brand,
                normalized_name=name_norm,
                manufacturer=(
                    str(row["manufacturer_name"])
                    if pd.notna(row.get("manufacturer_name"))
                    else None
                ),
                strength_label=None,
                dosage_form=(str(row["form"]) if pd.notna(row.get("form")) else None),
                route="oral",
                identity_status="VERIFIED_CATALOGUE_MATCH",
                source=CATALOGUE_SOURCE_LABEL,
                source_version="brands_clean.parquet",
                is_discontinued=(
                    bool(row.get("is_discontinued"))
                    if pd.notna(row.get("is_discontinued"))
                    else False
                ),
                is_synthetic=False,
            )
        )
        counts["products"] += 1

        strength_parts: list[str] = []
        for comp in comps or []:
            cname = (
                comp.get("ingredient_full")
                or comp.get("ingredient")
                or comp.get("canonical_name")
                or ""
            ).strip()
            if not cname:
                continue
            nname = cname.lower().strip()
            if nname not in ing_cache:
                iid = f"ing-{abs(hash(nname)) % (10**12)}"
                while (
                    db.get(Ingredient, iid)
                    and db.get(Ingredient, iid).normalized_name != nname
                ):
                    iid = f"ing-{abs(hash(nname + iid)) % (10**12)}"
                if not db.get(Ingredient, iid):
                    db.add(
                        Ingredient(
                            id=iid,
                            canonical_name=cname,
                            normalized_name=nname,
                            status="REVIEW_PENDING",
                            source=CATALOGUE_SOURCE_LABEL,
                            dataset_version="catalogue-v1",
                            is_synthetic=False,
                        )
                    )
                    counts["ingredients"] += 1
                ing_cache[nname] = iid

            iid = ing_cache[nname]
            sval = comp.get("strength_value")
            sunit = comp.get("unit")
            if sval is not None:
                strength_parts.append(f"{cname} {sval} {sunit or ''}".strip())

            exists_link = db.scalars(
                select(ProductIngredient).where(
                    ProductIngredient.product_id == ext_id,
                    ProductIngredient.ingredient_id == iid,
                )
            ).first()
            if not exists_link:
                db.add(
                    ProductIngredient(
                        product_id=ext_id,
                        ingredient_id=iid,
                        strength_value=float(sval) if sval is not None else None,
                        strength_unit=sunit,
                        per_value=comp.get("per_value"),
                        per_unit=comp.get("per_unit"),
                        source=CATALOGUE_SOURCE_LABEL,
                        incomplete_flag=incomplete,
                        active_flag=True,
                    )
                )
                counts["links"] += 1

        prod = db.get(Product, ext_id)
        if prod and strength_parts:
            prod.strength_label = " + ".join(strength_parts)

        if counts["products"] % 2000 == 0:
            db.commit()

    _set_setting(db, "catalogue_version", "catalogue-v1")
    _set_setting(db, "catalogue_source", CATALOGUE_SOURCE_LABEL)
    db.commit()
    return counts


def _tier_to_severity(tier: str | None) -> str:
    t = (tier or "").lower()
    if t == "critical":
        return "CRITICAL"
    if t == "review":
        return "HIGH"
    if t == "info":
        return "INFORMATIONAL"
    return "MODERATE"


def seed_rules(db: Session) -> dict[str, int]:
    """Import curated interactions, DDInter pairs (sample-safe), and max_dose into dose_rules."""
    counts = {"interactions": 0, "dose_rules": 0, "ingredients_ensured": 0}

    def ensure_ing(name: str) -> str:
        n = name.strip().lower()
        existing = db.scalars(
            select(Ingredient).where(Ingredient.normalized_name == n)
        ).first()
        if existing:
            return existing.id
        iid = f"ing-rule-{abs(hash(n)) % (10**12)}"
        if not db.get(Ingredient, iid):
            db.add(
                Ingredient(
                    id=iid,
                    canonical_name=name.strip(),
                    normalized_name=n,
                    status="REVIEW_PENDING",
                    source="rules import",
                    dataset_version="rules-v1",
                    is_synthetic=False,
                )
            )
            counts["ingredients_ensured"] += 1
            db.flush()
        return iid

    curated_path = DATA_DIR / "rules" / "curated_interactions.json"
    if curated_path.exists():
        for row in json.loads(curated_path.read_text(encoding="utf-8")):
            code = row.get("id") or f"CUR-{row.get('ingredient_a')}-{row.get('ingredient_b')}"
            if db.scalars(select(InteractionRule).where(InteractionRule.rule_code == code)).first():
                continue
            a = ensure_ing(row["ingredient_a"])
            b = ensure_ing(row["ingredient_b"])
            a_id, b_id = sorted([a, b])
            status = map_legacy_rule_status(
                status=row.get("status"),
                verified_by_pharmacist=bool(row.get("verified_by_pharmacist")),
            )
            db.add(
                InteractionRule(
                    rule_code=code,
                    ingredient_a_id=a_id,
                    ingredient_b_id=b_id,
                    category="drug_drug",
                    severity=_tier_to_severity(row.get("tier")),
                    description=row.get("mechanism") or "Interaction rule (source pending review).",
                    action=row.get("recommended_action") or "Seek pharmacist/clinician review.",
                    evidence_source=row.get("source_url") or "source not recorded",
                    evidence_reference=code,
                    version="rules-v1",
                    status=status,
                    reviewed_at=None,
                    active=True,
                    is_synthetic=False,
                )
            )
            counts["interactions"] += 1

    # DDInter pairs — import up to a capped set to keep local demo practical
    dd_path = DATA_DIR / "rules" / "ddinter_pairs.parquet"
    if dd_path.exists():
        import pandas as pd

        ddf = pd.read_parquet(dd_path)
        # Cap for Stage 1 local seed speed; full set can be re-imported later
        for _, row in ddf.head(5000).iterrows():
            a_name = str(row.get("ingredient_a") or row.get("drug_a") or "").strip()
            b_name = str(row.get("ingredient_b") or row.get("drug_b") or "").strip()
            if not a_name or not b_name:
                continue
            code = str(row.get("id") or f"DDI-{a_name}-{b_name}")[:64]
            if db.scalars(select(InteractionRule).where(InteractionRule.rule_code == code)).first():
                continue
            a = ensure_ing(a_name)
            b = ensure_ing(b_name)
            a_id, b_id = sorted([a, b])
            db.add(
                InteractionRule(
                    rule_code=code,
                    ingredient_a_id=a_id,
                    ingredient_b_id=b_id,
                    category="drug_drug",
                    severity=_tier_to_severity(str(row.get("tier") or row.get("level") or "review")),
                    description=str(row.get("description") or "DDInter-derived pair (academic use)."),
                    action="Review with a clinician/pharmacist. Academic dataset — not clinically validated here.",
                    evidence_source=DDINTER_SOURCE_LABEL,
                    evidence_reference=code,
                    version="ddinter-import-v1",
                    status="REVIEW_PENDING",
                    reviewed_at=None,
                    active=True,
                    is_synthetic=False,
                )
            )
            counts["interactions"] += 1

    dose_path = DATA_DIR / "rules" / "max_dose.json"
    if dose_path.exists():
        for row in json.loads(dose_path.read_text(encoding="utf-8")):
            code = row.get("id") or f"MAX-{row.get('ingredient')}"
            if db.scalars(select(DoseRule).where(DoseRule.rule_code == code)).first():
                continue
            iid = ensure_ing(row["ingredient"])
            status = map_legacy_rule_status(
                status=row.get("status"),
                verified_by_pharmacist=bool(row.get("verified_by_pharmacist")),
            )
            required = ["dose_amount", "dose_unit", "frequency_structured", "age_years"]
            criteria = {
                "adult_max_mg_day": row.get("adult_max_mg_day"),
                "pediatric_mg_per_kg_day": row.get("pediatric_mg_per_kg_day"),
                "renal_adjustment": row.get("renal_adjustment"),
                "elderly_note": row.get("elderly_note"),
            }
            db.add(
                DoseRule(
                    rule_code=code,
                    scope_type="ingredient",
                    ingredient_id=iid,
                    patient_criteria_json=json.dumps({"min_age_years": row.get("min_age_years")}),
                    dose_criteria_json=json.dumps(criteria),
                    required_fields_json=json.dumps(required),
                    result_type="potential_issue_or_unable",
                    explanation=(
                        row.get("notes")
                        or f"Configured daily-max style rule for {row.get('ingredient')} "
                        f"(status {status}). Not a universal maximum dose."
                    ),
                    source=row.get("source_url") or "source not recorded",
                    version="rules-v1",
                    status=status,
                    dose_max=row.get("adult_max_mg_day"),
                    dose_unit="mg",
                    severity="HIGH",
                    active=True,
                    is_synthetic=False,
                )
            )
            counts["dose_rules"] += 1

    _set_setting(db, "rule_set_version", "rules-v1")
    db.commit()
    return counts


def seed_all(db: Session, *, catalogue_limit: int | None = None) -> dict[str, Any]:
    settings = get_settings()
    summary: dict[str, Any] = {"demo": seed_demo(db)}
    if not settings.demo_mode:
        summary["catalogue"] = seed_catalogue(db, limit=catalogue_limit)
        summary["rules"] = seed_rules(db)
        _set_setting(db, "dataset_version", "catalogue-v1+rules-v1")
        _set_setting(db, "demo_mode", "false")
    else:
        _set_setting(db, "demo_mode", "true")
        _set_setting(db, "dataset_version", "demo-1.0")
    db.commit()
    summary["demo_mode"] = settings.demo_mode
    summary["totals"] = {
        "ingredients": db.scalar(select(func.count()).select_from(Ingredient)) or 0,
        "products": db.scalar(select(func.count()).select_from(Product)) or 0,
        "interaction_rules": db.scalar(select(func.count()).select_from(InteractionRule)) or 0,
        "dose_rules": db.scalar(select(func.count()).select_from(DoseRule)) or 0,
    }
    return summary
