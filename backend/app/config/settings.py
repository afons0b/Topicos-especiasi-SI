import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    app_env: str
    frontend_origin: str | None


def get_settings() -> Settings:
    app_env = os.getenv("APP_ENV", "development").lower()
    frontend_origin = os.getenv("FRONTEND_ORIGIN") or None

    if app_env == "production" and frontend_origin is None:
        raise RuntimeError("FRONTEND_ORIGIN é obrigatório em produção")

    return Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://gastos:gastos@localhost:55432/gastos",
        ),
        app_env=app_env,
        frontend_origin=frontend_origin,
    )
