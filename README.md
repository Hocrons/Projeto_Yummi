# Yummy - Delivery (estilo iFood)

Projeto de delivery em **MVC**, feito com **Python (Flask)**, **MySQL**, **JS**, **HTML** e **CSS**,
baseado no Modelo de Dados Físico fornecido (usuario / cliente / restaurante / entregador / produto /
endereco / pedido / item_pedido / pagamento / plano).

O projeto tem **3 portais separados** (Cliente / Restaurante / Entregador), além de uma
**landing page** inicial que direciona para cada um.

---

## 🧱 Estrutura (MVC)
Yummy/
├── app.py # Ponto de entrada Flask (cria a app e registra os controllers)
├── database.sql # Script MySQL (CREATE TABLE de todo o modelo)
├── requirements.txt # Dependências Python
├── .env.example # Copie para .env e configure o banco
├── .gitignore
│
├── controllers/ # Controller: rotas Flask (blueprints)
│ ├── landing_ctrl.py # Landing page inicial (escolha do portal)
│ ├── auth_ctrl.py # Login/cadastro de cliente, restaurante e entregador
│ ├── home_ctrl.py # Home do cliente (busca + categorias + restaurantes)
│ ├── cliente_ctrl.py # Cardápio, carrinho (AJAX), checkout, pedidos, perfil
│ ├── restaurante_ctrl.py # Portal do parceiro (painel, produtos, perfil)
│ ├── entregador_ctrl.py # Portal do entregador (corridas)
│ ├── pedido_ctrl.py # API de status do pedido (polling)
│ └── decorators.py # @login_requerido('cliente'|'restaurante'|'entregador')
│
├── models/ # Model: acesso ao banco (sem HTTP aqui)
│ ├── db.py # Conexão MySQL (PyMySQL)
│ └── models.py # Funções de CRUD por entidade
│
├── services/ # Serviços auxiliares
│ ├── otp.py # Geração e validade dos códigos OTP
│ ├── verificacao_email.py # Envio de código por e-mail (SMTP)
│ └── verificacao_whatsapp_local.py # Cliente HTTP do microsserviço WhatsApp
│
├── utils.py # Normalização / máscaras (telefone, e-mail)
│
├── templates/ # View: Jinja2 (HTML)
│ ├── base.html
│ ├── landing/index.html
│ ├── index.html # Home do cliente (estilo iFood)
│ ├── cliente/ # Cadastro, login, carrinho, checkout, perfil
│ ├── restaurante/ # Cadastro em 6 etapas, login, painel, produtos, perfil
│ └── entregador/ # Cadastro, login, painel
│
├── static/
│ ├── css/ (global.css, style.css, landing.css, cliente.css, restaurante.css, entregador.css)
│ ├── js/ (main.js, viacep.js, carrinho.js, codigo.js, status_pedido.js, endereco.js)
│ └── img/
│
└── whatsapp-service/ # 🆕 Microsserviço Node.js para enviar WhatsApp
├── package.json
├── index.js
└── sessao/ # ⚠️ Sessão do WhatsApp (NÃO subir pro GitHub)

text

---

## 🚀 Como rodar

### 1. Clonar o repositório

```bash
git clone https://github.com/Hocrons/Projeto_Yummi.git
cd Projeto_Yummi
git checkout dev
2. Criar e ativar o ambiente virtual Python
bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac
3. Instalar as dependências Python
bash
pip install -r requirements.txt
4. Criar o banco no MySQL
bash
mysql -u root -p < database.sql
5. Configurar o .env
bash
cp .env.example .env
Edite o .env com:

Credenciais do MySQL (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)

SECRET_KEY (qualquer string aleatória)

BASE_URL (http://localhost:5000)

Credenciais dos OAuths (Google / Facebook) — se for usar

SMTP para envio de e-mail (se for usar OTP por e-mail)

6. Rodar o servidor Flask
bash
python app.py
Acesse http://localhost:5000.

📱 Como rodar o microsserviço de WhatsApp
O envio de código OTP por WhatsApp (usado no cadastro e login) depende de um
microsserviço Node.js separado, que fica rodando em paralelo ao Flask, na porta 3001.

Pré-requisitos
Node.js instalado (versão LTS) → https://nodejs.org

Um celular com WhatsApp ativo para escanear o QR Code

Primeira vez (instalar dependências)
bash
cd whatsapp-service
npm install
⚠️ A primeira instalação demora alguns minutos porque baixa o Chromium embutido
(usado pelo whatsapp-web.js para controlar o WhatsApp Web). São ~200 MB.

Iniciar o microsserviço
Em um terminal separado (deixe o Flask rodando no outro):

bash
cd whatsapp-service
node index.js
Na primeira vez, o terminal vai mostrar um QR Code em ASCII:

text
=== Escaneie este QR Code com o WhatsApp ===
(Configurações > Aparelhos conectados > Conectar um aparelho)

█████████████████████████████
████ ▄▄▄▄▄ █▀▀ █▀ █▄▄ ▄▄▄▄▄ ████
...
No celular:

Abra o WhatsApp

Toque em Configurações (ou nos 3 pontinhos)

Aparelhos conectados → Conectar um aparelho

Escaneie o QR Code

Quando conectar, o terminal mostra:

text
✅ WhatsApp conectado! Pronto para enviar códigos de verificação.
A sessão fica salva na pasta whatsapp-service/sessao/ — nas próximas vezes
não precisa escanear de novo.

Fluxo do dia a dia
Você vai precisar de 2 terminais abertos em paralelo:

Terminal 1 — Flask (porta 5000):

bash
cd Projeto_Yummi
venv\Scripts\activate
python app.py
Terminal 2 — WhatsApp (porta 3001):

bash
cd Projeto_Yummi\whatsapp-service
node index.js
Agora, quando alguém se cadastrar, o Flask chama o Node por HTTP (POST /enviar)
e a mensagem sai pelo WhatsApp.

Endpoints do microsserviço
Método	Rota	Descrição
GET	/status	Retorna {"conectado": true/false}
POST	/enviar	Envia mensagem. Body: {"numero": "5511999999999", "mensagem": "..."}
Testar isoladamente
bash
curl http://localhost:3001/status
curl -X POST http://localhost:3001/enviar \
  -H "Content-Type: application/json" \
  -d "{\"numero\":\"5511999999999\",\"mensagem\":\"Teste do Yummy!\"}"
⚠️ Problemas comuns do WhatsApp
Erro	Solução
Cannot find module 'whatsapp-web.js'	Rode npm install na pasta whatsapp-service
QR Code não aparece	Espere 10-30s (Chromium está iniciando). Se persistir, apague a pasta sessao/ e rode de novo
ProtocolError / Evaluation failed	Apague whatsapp-service/sessao/ e escaneie o QR de novo
Flask retorna 503 Service Unavailable	O Node não está rodando ou está em outra porta. Confira o terminal do Node
WhatsApp ainda não conectado	Espere aparecer o "✅ conectado" no terminal do Node antes de testar
Conexão cai depois de horas	Normal do WhatsApp Web — só reiniciar o Node