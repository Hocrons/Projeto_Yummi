"""Testes da documentacao OpenAPI.

Existem porque o YAML vive dentro das docstrings: uma indentacao errada nao
quebra o Python, so some com o endpoint da documentacao - e ninguem percebe
ate abrir o /apidocs. Estes testes falham antes disso.
"""
import pytest
from openapi_spec_validator import validate

ROTAS_ESPERADAS = {
    ("/api/usuarios", "post"),
    ("/api/usuarios", "get"),
    ("/api/usuarios/{id_usuario}", "get"),
    ("/api/usuarios/{id_usuario}", "patch"),
    ("/api/usuarios/{id_usuario}/status", "patch"),
    ("/api/usuarios/{id_usuario}", "delete"),
    ("/api/saude", "get"),
}


@pytest.fixture
def spec(client):
    resposta = client.get("/apispec_1.json")
    assert resposta.status_code == 200
    return resposta.get_json()


def test_swagger_ui_responde(client):
    assert client.get("/apidocs/").status_code == 200


def test_spec_cumpre_o_padrao_openapi_3(spec):
    validate(spec)  # levanta excecao se a especificacao for invalida
    assert spec["openapi"].startswith("3.")


def test_todas_as_rotas_estao_documentadas(spec):
    documentadas = {
        (rota, metodo) for rota, metodos in spec["paths"].items() for metodo in metodos
    }
    assert ROTAS_ESPERADAS <= documentadas


def test_todo_endpoint_tem_resumo(spec):
    sem_resumo = [
        f"{metodo.upper()} {rota}"
        for rota, metodos in spec["paths"].items()
        for metodo, detalhe in metodos.items()
        if not detalhe.get("summary")
    ]
    assert sem_resumo == []


def test_referencias_de_schema_existem(spec):
    """Um $ref para schema inexistente passa no YAML e quebra so na tela."""
    definidos = set(spec.get("components", {}).get("schemas", {}))
    pendentes, refs = [spec["paths"]], []

    while pendentes:
        no = pendentes.pop()
        if isinstance(no, dict):
            for chave, valor in no.items():
                if chave == "$ref" and isinstance(valor, str):
                    refs.append(valor)
                else:
                    pendentes.append(valor)
        elif isinstance(no, list):
            pendentes.extend(no)

    quebrados = [r for r in refs if r.rsplit("/", 1)[-1] not in definidos]
    assert refs, "nenhum $ref encontrado - os schemas reutilizaveis sumiram"
    assert quebrados == []


def test_post_documenta_os_tres_status_possiveis(spec):
    """201 criado, 400 dado invalido e 409 duplicado - os tres ja verificados."""
    respostas = spec["paths"]["/api/usuarios"]["post"]["responses"]
    assert {"201", "400", "409"} <= set(respostas)
