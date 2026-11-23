-- Dados ficticios para demonstracao, dependentes de database.sql e
-- seed_restaurantes_ficticios.sql. Nao representam transacoes reais.
-- Execute em MySQL 8.0, na mesma sessao. Reexecutar substitui somente os
-- pedidos associados aos clientes cliente.demo.vendas.*@example.invalid.
--
-- Distribuicao mensal por restaurante:
--   restaurantes 001-005: 22 a 36 pedidos (volume alto, crescente)
--   restaurantes 006-015: 8 a 15 pedidos (volume medio, crescente)
--   restaurantes 016-050: 1 a 3 pedidos (volume baixo)
-- Com o catalogo da seed, sao gerados 2.641 pedidos, dos quais 263 cancelados.
-- O periodo cobre os ultimos 8 meses-calendario, ate ontem. Sao geradas
-- vendas concluidas e canceladas, com 1-3 produtos por pedido.
-- Identificadores de gateway com prefixo "demo-" sao ficticios.

USE yummy;
SET NAMES utf8mb4;

DROP TEMPORARY TABLE IF EXISTS tmp_seed_venda_num;
CREATE TEMPORARY TABLE tmp_seed_venda_num (
    n INT NOT NULL PRIMARY KEY
) ENGINE=MEMORY;

INSERT INTO tmp_seed_venda_num (n) VALUES
    (1),(2),(3),(4),(5),(6),(7),(8),(9),(10),
    (11),(12),(13),(14),(15),(16),(17),(18),(19),(20),
    (21),(22),(23),(24),(25),(26),(27),(28),(29),(30),
    (31),(32),(33),(34),(35),(36),(37),(38),(39),(40),
    (41),(42),(43),(44),(45),(46),(47),(48),(49),(50);

SET @senha_demo = 'scrypt:32768:8:1$d9cxhqbNPOMAe16n$ad384fee38c921f556570fdc32765220da995cfd9a4951ba2bb71edecdf2fd111402e0ebc48bc7ec65abb6f32377b59bfba484e28927f2955e6abc2a70dca884';

-- Clientes e enderecos exclusivos para os pedidos de apresentacao.
START TRANSACTION;

INSERT INTO usuario (nome, email, senha, telefone, tipo)
SELECT CONCAT('Cliente Demo ', LPAD(n.n, 3, '0')),
       CONCAT('cliente.demo.vendas.', LPAD(n.n, 3, '0'), '@example.invalid'),
       @senha_demo,
       CONCAT('+5511998', LPAD(n.n, 6, '0')),
       'cliente'
FROM tmp_seed_venda_num n
WHERE NOT EXISTS (
    SELECT 1
    FROM usuario u
    WHERE u.email = CONCAT(
        'cliente.demo.vendas.', LPAD(n.n, 3, '0'), '@example.invalid'
    )
      AND u.tipo = 'cliente'
);

INSERT INTO cliente (id_usuario, cpf, apelido)
SELECT u.id,
       CONCAT('987654321', LPAD(n.n, 2, '0')),
       CONCAT('Demo ', LPAD(n.n, 3, '0'))
FROM tmp_seed_venda_num n
JOIN usuario u
  ON u.email = CONCAT(
      'cliente.demo.vendas.', LPAD(n.n, 3, '0'), '@example.invalid'
  )
 AND u.tipo = 'cliente'
WHERE NOT EXISTS (
    SELECT 1 FROM cliente c WHERE c.id_usuario = u.id
);

-- Apaga apenas vendas/endereco de demonstracao, para permitir reexecucao.
DELETE p
FROM pedido p
JOIN usuario u ON u.id = p.id_cliente
WHERE u.tipo = 'cliente'
  AND u.email LIKE 'cliente.demo.vendas.%@example.invalid';

DELETE e
FROM endereco e
JOIN usuario u ON u.id = e.id_cliente
WHERE u.tipo = 'cliente'
  AND u.email LIKE 'cliente.demo.vendas.%@example.invalid'
  AND e.rua = 'Rua Demo Yummy';

INSERT INTO endereco (id_cliente, rua, numero, bairro, cidade, cep, ativo)
SELECT u.id, 'Rua Demo Yummy', LPAD(n.n, 4, '0'),
       'Centro', 'Sao Paulo', '01000-000', 1
