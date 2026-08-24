import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import AuthLayout from "../components/AuthLayout";
import FormField from "../components/FormField";
import PrimaryButton from "../components/PrimaryButton";
import AlertBanner from "../components/AlertBanner";
import { enviarCodigo, validarCodigo } from "../api/verificacao";
import { extrairErroApi } from "../api/client";

const SEGUNDOS_PARA_REENVIO = 60;

export default function Verificacao() {
  const navigate = useNavigate();
  const location = useLocation();

  // Quem chega aqui vem do cadastro, que passa o id e o e-mail pela rota.
  const { idUsuario, email, codigoEnviado } = location.state || {};

  const [codigo, setCodigo] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erroApi, setErroApi] = useState(null);
  const [sucesso, setSucesso] = useState(false);
  // Sem SMTP configurado no back-end, o código sai no log em vez do e-mail.
  // O valor já é conhecido na primeira renderização, então nasce no estado
  // inicial — não precisa de efeito.
  const [aviso, setAviso] = useState(
    codigoEnviado === false
      ? "O envio por e-mail não está configurado: o código aparece no terminal do back-end."
      : null,
  );
  const [segundos, setSegundos] = useState(SEGUNDOS_PARA_REENVIO);

  useEffect(() => {
    if (!idUsuario) navigate("/cadastro", { replace: true });
  }, [idUsuario, navigate]);

  // Contagem regressiva do reenvio (RF04: liberado após 60 segundos).
  useEffect(() => {
    if (segundos <= 0) return undefined;
    const id = setTimeout(() => setSegundos((s) => s - 1), 1000);
    return () => clearTimeout(id);
  }, [segundos]);


  if (!idUsuario) return null;

  async function handleSubmit(e) {
    e.preventDefault();
    setErroApi(null);

    if (codigo.trim().length !== 6) {
      setErroApi("O código tem 6 dígitos.");
      return;
    }

    setEnviando(true);
    try {
      await validarCodigo(idUsuario, codigo);
      setSucesso(true);
      setTimeout(() => navigate("/login", { replace: true }), 1800);
    } catch (err) {
      setErroApi(extrairErroApi(err).mensagem);
    } finally {
      setEnviando(false);
    }
  }

  async function handleReenviar() {
    setErroApi(null);
    setAviso(null);
    try {
      const dados = await enviarCodigo(idUsuario);
      setSegundos(SEGUNDOS_PARA_REENVIO);
      setCodigo("");
      setAviso(
        dados.enviado_por_email
          ? "Enviamos um novo código."
          : "Novo código gerado. O envio por e-mail não está configurado: veja o terminal do back-end.",
      );
    } catch (err) {
      setErroApi(extrairErroApi(err).mensagem);
    }
  }

  if (sucesso) {
    return (
      <AuthLayout title="Conta verificada" subtitle="Tudo certo!">
        <AlertBanner tone="success">
          Conta verificada com sucesso. Levando você para o login...
        </AlertBanner>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Confirme seu e-mail"
      subtitle={email ? `Enviamos um código de 6 dígitos para ${email}` : "Digite o código de 6 dígitos"}
    >
      <AlertBanner>{erroApi}</AlertBanner>
      {aviso ? <AlertBanner tone="success">{aviso}</AlertBanner> : null}

      <form onSubmit={handleSubmit} noValidate>
        <FormField
          label="Código de verificação"
          placeholder="000000"
          value={codigo}
          onChange={(e) => setCodigo(e.target.value.replace(/\D/g, "").slice(0, 6))}
          inputMode="numeric"
          autoComplete="one-time-code"
          hint="O código vale por 5 minutos."
        />

        <PrimaryButton type="submit" loading={enviando} disabled={codigo.length !== 6}>
          Confirmar
        </PrimaryButton>
      </form>

      <p className="auth-footer">
        {segundos > 0 ? (
          <>Não recebeu? Você pode pedir outro em {segundos}s.</>
        ) : (
          <button type="button" className="auth-footer__link" onClick={handleReenviar}>
            Reenviar código
          </button>
        )}
      </p>

      <p className="auth-footer">
        <Link to="/login" className="auth-footer__link">
          Voltar para o login
        </Link>
      </p>
    </AuthLayout>
  );
}
