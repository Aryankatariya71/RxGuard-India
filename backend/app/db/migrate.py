"""Repeatable schema ensure (create_all). Alembic-ready hook for later revisions."""

from __future__ import annotations

from sqlalchemy import text

from backend.app.db.session import Base, engine
from backend.app.models import entities  # noqa: F401 — register models


SCHEMA_VERSION = "stage1-v1"


def upgrade() -> str:
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
        exists = conn.execute(
            text("SELECT 1 FROM schema_migrations WHERE version = :v"),
            {"v": SCHEMA_VERSION},
        ).first()
        if not exists:
            conn.execute(
                text("INSERT INTO schema_migrations (version) VALUES (:v)"),
                {"v": SCHEMA_VERSION},
            )
    return SCHEMA_VERSION


if __name__ == "__main__":
    v = upgrade()
    print(f"Schema ensured. version={v}")