FROM tmp_seed_venda_num n
JOIN usuario u
  ON u.email = CONCAT(
      'cliente.demo.vendas.', LPAD(n.n, 3, '0'), '@example.invalid'
  )
 AND u.tipo = 'cliente';

COMMIT;

DROP TEMPORARY TABLE IF EXISTS tmp_seed_venda_item;
CREATE TEMPORARY TABLE tmp_seed_venda_item (
    seed_order BIGINT NOT NULL,
    id_produto INT NOT NULL,
    quantidade INT NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (seed_order, id_produto)
) ENGINE=MEMORY;

DROP PROCEDURE IF EXISTS seed_vendas_apresentacao;
DELIMITER $$
CREATE PROCEDURE seed_vendas_apresentacao()
BEGIN
    DECLARE v_done BOOLEAN DEFAULT FALSE;
    DECLARE v_rest_count INT DEFAULT 0;
    DECLARE v_client_count INT DEFAULT 0;
    DECLARE v_rest_id INT;
    DECLARE v_rest_no INT;
    DECLARE v_month_index INT;
    DECLARE v_order_count INT;
    DECLARE v_order_index INT;
    DECLARE v_item_count INT;
    DECLARE v_item_index INT;
    DECLARE v_item_offset INT;
    DECLARE v_product_count INT;
    DECLARE v_product_id INT;
    DECLARE v_product_price DECIMAL(10,2);
    DECLARE v_quantity INT;
    DECLARE v_client_id INT;
    DECLARE v_address_id INT;
    DECLARE v_fee DECIMAL(10,2);
    DECLARE v_subtotal DECIMAL(10,2);
    DECLARE v_total DECIMAL(10,2);
    DECLARE v_first_month DATE;
    DECLARE v_month_start DATE;
    DECLARE v_month_end DATE;
    DECLARE v_order_day DATE;
    DECLARE v_order_at DATETIME;
    DECLARE v_delivered_at DATETIME;
    DECLARE v_day_count INT;
    DECLARE v_delivery_minutes INT;
    DECLARE v_seed_order BIGINT DEFAULT 0;
    DECLARE v_order_id INT;
    DECLARE v_payment_method VARCHAR(20);
    DECLARE v_payment_status VARCHAR(20);
    DECLARE v_order_status VARCHAR(30);
    DECLARE v_gateway_order VARCHAR(100);
    DECLARE v_gateway_transaction VARCHAR(100);

    DECLARE cur_rest CURSOR FOR
        SELECT r.id_usuario,
               CAST(
                   SUBSTRING_INDEX(
                       SUBSTRING_INDEX(u.email, '@', 1), '.', -1
                   ) AS UNSIGNED
               )
        FROM restaurante r
        JOIN usuario u ON u.id = r.id_usuario
        WHERE u.tipo = 'restaurante'
          AND u.email LIKE 'restaurante.demo.%@example.invalid'
        ORDER BY u.email;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = TRUE;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SELECT COUNT(DISTINCT r.id_usuario)
      INTO v_rest_count
    FROM restaurante r
    JOIN usuario u ON u.id = r.id_usuario
    WHERE u.tipo = 'restaurante'
      AND u.email LIKE 'restaurante.demo.%@example.invalid';

    SELECT COUNT(*)
      INTO v_client_count
    FROM cliente c
    JOIN usuario u ON u.id = c.id_usuario
    WHERE u.tipo = 'cliente'
      AND u.email LIKE 'cliente.demo.vendas.%@example.invalid';

    IF v_rest_count <> 50 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'Execute primeiro seed_restaurantes_ficticios.sql (50 restaurantes).';
    END IF;

    IF v_client_count <> 50 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Os 50 clientes demonstrativos nao foram preparados.';
    END IF;

    SET v_first_month = STR_TO_DATE(
        DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 7 MONTH), '%Y-%m-01'),
        '%Y-%m-%d'
    );

    START TRANSACTION;
    OPEN cur_rest;

    restaurant_loop: LOOP
        FETCH cur_rest INTO v_rest_id, v_rest_no;
        IF v_done THEN
            LEAVE restaurant_loop;
        END IF;

        SELECT COUNT(*)
          INTO v_product_count
        FROM produto
        WHERE id_restaurante = v_rest_id
          AND disponivel = 1;

        IF v_product_count > 0 THEN
            SELECT COALESCE(taxa_entrega, 0)
              INTO v_fee
            FROM restaurante
            WHERE id_usuario = v_rest_id;

            SET v_month_index = 0;
            WHILE v_month_index < 8 DO
                SET v_month_start =
                    DATE_ADD(v_first_month, INTERVAL v_month_index MONTH);
                SET v_month_end = LEAST(
                    LAST_DAY(v_month_start),
                    DATE_SUB(CURDATE(), INTERVAL 1 DAY)
                );

                IF v_month_end >= v_month_start THEN
                    IF v_rest_no BETWEEN 1 AND 5 THEN
                        SET v_order_count = 22 + (2 * v_month_index);
                    ELSEIF v_rest_no BETWEEN 6 AND 15 THEN
                        SET v_order_count = 8 + v_month_index;
                    ELSE
                        SET v_order_count =
                            1 + MOD(v_rest_no + v_month_index, 3);
                    END IF;

                    SET v_day_count =
                        DATEDIFF(v_month_end, v_month_start) + 1;
                    SET v_order_index = 1;

                    WHILE v_order_index <= v_order_count DO
                        SELECT c.id_usuario, e.id
                          INTO v_client_id, v_address_id
                        FROM cliente c
                        JOIN usuario u ON u.id = c.id_usuario
                        JOIN endereco e
                          ON e.id_cliente = c.id_usuario
                         AND e.ativo = 1
                        WHERE u.email LIKE 'cliente.demo.vendas.%@example.invalid'
                        ORDER BY RAND()
                        LIMIT 1;

                        SET v_order_day = DATE_ADD(
                            v_month_start,
                            INTERVAL FLOOR(RAND() * v_day_count) DAY
                        );
                        SET v_order_at = TIMESTAMP(
                            v_order_day,
                            MAKETIME(
                                11 + FLOOR(RAND() * 10),
                                FLOOR(RAND() * 60),
                                0
                            )
                        );
                        SET v_delivery_minutes =
                            30 + FLOOR(RAND() * 61);
                        SET v_order_status = IF(
                            MOD(
                                v_order_index + v_rest_no + v_month_index,
                                10
                            ) = 0,
                            'cancelado',
                            'entregue'
                        );
                        SET v_delivered_at = IF(
                            v_order_status = 'entregue',
                            DATE_ADD(
                                v_order_at,
                                INTERVAL v_delivery_minutes MINUTE
                            ),
                            NULL
                        );

                        SET v_item_count = LEAST(
                            v_product_count,
                            1 + MOD(
                                v_order_index + v_rest_no + v_month_index, 3
                            )
                        );
                        SET v_subtotal = 0;
                        SET v_seed_order = v_seed_order + 1;
                        SET v_item_index = 0;

                        WHILE v_item_index < v_item_count DO
                            SET v_item_offset = MOD(
                                v_order_index + v_rest_no + v_month_index
                                    + v_item_index,
                                v_product_count
                            );

                            SELECT id, preco
                              INTO v_product_id, v_product_price
                            FROM produto
                            WHERE id_restaurante = v_rest_id
                              AND disponivel = 1
                            ORDER BY id
                            LIMIT v_item_offset, 1;

                            SET v_quantity =
                                1 + MOD(v_order_index + v_item_index, 2);

                            INSERT INTO tmp_seed_venda_item
                                (seed_order, id_produto, quantidade, preco_unitario)
                            VALUES
                                (v_seed_order, v_product_id, v_quantity, v_product_price);

                            SET v_subtotal =
                                v_subtotal + (v_product_price * v_quantity);
                            SET v_item_index = v_item_index + 1;
                        END WHILE;

                        SET v_total = ROUND(v_subtotal + v_fee, 2);

                        INSERT INTO pedido
                            (id_cliente, id_restaurante, id_endereco,
                             data_hora, entregue_em, status, tipo_entrega,
                             valor_total, taxa_entrega_cobrada)
                        VALUES
                            (v_client_id, v_rest_id, v_address_id,
                             v_order_at, v_delivered_at, v_order_status,
                             IF(v_order_status = 'entregue', 'propria', NULL),
                             v_total, v_fee);

                        SET v_order_id = LAST_INSERT_ID();

                        INSERT INTO item_pedido
                            (id_pedido, id_produto, quantidade, preco_unitario)
                        SELECT v_order_id, id_produto, quantidade, preco_unitario
                        FROM tmp_seed_venda_item
                        WHERE seed_order = v_seed_order;

                        DELETE FROM tmp_seed_venda_item
                        WHERE seed_order = v_seed_order;

                        SET v_payment_method =
                            IF(MOD(v_seed_order, 5) = 0, 'dinheiro', 'infinitepay');
                        SET v_payment_status = IF(
                            v_order_status = 'cancelado',
                            'cancelado',
                            'aprovado'
                        );

                        IF v_payment_method = 'infinitepay' THEN
                            SET v_gateway_order =
                                CONCAT('demo-yummy-order-', v_order_id);
                            SET v_gateway_transaction = IF(
                                v_order_status = 'entregue',
                                CONCAT('demo-yummy-txn-', v_order_id),
                                NULL
                            );
                        ELSE
                            SET v_gateway_order = NULL;
                            SET v_gateway_transaction = NULL;
                        END IF;

                        INSERT INTO pagamento
                            (id_pedido, forma_pagamento, valor, status,
                             gateway_order_nsu, gateway_transaction_nsu,
                             gateway_slug)
                        VALUES
                            (v_order_id, v_payment_method, v_total,
                             v_payment_status,
                             v_gateway_order, v_gateway_transaction,
                             IF(v_payment_method = 'infinitepay'
                                    AND v_order_status = 'entregue',
                                'demo-apresentacao', NULL));

                        SET v_order_index = v_order_index + 1;
                    END WHILE;
                END IF;

                SET v_month_index = v_month_index + 1;
            END WHILE;
        END IF;
    END LOOP;

    CLOSE cur_rest;
    COMMIT;
