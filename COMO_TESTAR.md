# Como rodar e testar o Yummi

Guia para subir o backend do zero numa máquina nova e testar a API pelo Swagger.

O que está pronto até aqui: o **CRUD de cadastro de usuário** — criar, consultar,
atualizar e excluir, com validação de CPF, unicidade e senha criptografada.

---

## Caminho rápido: só os testes (5 minutos, sem banco)

Se você só quer conferir que o projeto funciona, **não precisa instalar MySQL**.
Os 43 testes rodam contra um banco em memória.

Você vai precisar do [Python 3.10 ou superior](https://www.python.org/downloads/)
(desenvolvido no 3.14). Na instalação, marque **"Add Python to PATH"**.

```bash
git clone -b Development https://github.com/Hocrons/Projeto_Yummi.git
```

```bash
cd Projeto_Yummi/backend
```

```bash
python -m venv .venv
```

```bash
.venv\Scripts\python -m pip install -r requirements.txt
```

```bash
.venv\Scripts\python -m pytest tests/ -v
```

Esperado: **43 passed**. Se der isso, o código está íntegro na sua máquina.

> **Por que `.venv\Scripts\python` em vez de ativar o ambiente?** Porque no
> Windows o `Activate.ps1` costuma esbarrar na política de execução do
> PowerShell. Chamando o executável direto, você pula esse problema.

---

## Caminho completo: API + Swagger

Aqui você sobe a API de verdade, conectada ao MySQL, e testa pelo navegador.

### 1. Instalar o MySQL

Se você tem **winget** (vem no Windows 10/11 atualizado), é um comando:

```bash
winget install --id Oracle.MySQL --source winget
```

E o Workbench, que dá a interface gráfica para ver o banco:

```bash
winget install --id Oracle.MySQLWorkbench --source winget
```

Sem winget, baixe o instalador em [dev.mysql.com/downloads/installer](https://dev.mysql.com/downloads/installer/).

### 2. Configurar o servidor

O instalador **só copia os arquivos** — ele não cria o banco nem o serviço.
Abra o configurador **como administrador**:

```
"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql_configurator.exe"
```

Nas telas:

| Tela | Escolha |
| --- | --- |
| Config Type | `Development Computer` |
| Connectivity | TCP/IP, porta `3306` |
| Authentication | `Use Strong Password Encryption` |
| Accounts | **defina a senha do root e anote** |
| Windows Service | instalar como serviço, início automático |

No fim, clique em **Apply**.

### 3. Criar o banco

Na pasta `backend`, com o caminho do MySQL:

```bash
"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -u root -p < database/yummi_schema.sql
```

Ele pede a senha que você definiu. O script já começa com `DROP DATABASE IF EXISTS yummi`,
então rodar de novo sempre devolve um banco limpo.

> `database/yummi_schema.sql` é **gerado**, não escrito à mão. Ele sai dos models
> SQLAlchemy pelo `scripts/gerar_schema_sql.py`. Se você mexer num model, rode o
> script de novo — nunca edite o `.sql` direto, a mudança se perde.

### 4. Configurar a senha no projeto

Copie o arquivo de exemplo:

```bash
copy .env.example .env
```

Abra o `.env` e troque a linha `DB_PASSWORD=` pela senha que você definiu no passo 2.

O `.env` está no `.gitignore` — sua senha não vai para o repositório.

### 5. Subir a API

```bash
.venv\Scripts\python run.py
```

Deve aparecer `Running on http://127.0.0.1:5000`. **Deixe esse terminal aberto** —
fechar ele derruba a API.

Confira que respondeu, em outro terminal ou no navegador:

```
http://127.0.0.1:5000/api/saude
```

Esperado: `{"status": "ok", "servico": "yummi-api"}`

---

## Testando pelo Swagger

Abra no navegador:

```
http://127.0.0.1:5000/apidocs/
```

Você vai ver os 7 endpoints. Em cada um, o botão **Try it out** libera os campos,
e **Execute** dispara a requisição de verdade contra o banco.

### Roteiro sugerido

Cada passo abaixo mostra uma regra diferente funcionando. Faça na ordem.

**1. Cadastrar um usuário** — `POST /api/usuarios`

Try it out → no seletor de exemplos escolha **"Cadastro com e-mail e senha"** →
Execute.

Esperado: **201**. Repare na resposta que:
- o CPF `529.982.247-25` foi gravado como `52998224725`, sem máscara
- o e-mail virou minúsculas
- `status_conta` é `pendente` — a conta só ativa depois da validação do código OTP
- **não existe campo de senha na resposta**, nem o hash

**2. Tentar cadastrar o mesmo CPF** — repita o passo 1 sem mudar nada.

Esperado: **409**, dizendo qual campo duplicou.

**3. Cadastrar com CPF inválido** — mesmo endpoint, troque o `cpf` por `"11111111111"`
e mude o e-mail e o celular para não colidir com o do passo 1.

Esperado: **400** com `"CPF invalido."` — o CPF é validado pelo algoritmo módulo 11,
que rejeita sequências de dígitos iguais mesmo elas "fechando" a conta.

**4. Cadastrar um menor de idade** — troque `data_nascimento` para `"2020-01-01"`.

Esperado: **400**, idade mínima de 18 anos.

**5. Listar** — `GET /api/usuarios` → Execute.

Esperado: **200** com o usuário do passo 1 e o bloco de paginação. Experimente
os filtros `busca=maria` e `por_pagina=1`.

**6. Ativar a conta** — `PATCH /api/usuarios/{id_usuario}/status`, com
`id_usuario = 1` e corpo `{"status_conta": "ativo"}`.

Esperado: **200**, agora com `status_conta: "ativo"`.

**7. Tentar trocar o CPF** — `PATCH /api/usuarios/{id_usuario}`, corpo
`{"cpf": "16899535009"}`.

Esperado: **400**. O CPF não é editável de propósito — é a chave de negócio da
pessoa, e permitir a troca abriria caminho para assumir a identidade de outro cadastro.

**8. Excluir** — `DELETE /api/usuarios/{id_usuario}` com `id_usuario = 1`.

Esperado: **200**. Agora faça `GET /api/usuarios/1`: devolve **404**.

Mas a linha **não foi apagada** — veja o próximo bloco.

---

## Conferindo no banco

Abra o **MySQL Workbench** e conecte na `Local instance MySQL84`.

No painel esquerdo, clique na aba **`Schemas`** (fica ao lado de `Administration`,
embaixo). Se o `yummi` não aparecer, botão direito → **Refresh All**.

Na aba de query, rode:

```sql
SELECT id_usuario, nome_completo, email, cpf, status_conta, senha_hash
FROM yummi.USUARIO;
```

Duas coisas para reparar:

**A senha está como hash**, começando com `$2b$12$` — é bcrypt com salt. Em lugar
nenhum do banco existe a senha em texto puro.

**O usuário do passo 8 continua lá**, com `status_conta = 'excluido'`. A exclusão é
lógica, não física. O motivo: `PEDIDO.id_usuario` é chave estrangeira `NOT NULL`, então
apagar a linha de verdade seria bloqueado pelo banco assim que o usuário tivesse um
pedido — e o histórico de pedidos iria junto.

### Vendo o modelo físico

```sql
SHOW CREATE TABLE yummi.USUARIO;
```

Devolve o DDL real, com os tipos, os campos nulos e não nulos, as chaves e as
constraints nomeadas. Dá para testar que elas funcionam:

```sql
INSERT INTO yummi.USUARIO (nome_completo, cpf, data_nascimento, senha_hash, tipo_usuario, status_conta)
VALUES ('Teste', '16899535009', '1990-01-01', 'x', 'cliente', 'pendente');
```

Esperado: erro `Check constraint 'ck_USUARIO_contato' is violated` — o banco recusa
um usuário sem e-mail **e** sem celular, porque ele não teria como receber o código OTP.

---

## Problemas comuns

**`'python' não é reconhecido`** — o Python não está no PATH. Reinstale marcando
"Add Python to PATH", ou use o caminho completo do executável.

**`cryptography is required for sha256_password`** — falta instalar as dependências.
Rode o `pip install -r requirements.txt` de novo; o `cryptography` está lá. Ele é
necessário porque o MySQL 8.4 autentica com `caching_sha2_password`.

**`Access denied for user 'root'@'localhost'`** — a senha no `.env` não bate com a
que você definiu no configurador. Confira o `DB_PASSWORD`.

**`Can't connect to MySQL server`** — o serviço não está rodando. Confira com:

```bash
powershell -Command "Get-Service MySQL84"
```

Se aparecer `Stopped`, inicie com `net start MySQL84` num terminal como administrador.

**`Unknown database 'yummi'`** — você pulou o passo 3. Rode o `yummi_schema.sql`.

**`Address already in use` na porta 5000** — já tem uma API rodando. Feche o terminal
dela, ou descubra quem está na porta:

```bash
powershell -Command "Get-NetTCPConnection -LocalPort 5000 -State Listen"
```

**O Swagger abre mas os endpoints somem** — algum YAML de docstring quebrou. Rode
`.venv\Scripts\python -m pytest tests/test_swagger.py -v`; os testes apontam o problema.

---

## Comandos de referência

| O que | Comando |
| --- | --- |
| Rodar os testes | `.venv\Scripts\python -m pytest tests/ -v` |
| Subir a API | `.venv\Scripts\python run.py` |
| Regerar o schema SQL | `.venv\Scripts\python scripts\gerar_schema_sql.py` |
| Zerar o banco | rodar `database/yummi_schema.sql` no MySQL |
| Swagger | http://127.0.0.1:5000/apidocs/ |
| Sonda de saúde | http://127.0.0.1:5000/api/saude |

Detalhes de arquitetura e decisões de projeto estão em [backend/README.md](backend/README.md).
O documento geral do projeto — escopo, requisitos e modelo de dados — está em
[YUMMI_PROJETO.md](YUMMI_PROJETO.md).
