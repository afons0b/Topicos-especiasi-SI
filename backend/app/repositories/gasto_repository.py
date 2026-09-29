
from sqlalchemy.orm import Session

from app.models.gasto import Gasto


class GastoRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def criar(self, gasto: Gasto) -> Gasto:
        self._session.add(gasto)
        self._session.commit()
        self._session.refresh(gasto)
        return gasto


