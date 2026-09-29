from datetime import date

from pydantic import BaseModel, ConfigDict, StrictStr

from app.models.gasto import Categoria


class GastoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    descricao: StrictStr
    valor: StrictStr
    categoria: Categoria
    data: date


class GastoResponse(BaseModel):
    id: int
    descricao: StrictStr
    valor: StrictStr
    categoria: Categoria
    data: date
