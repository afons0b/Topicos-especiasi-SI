import os
from collections.abc import Generator
from typing import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

os.environ["APP_ENV"] = "development"
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://gastos:gastos@localhost:55432/gastos",
)

from app.config.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.gasto import Gasto  # noqa: E402


@pytest.fixture(autouse=True)
def banco_limpo() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def quantidade_gastos() -> Generator[Callable[[], int], None, None]:
    def contar() -> int:
        with SessionLocal() as session:
            return session.scalar(select(func.count()).select_from(Gasto)) or 0

    yield contar

