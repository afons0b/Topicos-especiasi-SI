from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.exceptions.application import RegraDeNegocioError


def _campo_do_erro(localizacao: tuple[Any, ...]) -> str:
    partes = [str(parte) for parte in localizacao if parte not in {"body", "query", "path"}]
    return ".".join(partes) or "requisicao"


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    del request
    erros = exc.errors()
    json_invalido = any(erro.get("type") == "json_invalid" for erro in erros)

    if json_invalido:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "erro": {
                    "codigo": "JSON_INVALIDO",
                    "mensagem": "O corpo da requisição contém JSON malformado.",
                }
            },
        )

    campos: dict[str, str] = {}
    for erro in erros:
        campo = _campo_do_erro(tuple(erro.get("loc", ())))
        campos.setdefault(campo, erro.get("msg", "Valor inválido"))

    return JSONResponse(
        status_code=422,
        content={
            "erro": {
                "codigo": "DADOS_INVALIDOS",
                "mensagem": "Os dados enviados são inválidos.",
                "campos": campos,
            }
        },
    )


async def business_error_handler(
    request: Request, exc: RegraDeNegocioError
) -> JSONResponse:
    del request
    return JSONResponse(
        status_code=422,
        content={
            "erro": {
                "codigo": "DADOS_INVALIDOS",
                "mensagem": str(exc),
                "campos": exc.campos,
            }
        },
    )


async def database_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    del request, exc
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "erro": {
                "codigo": "ERRO_DE_PERSISTENCIA",
                "mensagem": "Não foi possível persistir o gasto.",
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(RegraDeNegocioError, business_error_handler)
    app.add_exception_handler(SQLAlchemyError, database_error_handler)
