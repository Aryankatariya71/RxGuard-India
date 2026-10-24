from __future__ import annotations

from fastapi import APIRouter

from backend.app.core.config import get_settings
from backend.app.core.constants import SAFETY_DISCLAIMER
from backend.app.db.session import check_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    settings = get_settings()
    ok = check_db()
    return {
        "status": "ok" if ok else "degraded",
        "api": "up",
        "database": "connected" if ok else "unavailable",
        "app_version": settings.app_version,
        "environment": settings.environment,
        "demo_data_mode": settings.demo_data_mode,
    }


@router.get("/config/public")
def public_config():
    settings = get_settings()
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "demo_data_mode": settings.demo_data_mode,
        "catalogue_version": settings.catalogue_version,
        "rule_set_version": settings.rule_set_version,
        "auth_enabled": False,
        "disclaimer": SAFETY_DISCLAIMER,
    }