END$$
DELIMITER ;

CALL seed_vendas_apresentacao();
DROP PROCEDURE seed_vendas_apresentacao;

-- Resumo geral das vendas de demonstracao.
SELECT COUNT(*) AS pedidos_total,
       COALESCE(SUM(p.status = 'entregue'), 0) AS pedidos_concluidos,
       COALESCE(SUM(p.status = 'cancelado'), 0) AS pedidos_cancelados,
       ROUND(COALESCE(SUM(
           CASE WHEN p.status <> 'cancelado' THEN p.valor_total ELSE 0 END
       ), 0), 2) AS faturamento,
       MIN(p.data_hora) AS primeira_venda,
       MAX(p.data_hora) AS venda_mais_recente
FROM pedido p
JOIN usuario u ON u.id = p.id_cliente
WHERE u.email LIKE 'cliente.demo.vendas.%@example.invalid'
  AND p.status = 'entregue'
  AND p.data_hora >= STR_TO_DATE(
      DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 7 MONTH), '%Y-%m-01'),
      '%Y-%m-%d'
  );

-- Ranking para conferir a diferenca de volume entre restaurantes.
SELECT r.nome_fantasia,
       COUNT(p.id) AS pedidos_total,
       COALESCE(SUM(p.status = 'entregue'), 0) AS pedidos_concluidos,
       COALESCE(SUM(p.status = 'cancelado'), 0) AS pedidos_cancelados,
       ROUND(COALESCE(SUM(
           CASE WHEN p.status <> 'cancelado' THEN p.valor_total ELSE 0 END
       ), 0), 2) AS faturamento
FROM restaurante r
JOIN usuario ur ON ur.id = r.id_usuario
LEFT JOIN pedido p
  ON p.id_restaurante = r.id_usuario
 AND p.status IN ('entregue', 'cancelado')
 AND p.data_hora >= STR_TO_DATE(
     DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 7 MONTH), '%Y-%m-01'),
     '%Y-%m-%d'
 )
 AND p.id_cliente IN (
     SELECT uc.id
     FROM usuario uc
     WHERE uc.tipo = 'cliente'
       AND uc.email LIKE 'cliente.demo.vendas.%@example.invalid'
 )
WHERE ur.email LIKE 'restaurante.demo.%@example.invalid'
GROUP BY r.id_usuario, r.nome_fantasia
ORDER BY faturamento DESC, pedidos_total DESC;

DROP TEMPORARY TABLE tmp_seed_venda_item;
DROP TEMPORARY TABLE tmp_seed_venda_num;
