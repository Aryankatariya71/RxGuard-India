"""Stage 1: clean migrate + seed is repeatable (idempotent)."""

from __future__ import annotations

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker

from backend.app.db.session import Base
from backend.app.models import entities  # noqa: F401
from backend.app.models.entities import DoseRule, Ingredient, InteractionRule, Product
from backend.app.services.seed_service import seed_demo


def test_seed_demo_idempotent(tmp_path):
    db_file = tmp_path / "stage1.db"
    url = f"sqlite:///{db_file.as_posix()}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(64) PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(text("INSERT OR IGNORE INTO schema_migrations (version) VALUES ('stage1-v1')"))

    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = Session()
    try:
        first = seed_demo(db)
        assert first["ingredients"] == 3
        assert first["products"] == 8  # includes same-composition price demo variants
        assert first["interactions"] == 1
        assert first["dose_rules"] == 1

        second = seed_demo(db)
        assert second == {
            "ingredients": 0,
            "products": 0,
            "links": 0,
            "interactions": 0,
            "dose_rules": 0,
        }

        assert db.scalar(select(func.count()).select_from(Ingredient)) == 3
        assert db.scalar(select(func.count()).select_from(Product)) == 8
        assert db.scalar(select(func.count()).select_from(InteractionRule)) == 1
        assert db.scalar(select(func.count()).select_from(DoseRule)) == 1

        alpha = db.get(Product, "prod-demo-alpha")
        assert alpha is not None and alpha.is_synthetic is True
        assert alpha.price == 100.0
        gamma = db.get(Product, "prod-demo-gamma")
        assert gamma is not None
        assert len(list(gamma.ingredients)) == 2
        disc = db.get(Product, "prod-demo-alpha-disc")
        assert disc is not None and disc.is_discontinued is True

        rule = db.scalars(
            select(InteractionRule).where(
                InteractionRule.rule_code == "Demo Interaction Rule 001"
            )
        ).first()
        assert rule is not None
        assert rule.status == "DEMO_ILLUSTRATIVE"
        assert rule.evidence_source == "Synthetic demo dataset"
    finally:
        db.close()
        engine.dispose()
