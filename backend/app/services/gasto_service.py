import re
from datetime import date
from decimal import Decimal, InvalidOperation


from app.exceptions.application import RegraDeNegocioError
from app.models.gasto import Gasto
from app.repositories.gasto_repository import GastoRepository
from app.schemas.gasto import GastoCreate, GastoResponse


VALOR_PATTERN = re.compile(r"^(?:0|[1-9]\d{0,9})\.\d{2}$")
VALOR_MAXIMO = Decimal("9999999999.99")


class GastoService:
    def __init__(self, repository: GastoRepository) -> None:
        self._repository = repository

    def criar(self, dados: GastoCreate) -> GastoResponse:
        descricao = self._normalizar_descricao(dados.descricao)
        valor = self._validar_valor(dados.valor)
        self._validar_data(dados.data)

        gasto = self._repository.criar(
            Gasto(
                descricao=descricao,
                valor=valor,
                categoria=dados.categoria,
                data=dados.data,
            )
        )

        return GastoResponse(
            id=gasto.id,
            descricao=gasto.descricao,
            valor=f"{gasto.valor:.2f}",
            categoria=gasto.categoria,
            data=gasto.data,
        )

    @staticmethod
    def _normalizar_descricao(valor: str) -> str:
        descricao = valor.strip()
        if not 1 <= len(descricao) <= 120:
            raise RegraDeNegocioError(
                {"descricao": "deve conter entre 1 e 120 caracteres após normalização"}
            )
        return descricao

    @staticmethod
    def _validar_valor(valor: str) -> Decimal:
        if not VALOR_PATTERN.fullmatch(valor):
            raise RegraDeNegocioError(
                {"valor": "deve ser uma string decimal positiva com duas casas decimais"}
            )

        try:
            valor_decimal = Decimal(valor)
        except InvalidOperation as exc:
            raise RegraDeNegocioError(
                {"valor": "deve ser um valor decimal válido"}
            ) from exc

        if valor_decimal <= Decimal("0.00"):
            raise RegraDeNegocioError({"valor": "deve ser maior que zero"})
        if valor_decimal > VALOR_MAXIMO:
            raise RegraDeNegocioError(
                {"valor": "deve ser menor ou igual a 9999999999.99"}
            )
        return valor_decimal

    @staticmethod
    def _validar_data(valor: date) -> None:
        if valor > date.today():
            raise RegraDeNegocioError({"data": "não pode estar no futuro"})


