#!/usr/bin/env python3
"""CLI: migrate schema + seed demo (and optionally catalogue/rules). Idempotent."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.config import get_settings
from backend.app.db.migrate import upgrade
from backend.app.db.session import SessionLocal
from backend.app.services.seed_service import seed_all, seed_demo


def seed() -> dict:
    """Used by tests — demo seed only against configured DB."""
    upgrade()
    db = SessionLocal()
    try:
        return seed_demo(db)
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="RxGuard India seed")
    parser.add_argument(
        "--catalogue",
        action="store_true",
        help="Force catalogue+rules import (sets demo_mode off for this run)",
    )
    parser.add_argument(
        "--catalogue-limit",
        type=int,
        default=None,
        help="Limit catalogue rows (useful for CI)",
    )
    args = parser.parse_args()

    upgrade()
    settings = get_settings()
    if args.catalogue:
        # Temporarily override via env-like attribute for this process
        object.__setattr__(settings, "demo_mode", False)

    db = SessionLocal()
    try:
        summary = seed_all(db, catalogue_limit=args.catalogue_limit)
        print("Seed complete (idempotent).")
        print(summary)
        print("ALL SYNTHETIC DEMO DATA IS DEMO_ILLUSTRATIVE — not clinical guidance.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
