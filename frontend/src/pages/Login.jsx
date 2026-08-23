import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthLayout from "../components/AuthLayout";
import FormField from "../components/FormField";
import PasswordField from "../components/PasswordField";
import PrimaryButton from "../components/PrimaryButton";
import AlertBanner from "../components/AlertBanner";
import { entrar } from "../api/auth";
import { emailValido } from "../utils/validators";

export default function Login() {
  const navigate = useNavigate();
  const [identificador, setIdentificador] = useState("");
  const [senha, setSenha] = useState("");
  const [tocado, setTocado] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [erroApi, setErroApi] = useState(null);

  const emailInvalido = tocado && !emailValido(identificador);

  async function handleSubmit(e) {
    e.preventDefault();
    setTocado(true);
    setErroApi(null);

    if (!emailValido(identificador) || senha.length < 1) return;

    setEnviando(true);
    try {
      await entrar({ identificador, senha });
      navigate("/");
    } catch (err) {
      if (err?.response?.status === 404) {
        setErroApi("O login ainda não está disponível: essa rota faz parte do próximo módulo do back-end.");
      } else if (err?.response?.status === 401) {
        setErroApi("E-mail ou senha incorretos.");
      } else {
        setErroApi("Não foi possível entrar agora. Tente novamente em instantes.");
      }
    } finally {
      setEnviando(false);
    }
  }

  return (
    <AuthLayout title="Entrar" subtitle="Acesse sua conta para continuar">
      <AlertBanner>{erroApi}</AlertBanner>

      <form onSubmit={handleSubmit} noValidate>
        <FormField
          label="E-mail"
          placeholder="voce@exemplo.com"
          value={identificador}
          onChange={(e) => setIdentificador(e.target.value)}
          onBlur={() => setTocado(true)}
          error={emailInvalido ? "E-mail inválido" : null}
          autoComplete="email"
        />

        <PasswordField
          label="Senha"
          placeholder="••••••••"
          value={senha}
          onChange={(e) => setSenha(e.target.value)}
          autoComplete="current-password"
        />

        <div className="auth-forgot">
          <Link to="/esqueci-senha" className="auth-forgot__link">
            Esqueceu a senha?
          </Link>
        </div>

        <PrimaryButton
          type="submit"
          loading={enviando}
          disabled={tocado && (emailInvalido || senha.length < 1)}
        >
          Entrar na conta
        </PrimaryButton>
      </form>

      <p className="auth-footer">
        Não tem uma conta?{" "}
        <Link to="/cadastro" className="auth-footer__link">
          Cadastre-se
        </Link>
      </p>
    </AuthLayout>
  );
}
