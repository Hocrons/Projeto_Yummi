# Yummi — Backend

API REST do Yummi. Flask + SQLAlchemy + MySQL 8, organizada em MVC.

## Camadas

O fluxo de uma requisição atravessa as camadas nesta ordem, e cada uma só
conhece a seguinte:

```
routes/       mapa de URLs (blueprint)
  └─ controllers/   traduz HTTP <-> serviço. Não tem regra de negócio nem SQL.
       └─ services/     regras de negócio: valida, normaliza, cifra, checa unicidade.
            └─ models/     camada M: tabelas, tipos, chaves e constraints.
```

`utils/` guarda validadores de domínio (CPF, e-mail, celular, idade) e os
erros de negócio que o `app/__init__.py` traduz em status HTTP.

## Rodando

```bash
python -m venv .venv
```

```bash
.venv\Scripts\pip install -r requirements.txt
```

Crie o banco a partir do schema gerado:

```bash
mysql -u root -p < database/yummi_schema.sql
```

Copie `.env.example` para `.env`, preencha a senha do MySQL e suba a API:

```bash
.venv\Scripts\python run.py
```

## Testes

```bash
.venv\Scripts\python -m pytest tests/ -v
```

Os testes rodam contra SQLite em memória — sobem em segundos e não exigem
MySQL instalado. As regras testadas vivem na camada de serviço, então
independem do dialeto do banco.

## Modelo físico

`database/yummi_schema.sql` é **gerado**, não escrito à mão:

```bash
.venv\Scripts\python scripts/gerar_schema_sql.py
```

O SQL é derivado dos models SQLAlchemy, então os dois nunca divergem. Rode o
script sempre que alterar um model, e versione o `.sql` resultante — ele é o
artefato de modelo físico exigido pela disciplina.

## Endpoints

| Método | Rota | O que faz |
| --- | --- | --- |
| `POST` | `/api/usuarios` | Cadastra usuário. Nasce com `status_conta = pendente`. |
| `GET` | `/api/usuarios` | Lista paginada. Aceita `?pagina`, `?por_pagina`, `?tipo_usuario`, `?busca`. |
| `GET` | `/api/usuarios/<id>` | Detalha um usuário. |
| `PATCH` | `/api/usuarios/<id>` | Atualização parcial dos dados cadastrais. |
| `PATCH` | `/api/usuarios/<id>/status` | Ativa, bloqueia ou reativa a conta. |
| `DELETE` | `/api/usuarios/<id>` | Exclusão **lógica**. |
| `GET` | `/api/saude` | Sonda: confere se a API subiu. |

### Formato das respostas

Sucesso devolve `{"dados": {...}}`; erro devolve `{"erro": {"campo": ..., "mensagem": ...}}`.

| Status | Quando |
| --- | --- |
| `201` | Usuário criado |
| `200` | Consulta, atualização ou exclusão bem-sucedida |
| `400` | Dado inválido (CPF, e-mail, celular, idade, senha) |
| `404` | Usuário inexistente ou já excluído |
| `409` | E-mail, celular ou CPF já cadastrado |
| `500` | Erro não tratado — detalhe vai para o log, não para a resposta |

### Exemplo

```bash
curl -X POST http://127.0.0.1:5000/api/usuarios -H "Content-Type: application/json" -d "{\"nome_completo\":\"Maria de Souza\",\"email\":\"maria@exemplo.com\",\"celular\":\"11987654321\",\"cpf\":\"52998224725\",\"data_nascimento\":\"1998-03-15\",\"senha\":\"senhaSegura123\"}"
```

## Decisões que valem explicar na apresentação

**Exclusão é lógica, não física.** `PEDIDO.id_usuario` é FK `NOT NULL`: apagar
a linha seria bloqueado pela integridade referencial assim que o usuário
tivesse um pedido. O `DELETE` marca `status_conta = 'excluido'` — mesmo
raciocínio que o projeto já aplica em `PRODUTO` (`disponivel = false`).

**`status_conta` ganhou o valor `excluido`.** O dicionário de dados original
previa `pendente | ativo | bloqueado`, e nenhum desses significa "a conta foi
encerrada". Alteração a registrar no documento formal.

**CPF não é atualizável.** É a chave de negócio da pessoa e não muda na vida
real. Alterá-lo por uma rota de edição de perfil abriria caminho para assumir
a identidade de outro cadastro.

**Senha nunca em texto puro.** bcrypt com salt por usuário (RF09/RNF04), e
nem `senha_hash` nem `id_social` aparecem em qualquer resposta da API.

**Unicidade é checada duas vezes.** Uma no serviço, que devolve `409` com o
campo culpado; outra no `UNIQUE` do banco, que segura duas requisições
simultâneas passando juntas pela primeira checagem.

## Escopo

Implementado: **CRUD de `USUARIO`** — os 13 campos do dicionário, validação de
CPF por módulo 11, unicidade de e-mail/celular/CPF, hash bcrypt, idade mínima
e exclusão lógica.

Ainda não implementado, do mesmo módulo: envio e validação de OTP (RF04),
OAuth Google/Facebook (RF05 — o modelo já tem `provedor_social`/`id_social`,
falta o fluxo), cadastro de endereço (RF06), rate limiting (RF10) e JWT
(RNF05). As outras 17 tabelas entram junto com os módulos que as usam.
