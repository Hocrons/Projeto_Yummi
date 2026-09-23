-- =========================================================
-- Yummy - Schema MySQL
-- Baseado no "Modelo de Dados Físico — Sistema Yummi"
-- =========================================================

DROP DATABASE IF EXISTS yummy;
CREATE DATABASE yummy
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE yummy;

-- ---------------------------------------------------------
-- plano (planos de assinatura do restaurante)
-- ---------------------------------------------------------
CREATE TABLE plano (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nome            VARCHAR(50) NOT NULL,
    descricao       VARCHAR(255),
    mensalidade     DECIMAL(10,2) NOT NULL DEFAULT 0,
    comissao_pct    DECIMAL(5,2)  NOT NULL DEFAULT 0,
    taxa_cartao_pct DECIMAL(5,2)  NOT NULL DEFAULT 0,
    entrega_propria BOOLEAN NOT NULL DEFAULT FALSE,
    ativo           BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

INSERT INTO plano (nome, descricao, mensalidade, comissao_pct, taxa_cartao_pct, entrega_propria, ativo) VALUES
('Básico',      'Ideal pra quem está começando. Comissão maior, sem mensalidade.',              0.00,  12.00, 3.20, FALSE, TRUE),
('Crescimento', 'Mais pedidos, menos comissão. Pra quem já vende bem.',                          69.90,  8.00,  3.20, FALSE, TRUE),
('Pro',         'Entrega própria + comissão reduzida. Você gerencia seus entregadores.',        149.90, 5.00,  2.80, TRUE,  TRUE);

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
    tem_mesa               BOOLEAN NOT NULL DEFAULT FALSE,
    complemento            VARCHAR(50),
    cpf_representante      VARCHAR(11),
    nome_representante     VARCHAR(100),
    data_nasc_representante DATE,
    id_plano               INT NULL,
    foto_url               VARCHAR(500),
    CONSTRAINT fk_restaurante_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuario(id) ON DELETE CASCADE,
    CONSTRAINT fk_restaurante_plano
        FOREIGN KEY (id_plano) REFERENCES plano(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- cliente (1:1 com usuario)
-- ---------------------------------------------------------
CREATE TABLE cliente (
    id_usuario      INT PRIMARY KEY,
    cpf             VARCHAR(11) NOT NULL UNIQUE,
    apelido         VARCHAR(50),
    codigo_entrega  VARCHAR(4),
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
    foto_url       VARCHAR(500),
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
    ativo      TINYINT(1) NOT NULL DEFAULT 1,
    CONSTRAINT fk_endereco_cliente
        FOREIGN KEY (id_cliente) REFERENCES cliente(id_usuario) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- pedido
-- ---------------------------------------------------------
CREATE TABLE pedido (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente      INT NOT NULL,
    id_restaurante  INT NOT NULL,
    id_entregador   INT NULL,
    id_endereco     INT NULL,
    data_hora       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status          VARCHAR(30) NOT NULL DEFAULT 'pendente',
    -- pendente | preparando | localizando_entregador | indo_ao_restaurante
    -- | saiu_para_entrega | entregue | cancelado
    valor_total     DECIMAL(10,2) NOT NULL DEFAULT 0,
    codigo_entrega  VARCHAR(4),
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