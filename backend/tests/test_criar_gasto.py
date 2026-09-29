from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient


def gasto_valido() -> dict[str, str]:
    return {
        "descricao": "Almoço",
        "valor": "32.50",
        "categoria": "ALIMENTACAO",
        "data": date.today().isoformat(),
    }


def assert_erro_de_campo(resposta, campo: str) -> None:
    assert resposta.status_code == 422
    corpo = resposta.json()
    assert corpo["erro"]["codigo"] == "DADOS_INVALIDOS"
    assert corpo["erro"]["mensagem"]
    assert campo in corpo["erro"]["campos"]


def test_cria_gasto_valido(client: TestClient, quantidade_gastos) -> None:
    dados = gasto_valido()
    dados["descricao"] = "  Almoço  "

    resposta = client.post("/api/gastos", json=dados)

    assert resposta.status_code == 201
    assert resposta.json() == {
        "id": 1,
        "descricao": "Almoço",
        "valor": "32.50",
        "categoria": "ALIMENTACAO",
        "data": date.today().isoformat(),
    }
    assert quantidade_gastos() == 1


def test_rejeita_descricao_vazia(client: TestClient, quantidade_gastos) -> None:
    dados = gasto_valido()
    dados["descricao"] = "   "

    resposta = client.post("/api/gastos", json=dados)

    assert_erro_de_campo(resposta, "descricao")
    assert quantidade_gastos() == 0


def test_rejeita_descricao_maior_que_120_caracteres(
    client: TestClient, quantidade_gastos
) -> None:
    dados = gasto_valido()
    dados["descricao"] = "a" * 121

    resposta = client.post("/api/gastos", json=dados)

    assert_erro_de_campo(resposta, "descricao")
    assert quantidade_gastos() == 0


@pytest.mark.parametrize("valor", ["0.00", "-1.00"])
def test_rejeita_valor_nao_positivo(
    client: TestClient, quantidade_gastos, valor: str
) -> None:
    dados = gasto_valido()
    dados["valor"] = valor

    resposta = client.post("/api/gastos", json=dados)

    assert_erro_de_campo(resposta, "valor")
    assert quantidade_gastos() == 0


def test_rejeita_categoria_invalida(client: TestClient, quantidade_gastos) -> None:
    dados = gasto_valido()
    dados["categoria"] = "MORADIA"

    resposta = client.post("/api/gastos", json=dados)

    assert_erro_de_campo(resposta, "categoria")
    assert quantidade_gastos() == 0


def test_rejeita_data_futura(client: TestClient, quantidade_gastos) -> None:
    dados = gasto_valido()
    dados["data"] = (date.today() + timedelta(days=1)).isoformat()

    resposta = client.post("/api/gastos", json=dados)

    assert_erro_de_campo(resposta, "data")
    assert quantidade_gastos() == 0


@pytest.mark.parametrize("campo", ["descricao", "valor", "categoria", "data"])
def test_rejeita_campo_obrigatorio_ausente(
    client: TestClient, quantidade_gastos, campo: str
) -> None:
    dados = gasto_valido()
    dados.pop(campo)

    resposta = client.post("/api/gastos", json=dados)

    assert_erro_de_campo(resposta, campo)
    assert quantidade_gastos() == 0

