from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.schemas.gasto import GastoCreate, GastoResponse
from app.config.dependencies import get_gasto_service
from app.services.gasto_service import GastoService


router = APIRouter(prefix="/api/gastos", tags=["gastos"])


@router.post(
    "",
    response_model=GastoResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_gasto(
    dados: GastoCreate,
    service: Annotated[GastoService, Depends(get_gasto_service)],
) -> GastoResponse:
    return service.criar(dados)
