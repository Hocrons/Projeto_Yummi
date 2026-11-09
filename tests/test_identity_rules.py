import unittest
import sys
import types
from flask import Flask, session
from unittest.mock import patch

# The controller imports the PDF service, which is not needed by these tests.
xhtml2pdf_stub = types.ModuleType("xhtml2pdf")
xhtml2pdf_stub.pisa = types.SimpleNamespace(
    CreatePDF=lambda *args, **kwargs: None
)
sys.modules.setdefault("xhtml2pdf", xhtml2pdf_stub)

from controllers import auth_ctrl
from models import migrations, models


class RecordingCursor:
    def __init__(self):
        self.statements = []
        self.lastrowid = 17
        self.result = None
        self.rows = []

    def execute(self, query, params=None):
        self.statements.append((query, params))
        if "SELECT tipo FROM usuario" in query:
            self.result = {"tipo": "cliente"}
        elif "SELECT id FROM usuario" in query:
            self.result = None
        else:
            self.result = None

    def fetchone(self):
        return self.result

    def fetchall(self):
        return self.rows


class RecordingDB:
    def __init__(self):
        self.cursor = RecordingCursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class IdentityRuleTests(unittest.TestCase):
    def test_create_user_normalizes_email_and_phone(self):
        database = RecordingDB()
        with patch.object(models, "DB", return_value=database):
            user_id = models.criar_usuario(
                "Ana", "  ANA@EXEMPLO.COM ", "secret", "(11) 99999-1234", "cliente"
            )

        self.assertEqual(user_id, 17)
        insert = database.cursor.statements[0]
        self.assertEqual(insert[1][1], "ana@exemplo.com")
        self.assertEqual(insert[1][3], "5511999991234")

    def test_create_user_rejects_invalid_contact_values(self):
        with self.assertRaisesRegex(ValueError, "e-mail válido"):
            models.criar_usuario("Ana", "", "secret", "11999991234", "cliente")

        with self.assertRaisesRegex(ValueError, "telefone válido"):
            models.criar_usuario(
                "Ana", "ana@exemplo.com", "secret", "123", "cliente"
            )

    def test_email_lookup_is_scoped_to_profile_type(self):
        database = RecordingDB()
        with patch.object(models, "DB", return_value=database):
            models.buscar_usuario_por_email_e_tipo(" Ana@Exemplo.com ", "cliente")

        query, params = database.cursor.statements[0]
        self.assertIn("email=%s AND tipo=%s", query)
        self.assertEqual(params, ("ana@exemplo.com", "cliente"))

    def test_phone_lookup_is_scoped_to_profile_type(self):
        database = RecordingDB()
        with patch.object(models, "DB", return_value=database):
            models.buscar_usuario_por_telefone("11999991234", "restaurante")

        query, params = database.cursor.statements[0]
        self.assertIn("telefone=%s AND tipo=%s", query)
        self.assertEqual(params, ("5511999991234", "restaurante"))

    def test_google_login_finds_existing_customer_case_insensitively(self):
        app = Flask(__name__)
        app.secret_key = "test"
        usuario = {"id": 1, "nome": "Ana"}
        with app.test_request_context("/"):
            with (
                patch.object(
                    models, "buscar_usuario_por_email_e_tipo", return_value=usuario
                ) as buscar,
                patch.object(auth_ctrl, "_logar_usuario_cliente"),
                patch.object(auth_ctrl, "url_for", return_value="/home"),
            ):
                response = auth_ctrl._login_ou_cadastrar_social(
                    "Ana@Exemplo.com", "Ana", "google"
                )

        buscar.assert_called_once_with("ana@exemplo.com", "cliente")
        self.assertEqual(response.location, "/home")

    def test_google_login_starts_customer_registration_if_only_other_role_exists(self):
        app = Flask(__name__)
        app.secret_key = "test"
        with app.test_request_context("/"):
            with (
                patch.object(models, "buscar_usuario_por_email_e_tipo", return_value=None),
                patch.object(auth_ctrl, "url_for", return_value="/complete-registration"),
            ):
                response = auth_ctrl._login_ou_cadastrar_social(
                    "Ana@Exemplo.com", "Ana", "google"
                )

            self.assertEqual(
                session["cadastro_social"]["email"],
                "ana@exemplo.com",
            )

        self.assertEqual(response.location, "/complete-registration")

    def test_migration_allows_contact_reuse_across_profile_types(self):
        class MigrationCursor:
            def __init__(self):
                self.statements = []
                self.result = []

            def execute(self, query, params=None):
                self.statements.append((query, params))
                if query.startswith("SELECT id, email, telefone, tipo"):
                    self.result = [
                        {
                            "id": 1,
                            "email": "ana@example.com",
                            "telefone": "(11) 99999-1234",
                            "tipo": "cliente",
                        },
                        {
                            "id": 2,
                            "email": "ana@example.com",
                            "telefone": "5511999991234",
                            "tipo": "restaurante",
                        },
                    ]
                else:
                    self.result = []

            def fetchall(self):
                return self.result

        cursor = MigrationCursor()
        migrations._add_role_scoped_contact_uniqueness(cursor)

        updates = [
            params
            for query, params in cursor.statements
            if query.startswith("UPDATE usuario SET")
        ]
        self.assertEqual(
            updates,
            [
                ("ana@example.com", "5511999991234", 1),
                ("ana@example.com", "5511999991234", 2),
            ],
        )
        self.assertTrue(
            any("uq_usuario_email_tipo" in query for query, _ in cursor.statements)
        )
        self.assertTrue(
            any("uq_usuario_telefone_tipo" in query for query, _ in cursor.statements)
        )

    def test_migration_rejects_duplicate_contact_within_profile_type(self):
        class MigrationCursor:
            def execute(self, query, params=None):
                if query.startswith("SELECT id, email, telefone, tipo"):
                    self.result = [
                        {
                            "id": 1,
                            "email": "ana@example.com",
                            "telefone": "11999991234",
                            "tipo": "cliente",
                        },
                        {
                            "id": 2,
                            "email": "outra@example.com",
                            "telefone": "5511999991234",
                            "tipo": "cliente",
                        },
                    ]

            def fetchall(self):
                return self.result

        with self.assertRaisesRegex(RuntimeError, "telefones duplicados"):
            migrations._add_role_scoped_contact_uniqueness(MigrationCursor())


if __name__ == "__main__":
    unittest.main()
