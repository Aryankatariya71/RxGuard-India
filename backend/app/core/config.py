"""Application settings (env-driven). Never put secrets in source."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SQLITE = f"sqlite:///{(ROOT / 'data' / 'rxguard.db').as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(ROOT / "backend" / ".env", ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "RxGuard India"
    app_version: str = "1.1.0"
    engine_version: str = "engine-1.1.0"
    environment: str = "development"

    # demo = synthetic seed only; catalogue = synthetic + parquet catalogue + rules import
    demo_mode: bool = True
    dataset_version: str = "demo-1.0"
    catalogue_version: str = "demo-1.0"
    rule_set_version: str = "demo-1.0"  # matches demo InteractionRule.version

    database_url: str = DEFAULT_SQLITE
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def demo_data_mode(self) -> bool:
        """Alias used by existing /api/health and /api/config/public."""
        return self.demo_mode

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
