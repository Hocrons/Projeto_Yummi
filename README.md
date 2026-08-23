# Yummi

O Yummi é uma plataforma de pedidos de comida que conecta clientes a restaurantes parceiros.

Projeto acadêmico da disciplina **SI5 — Desenvolvimento de Sistemas de Informação**
(Faculdade Impacta).

## Por onde começar

| Documento | Para quê |
| --- | --- |
| **[COMO_TESTAR.md](COMO_TESTAR.md)** | **Rodar o projeto e testar a API pelo Swagger.** Comece por aqui. |
| [backend/README.md](backend/README.md) | Arquitetura do backend, endpoints e decisões de projeto. |
| [YUMMI_PROJETO.md](YUMMI_PROJETO.md) | Escopo, requisitos, modelo de dados e dicionário de dados. |

## Stack

Python · Flask · SQLAlchemy · MySQL 8 · API REST documentada em OpenAPI 3 (Swagger UI).

## Estado atual

Implementado o **CRUD de cadastro de usuário**: criar, consultar, atualizar e excluir,
com validação de CPF por módulo 11, unicidade de e-mail/celular/CPF, senha em hash
bcrypt e exclusão lógica.

Em aberto no mesmo módulo: OTP, login social, cadastro de endereço, rate limiting e JWT.
