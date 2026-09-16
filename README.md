# 🍔 Yummy — Delivery (estilo iFood)

**Plataforma de delivery completa em MVC com 3 portais independentes.**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-000000?style=for-the-badge&logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-Database-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-WhatsApp%20Service-339933?style=for-the-badge&logo=nodedotjs&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-Frontend-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

![Repo](https://img.shields.io/badge/GitHub-Hocrons%2FProjeto__Yummi-181717?style=flat-square&logo=github)
![Branch](https://img.shields.io/badge/branch-dev-blue?style=flat-square&logo=git)
![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow?style=flat-square)

---

## 📖 Sobre o projeto

**Yummy** é um sistema de delivery inspirado no iFood, construído sobre a arquitetura **MVC**
com **Python (Flask)** no backend, **MySQL** como banco de dados e **JavaScript / HTML / CSS**
no frontend.

O sistema é dividido em **3 portais independentes**, cada um com seu próprio fluxo de
autenticação e painel:

| Portal | Descrição |
|:------:|-----------|
| 👤 **Cliente** | Busca restaurantes, monta carrinho, faz checkout e acompanha pedidos em tempo real |
| 🏪 **Restaurante** | Painel do parceiro: cadastro em etapas, gestão de produtos, pedidos e perfil |
| 🛵 **Entregador** | Portal de corridas: aceita entregas, atualiza status e gerencia disponibilidade |

Além dos portais, há uma **landing page** inicial que direciona o usuário para o ambiente correto.

---

## 📑 Sumário

- [Sobre o projeto](#-sobre-o-projeto)
- [Estrutura (MVC)](#-estrutura-mvc)
- [Como rodar](#-como-rodar)
- [Microsserviço de WhatsApp](#-como-rodar-o-microsserviço-de-whatsapp)
- [Problemas comuns](#️-problemas-comuns-geral)

---

## 🧱 Estrutura (MVC)

```text
Projeto_Yummi/
├── app.py                              # 🚀 Ponto de entrada Flask
├── database.sql                        # 🗄️  Script MySQL (CREATE TABLE)
├── requirements.txt                    # 📦 Dependências Python
├── .env.example                        # ⚙️  Modelo de configuração
├── .gitignore
│
├── controllers/                        # 🎮 Controller — rotas Flask (blueprints)
│   ├── landing_ctrl.py
│   ├── auth_ctrl.py
│   ├── home_ctrl.py
│   ├── cliente_ctrl.py
│   ├── restaurante_ctrl.py
│   ├── entregador_ctrl.py
│   ├── pedido_ctrl.py
│   └── decorators.py
│
├── models/                             # 🧩 Model — acesso ao banco (sem HTTP)
│   ├── db.py                           # Conexão MySQL (PyMySQL)
│   └── models.py                       # CRUD por entidade
│
├── services/                           # 🔧 Serviços auxiliares
│   ├── otp.py
│   ├── verificacao_email.py
│   └── verificacao_whatsapp_local.py
│
├── utils.py                            # 🧰 Normalização / máscaras
│
├── templates/                          # 🎨 View — Jinja2
│   ├── base.html
│   ├── landing/index.html
│   ├── index.html
│   ├── cliente/
│   ├── restaurante/
│   └── entregador/
│
├── static/
│   ├── css/                            # global, style, landing, cliente, restaurante, entregador
│   ├── js/                             # main, viacep, carrinho, codigo, status_pedido, endereco
│   └── img/
│
└── whatsapp-service/                   # 📱 Microsserviço Node.js
    ├── package.json
    ├── index.js
    └── sessao/                         # ⚠️ NÃO subir pro GitHub
```

---

## 🚀 Como rodar

### 1️⃣ Clonar o repositório

```bash
git clone https://github.com/Hocrons/Projeto_Yummi.git
cd Projeto_Yummi
git checkout dev
```

### 2️⃣ Criar e ativar o ambiente virtual

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / Mac
```

> 💡 **Windows + PowerShell:** se aparecer *"a execução de scripts foi desabilitada neste sistema"*,
> rode uma vez no PowerShell como administrador:
>
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```
>
> Confirme com `S`. Depois feche e reabra o terminal.

### 3️⃣ Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4️⃣ Criar o banco no MySQL

**Linux / Mac / Git Bash:**

```bash
mysql -u root -p < database.sql
```

**Windows (PowerShell) — o operador `<` NÃO funciona:**

```powershell
Get-Content database.sql | mysql -u root -p yummy
```

> ⚠️ O `database.sql` **não cria o banco** `yummy`, apenas as tabelas.
> Crie antes, se ainda não existir:
>
> ```powershell
> mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS yummy CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
> ```
>
> 🔎 Se o comando `mysql` não for reconhecido, adicione o `bin` do MySQL ao PATH
> (ex.: `C:\Program Files\MySQL\MySQL Server 9.5\bin`) **ou** use o caminho completo:
>
> ```powershell
> & "C:\Program Files\MySQL\MySQL Server 9.5\bin\mysql.exe" -u root -p yummy
> ```

### 5️⃣ Configurar o `.env`

```bash
cp .env.example .env
```

| Variável | Descrição |
|----------|-----------|
| `DB_HOST` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | Credenciais do MySQL |
| `SECRET_KEY` | 🔐 **Obrigatória** — sem ela as sessões caem a cada restart |
| `BASE_URL` | URL base do app (ex.: `http://localhost:5000`) |
| OAuth (Google / Facebook) | Opcional |
| SMTP | Opcional — para OTP por e-mail |

Gere uma `SECRET_KEY` forte com:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 6️⃣ Rodar o servidor Flask

```bash
python app.py
```

🌐 Acesse **[http://localhost:5000](http://localhost:5000)**

---

## 📱 Como rodar o microsserviço de WhatsApp

O envio de código **OTP por WhatsApp** (usado no cadastro e login) depende de um
microsserviço **Node.js** separado, rodando em paralelo ao Flask na porta **3001**.

### Pré-requisitos

- ✅ Node.js instalado (versão LTS) → https://nodejs.org
- ✅ Celular com WhatsApp ativo para escanear o QR Code

### Primeira vez — instalar dependências

```bash
cd whatsapp-service
npm install
```

> ⏳ A primeira instalação demora alguns minutos: baixa o **Chromium** embutido
> (usado pelo `whatsapp-web.js`) — cerca de **200 MB**.

### Iniciar o microsserviço

Em **um terminal separado** (deixe o Flask rodando no outro):

```bash
cd whatsapp-service
node index.js
```

Na primeira vez, aparece um **QR Code em ASCII** no terminal:

```text
=== Escaneie este QR Code com o WhatsApp ===
(Configurações > Aparelhos conectados > Conectar um aparelho)

█████████████████████████████
████ ▄▄▄▄▄ █▀▀ █▀ █▄▄ ▄▄▄▄▄ ████
████ █ ▄▄▄ █ ▄▄ ▀█▄█ █▄▀█ █ ████
████ █ ███ █ ▀▄▀ █▀▄▀ █▀▀█ █ ████
████ █▄▄▄█ █▀▀▄▄▀█ ▀ ▄ █ ██ ████
████▄▄▄▄▄▄▄█▄▀ █ █▄▀▄█▄▄█▄▄█████
```

**No celular:**

1. Abra o WhatsApp
2. Toque em **Configurações** (ou nos **3 pontinhos**)
3. **Aparelhos conectados** → **Conectar um aparelho**
4. Escaneie o QR Code

✅ Quando conectar, o terminal mostra:

**`✅ WhatsApp conectado! Pronto para enviar códigos de verificação.`**

A sessão fica salva em `whatsapp-service/sessao/` — nas próximas vezes não precisa
escanear de novo.

### 🔁 Fluxo do dia a dia

Você vai precisar de **2 terminais** abertos em paralelo:

**Terminal 1 — Flask (porta 5000):**

```bash
cd Projeto_Yummi
venv\Scripts\activate
python app.py
```

**Terminal 2 — WhatsApp (porta 3001):**

```bash
cd Projeto_Yummi\whatsapp-service
node index.js
```

Quando alguém se cadastra, o **Flask** chama o **Node** por HTTP (`POST /enviar`)
e a mensagem sai pelo **WhatsApp**.

### 🔌 Endpoints do microsserviço

| Método | Rota | Descrição |
|:------:|------|-----------|
| `GET`  | `/status` | Retorna `{"conectado": true/false}` |
| `POST` | `/enviar` | Envia mensagem. Body: `{"numero": "5511999999999", "mensagem": "..."}` |

### 🧪 Testar isoladamente

```bash
curl http://localhost:3001/status

curl -X POST http://localhost:3001/enviar \
  -H "Content-Type: application/json" \
  -d "{\"numero\":\"5511999999999\",\"mensagem\":\"Teste do Yummy!\"}"
```

### ⚠️ Problemas comuns do WhatsApp

| Erro | Solução |
|------|---------|
| `Cannot find module 'whatsapp-web.js'` | Rode `npm install` na pasta `whatsapp-service` |
| QR Code não aparece | Espere 10–30 s (Chromium iniciando). Se persistir, apague `sessao/` e rode de novo |
| `ProtocolError` / `Evaluation failed` | Apague `whatsapp-service/sessao/` e escaneie o QR de novo |
| Flask retorna `503 Service Unavailable` | O Node não está rodando ou está em outra porta. Confira o terminal dele |
| WhatsApp ainda não conectado | Espere o **"✅ conectado"** no terminal do Node antes de testar |
| Conexão cai depois de horas | Comportamento normal do WhatsApp Web — só reiniciar o Node |

---

## 🛠️ Problemas comuns (geral)

| Erro | Causa provável / Solução |
|------|--------------------------|
| `Unknown database 'yummy'` | O banco não foi criado. Veja o passo 4 |
| `Access denied for user 'root'@'localhost'` | Senha errada no `.env` (`DB_PASSWORD`) |
| `SECRET_KEY não definida no .env. Sessões vão cair...` | Adicione `SECRET_KEY` no `.env` (passo 5) |
| `a execução de scripts foi desabilitada neste sistema` | Veja a dica de PowerShell no passo 2 |
| `O termo 'mysql' não é reconhecido` | Adicione o `bin` do MySQL ao PATH ou use o caminho completo do `mysql.exe` |

---

### 💛 Feito com carinho pelo time **Yummy**

⭐ Se este projeto te ajudou, deixe uma estrela no repositório!

[![GitHub stars](https://img.shields.io/github/stars/Hocrons/Projeto_Yummi?style=social)](https://github.com/Hocrons/Projeto_Yummi)