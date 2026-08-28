# Yummy - Delivery (estilo iFood)

Projeto de delivery em **MVC**, feito com **Python (Flask)**, **MySQL**, **JS**, **HTML** e **CSS**,
baseado no Modelo de Dados Físico fornecido (usuario / cliente / restaurante / entregador / produto /
endereco / pedido / item_pedido / pagamento).

## Estrutura (MVC)

```
Yummy/
├── app.py                 # Ponto de entrada Flask (cria a app e registra os controllers)
├── database.sql           # Script MySQL (CREATE TABLE de todo o modelo)
├── requirements.txt
├── .env.example            # copie para .env e configure o banco
├── controllers/            # Controller: rotas Flask (blueprints)
│   ├── auth_ctrl.py         # login/cadastro de cliente, restaurante e entregador
│   ├── home_ctrl.py         # home / busca de restaurantes
│   ├── cliente_ctrl.py      # cardápio, carrinho (AJAX), checkout, pedidos, perfil
│   ├── restaurante_ctrl.py  # painel de pedidos, CRUD de produtos, perfil
│   ├── entregador_ctrl.py   # painel de entregas
│   ├── pedido_ctrl.py       # API de status do pedido (polling)
│   └── decorators.py        # @login_requerido('cliente'|'restaurante'|'entregador')
├── models/                  # Model: acesso ao banco (sem HTTP aqui)
│   ├── db.py                 # conexão MySQL (PyMySQL)
│   └── models.py             # funções de CRUD por entidade
├── templates/                # View: Jinja2 (HTML)
│   ├── base.html / index.html
│   ├── cliente/  restaurante/  entregador/
└── static/
    ├── css/ (global.css, style.css, cliente.css, restaurante.css, entregador.css)
    ├── js/  (main.js, carrinho.js, status_pedido.js)
    └── img/
```

## Como rodar

1. Crie e ative o ambiente virtual:
   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # Linux/Mac
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Crie o banco no MySQL:
   ```bash
   mysql -u root -p < database.sql
   ```

4. Configure o `.env` (copie de `.env.example`) com usuário/senha do seu MySQL.

5. Rode o servidor:
   ```bash
   python app.py
   ```

6. Acesse `http://localhost:5000`.

## Fluxo para testar rapidinho

1. Cadastre um **restaurante** (`/auth/restaurante/cadastrar`) e faça login.
2. No painel do restaurante, adicione alguns **produtos** (`Meu cardápio > Novo produto`).
3. Saia e cadastre um **cliente** (`/auth/cliente/cadastrar`).
4. Na home, clique no restaurante, adicione itens ao carrinho e finalize o pedido (checkout).
5. Volte para o login do **restaurante**, aceite o pedido e marque como "pronto".
6. Cadastre um **entregador** (`/auth/entregador/cadastrar`), aceite a entrega e marque como entregue.
7. Como cliente, acompanhe o status em "Meus pedidos" (ele atualiza sozinho via AJAX).

## Funcionalidades implementadas

- Autenticação e sessão separada para os 3 perfis (cliente, restaurante, entregador)
- CRUD completo de produtos (restaurante)
- CRUD de endereços do cliente
- Carrinho de compras via sessão + AJAX (adicionar, atualizar quantidade, remover)
- Checkout com escolha de endereço e forma de pagamento, gerando pedido + itens + pagamento
- Painel do restaurante com fila de pedidos e mudança de status (pendente → preparando → pronto)
- Painel do entregador: aceitar pedidos prontos, marcar como entregue
- Acompanhamento de status do pedido em tempo quase real (polling JS a cada 5s)
- Camada Model 100% separada da camada Controller (raw SQL parametrizado via PyMySQL, sem ORM)

## Próximos passos sugeridos

- Trocar polling por WebSocket (Flask-SocketIO) para status em tempo real de verdade
- Adicionar upload de imagem de produto/restaurante (usar `static/img/`)
- Paginação na listagem de restaurantes/pedidos
- Avaliações de restaurante e de entregador
