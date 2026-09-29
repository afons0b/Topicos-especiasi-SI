from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.repositories.gasto_repository import GastoRepository
from app.services.gasto_service import GastoService


def get_gasto_repository(
    session: Annotated[Session, Depends(get_db)],
) -> GastoRepository:
    return GastoRepository(session)


def get_gasto_service(
    repository: Annotated[GastoRepository, Depends(get_gasto_repository)],
) -> GastoService:
    return GastoService(repository)
