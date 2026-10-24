"""Repeatable schema ensure (create_all). Alembic-ready hook for later revisions."""

from __future__ import annotations

from sqlalchemy import text

from backend.app.db.session import Base, engine
from backend.app.models import entities  # noqa: F401 — register models


SCHEMA_VERSION = "ingredient-explorer-v1"


def _sqlite_add_column_if_missing(conn, table: str, column: str, ddl: str) -> None:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    names = {r[1] for r in rows}
    if column not in names:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))


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
        # Additive columns for existing SQLite DBs (Stage external-sources)
        try:
            _sqlite_add_column_if_missing(
                conn, "products", "source_record_id", "source_record_id VARCHAR(128)"
            )
            _sqlite_add_column_if_missing(
                conn, "products", "source_url", "source_url VARCHAR(512)"
            )
            _sqlite_add_column_if_missing(
                conn, "products", "retrieved_at", "retrieved_at TIMESTAMP"
            )
            _sqlite_add_column_if_missing(
                conn,
                "products",
                "verification_status",
                "verification_status VARCHAR(64) DEFAULT 'UNRESOLVED'",
            )
            _sqlite_add_column_if_missing(
                conn,
                "products",
                "geographic_applicability",
                "geographic_applicability VARCHAR(64)",
            )
            _sqlite_add_column_if_missing(conn, "products", "price", "price FLOAT")
            _sqlite_add_column_if_missing(
                conn, "products", "price_as_of", "price_as_of VARCHAR(32)"
            )
            # Fast lookups for hidden-ingredient finder
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_pi_ingredient_id "
                    "ON product_ingredients (ingredient_id)"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_pi_product_id "
                    "ON product_ingredients (product_id)"
                )
            )
        except Exception:
            pass

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
