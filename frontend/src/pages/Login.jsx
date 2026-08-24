import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import AuthLayout from "../components/AuthLayout";
import FormField from "../components/FormField";
import PasswordField from "../components/PasswordField";
import PrimaryButton from "../components/PrimaryButton";
import AlertBanner from "../components/AlertBanner";
import { entrar } from "../api/auth";
import { extrairErroApi } from "../api/client";
import { limparSessao, salvarSessao } from "../auth/sessao";
import { emailValido } from "../utils/validators";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const [identificador, setIdentificador] = useState("");
  const [senha, setSenha] = useState("");
  const [tocado, setTocado] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [erroApi, setErroApi] = useState(null);
  // Guarda o usuario autenticado. Enquanto nao existe uma home para onde
  // redirecionar, a confirmacao do login e a propria tela.
  const [autenticado, setAutenticado] = useState(null);

  const emailInvalido = tocado && !emailValido(identificador);
  const contaExcluida = location.state?.contaExcluida;

  async function handleSubmit(e) {
    e.preventDefault();
    setTocado(true);
    setErroApi(null);

    if (!emailValido(identificador) || senha.length < 1) return;

    setEnviando(true);
    try {
      const usuario = await entrar({ identificador, senha });
      setAutenticado(usuario);
      salvarSessao(usuario);
      setSenha("");
    } catch (err) {
      // 401 e 403 trazem mensagem propria da API: a de credencial e generica de
      // proposito, e a de conta pendente/bloqueada diz o que fazer em seguida.
      setErroApi(extrairErroApi(err).mensagem);
    } finally {
      setEnviando(false);
    }
  }

  if (autenticado) {
    return (
      <AuthLayout title="Entrar" subtitle="Acesse sua conta para continuar">
        <AlertBanner tone="success">
          Login realizado com sucesso! Bem-vindo(a), {autenticado.nome_completo}.
        </AlertBanner>

        <p className="auth-footer">
          Ainda não existe uma página inicial — ela chega no próximo módulo.
        </p>

        <PrimaryButton type="button" onClick={() => navigate("/perfil")}>
          Ver e alterar meus dados
        </PrimaryButton>

        <p className="auth-footer">
          <button
            type="button"
            className="auth-footer__link"
            onClick={() => {
              limparSessao();
              setAutenticado(null);
              setIdentificador("");
              setTocado(false);
            }}
          >
            Sair
          </button>
        </p>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Entrar" subtitle="Acesse sua conta para continuar">
      <AlertBanner>{erroApi}</AlertBanner>
      {contaExcluida ? (
        <AlertBanner tone="success">
          Sua conta foi excluída. Obrigado por usar o Yummi!
        </AlertBanner>
      ) : null}

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
