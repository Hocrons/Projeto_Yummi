-- =========================================================
-- Yummi/Yummy - Schema MySQL
-- Baseado no "Modelo de Dados Físico — Sistema Yummi"
-- =========================================================

CREATE DATABASE IF NOT EXISTS yummy
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE yummy;

-- ---------------------------------------------------------
-- usuario (tabela mãe: cliente, restaurante e entregador
-- herdam id_usuario como PK/FK - table-per-subtype)
-- ---------------------------------------------------------
CREATE TABLE usuario (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    nome           VARCHAR(100) NOT NULL,
    email          VARCHAR(100) NOT NULL UNIQUE,
    senha          VARCHAR(255) NOT NULL,
    telefone       VARCHAR(20),
    tipo           VARCHAR(20)  NOT NULL,   -- 'cliente' | 'restaurante' | 'entregador'
    data_cadastro  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- restaurante (1:1 com usuario) - endereço fica direto aqui
-- ---------------------------------------------------------
CREATE TABLE restaurante (
    id_usuario             INT PRIMARY KEY,
    nome_fantasia          VARCHAR(100) NOT NULL,
    cnpj                   VARCHAR(20)  NOT NULL,
    categoria              VARCHAR(50),
    taxa_entrega           DECIMAL(10,2) NOT NULL DEFAULT 0,
    horario_funcionamento  VARCHAR(100),
    rua                    VARCHAR(100),
    numero                 VARCHAR(10),
    bairro                 VARCHAR(50),
    cidade                 VARCHAR(50),
    cep                    VARCHAR(10),
    CONSTRAINT fk_restaurante_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuario(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- cliente (1:1 com usuario)
-- ---------------------------------------------------------
CREATE TABLE cliente (
    id_usuario  INT PRIMARY KEY,
    cpf         VARCHAR(11) NOT NULL UNIQUE,
    apelido     VARCHAR(50),
    CONSTRAINT fk_cliente_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuario(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- entregador (1:1 com usuario)
-- ---------------------------------------------------------
CREATE TABLE entregador (
    id_usuario  INT PRIMARY KEY,
    cpf         VARCHAR(11) NOT NULL UNIQUE,
    veiculo     VARCHAR(50),
    placa       VARCHAR(10),
    disponivel  BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_entregador_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuario(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- produto (N:1 com restaurante)
-- ---------------------------------------------------------
CREATE TABLE produto (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    id_restaurante INT NOT NULL,
    nome           VARCHAR(100) NOT NULL,
    descricao      VARCHAR(255),
    preco          DECIMAL(10,2) NOT NULL,
    disponivel     BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_produto_restaurante
        FOREIGN KEY (id_restaurante) REFERENCES restaurante(id_usuario) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- endereco (N:1 com cliente - cliente pode ter vários)
-- ---------------------------------------------------------
CREATE TABLE endereco (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    rua        VARCHAR(100) NOT NULL,
    numero     VARCHAR(10),
    bairro     VARCHAR(50),
    cidade     VARCHAR(50),
    cep        VARCHAR(10),
    CONSTRAINT fk_endereco_cliente
        FOREIGN KEY (id_cliente) REFERENCES cliente(id_usuario) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- pedido
-- ---------------------------------------------------------
CREATE TABLE pedido (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente     INT NOT NULL,
    id_restaurante INT NOT NULL,
    id_entregador  INT NULL,
    id_endereco    INT NULL,
    data_hora      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status         VARCHAR(20) NOT NULL DEFAULT 'pendente',
    -- pendente | preparando | pronto | saiu_entrega | entregue | cancelado
    valor_total    DECIMAL(10,2) NOT NULL DEFAULT 0,
    CONSTRAINT fk_pedido_cliente
        FOREIGN KEY (id_cliente) REFERENCES cliente(id_usuario),
    CONSTRAINT fk_pedido_restaurante
        FOREIGN KEY (id_restaurante) REFERENCES restaurante(id_usuario),
    CONSTRAINT fk_pedido_entregador
        FOREIGN KEY (id_entregador) REFERENCES entregador(id_usuario),
    CONSTRAINT fk_pedido_endereco
        FOREIGN KEY (id_endereco) REFERENCES endereco(id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- item_pedido (N:N entre pedido e produto)
-- ---------------------------------------------------------
CREATE TABLE item_pedido (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    id_pedido      INT NOT NULL,
    id_produto     INT NOT NULL,
    quantidade     INT NOT NULL DEFAULT 1,
    preco_unitario DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_item_pedido
        FOREIGN KEY (id_pedido) REFERENCES pedido(id) ON DELETE CASCADE,
    CONSTRAINT fk_item_produto
        FOREIGN KEY (id_produto) REFERENCES produto(id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- pagamento
-- ---------------------------------------------------------
CREATE TABLE pagamento (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    id_pedido       INT NOT NULL,
    forma_pagamento VARCHAR(20) NOT NULL,  -- cartao | pix | dinheiro
    valor           DECIMAL(10,2) NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'pendente', -- pendente | aprovado | recusado
    CONSTRAINT fk_pagamento_pedido
        FOREIGN KEY (id_pedido) REFERENCES pedido(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- Dados de exemplo para testar rapidamente
-- (senha "123456" já em hash Werkzeug para todos)
-- ---------------------------------------------------------
INSERT INTO usuario (nome, email, senha, telefone, tipo) VALUES
('Restaurante Sabor Caseiro', 'restaurante@yummy.com',
 'scrypt:32768:8:1$0Y6Cg1YQZq2eK6r5$8f7e1a1b0c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f',
 '11999990000', 'restaurante');

-- Observação: os INSERTs de exemplo com senha em hash real serão
-- gerados automaticamente pelo próprio app na hora do cadastro.
-- Recomenda-se cadastrar os usuários de teste pela tela /auth/registro
-- em vez de usar hash fixo aqui (evita incompatibilidade de versão do Werkzeug).
