-- =====================================================================
-- Yummi - Modelo de dados fisico
-- MySQL 8.0+
--
-- ARQUIVO GERADO. Nao edite a mao.
-- Fonte: os models SQLAlchemy em backend/app/models/.
-- Para regenerar:  python scripts/gerar_schema_sql.py
-- =====================================================================

DROP DATABASE IF EXISTS yummi;
CREATE DATABASE yummi
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;
USE yummi;


-- ---------------------------------------------- USUARIO
CREATE TABLE `USUARIO` (
	id_usuario INTEGER NOT NULL AUTO_INCREMENT, 
	nome_completo VARCHAR(100) NOT NULL, 
	email VARCHAR(254), 
	celular VARCHAR(15), 
	cpf CHAR(11) NOT NULL, 
	rg VARCHAR(20), 
	data_nascimento DATE NOT NULL, 
	senha_hash VARCHAR(128), 
	tipo_usuario VARCHAR(20) NOT NULL DEFAULT 'cliente', 
	status_conta VARCHAR(20) NOT NULL DEFAULT 'pendente', 
	provedor_social VARCHAR(20), 
	id_social VARCHAR(100), 
	data_cadastro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	CONSTRAINT `pk_USUARIO` PRIMARY KEY (id_usuario), 
	CONSTRAINT `ck_USUARIO_tipo` CHECK (tipo_usuario IN ('cliente','restaurante','entregador','admin')), 
	CONSTRAINT `ck_USUARIO_status` CHECK (status_conta IN ('pendente','ativo','bloqueado','excluido')), 
	CONSTRAINT `ck_USUARIO_provedor` CHECK (provedor_social IS NULL OR provedor_social IN ('google','facebook')), 
	CONSTRAINT `ck_USUARIO_contato` CHECK (email IS NOT NULL OR celular IS NOT NULL), 
	CONSTRAINT `ck_USUARIO_senha` CHECK (senha_hash IS NOT NULL OR provedor_social IS NOT NULL), 
	CONSTRAINT `uk_USUARIO_email` UNIQUE (email), 
	CONSTRAINT `uk_USUARIO_celular` UNIQUE (celular), 
	CONSTRAINT `uk_USUARIO_cpf` UNIQUE (cpf)
)CHARSET=utf8mb4 ENGINE=InnoDB;


-- ---------------------------------------------- CODIGO_OTP
CREATE TABLE `CODIGO_OTP` (
	id_otp INTEGER NOT NULL AUTO_INCREMENT, 
	id_usuario INTEGER NOT NULL, 
	codigo CHAR(6) NOT NULL, 
	canal VARCHAR(20) NOT NULL, 
	finalidade VARCHAR(20) NOT NULL, 
	criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	expira_em DATETIME NOT NULL, 
	tentativas INTEGER NOT NULL DEFAULT 0, 
	validado BOOL NOT NULL DEFAULT 0, 
	CONSTRAINT `pk_CODIGO_OTP` PRIMARY KEY (id_otp), 
	CONSTRAINT `ck_CODIGO_OTP_canal` CHECK (canal IN ('whatsapp','sms','email')), 
	CONSTRAINT `ck_CODIGO_OTP_finalidade` CHECK (finalidade IN ('cadastro','login')), 
	CONSTRAINT `ck_CODIGO_OTP_codigo` CHECK (LENGTH(codigo) = 6), 
	CONSTRAINT `ck_CODIGO_OTP_tentativas` CHECK (tentativas BETWEEN 0 AND 5), 
	CONSTRAINT `fk_CODIGO_OTP_id_usuario` FOREIGN KEY(id_usuario) REFERENCES `USUARIO` (id_usuario)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE INDEX `ix_CODIGO_OTP_id_usuario` ON `CODIGO_OTP` (id_usuario);
