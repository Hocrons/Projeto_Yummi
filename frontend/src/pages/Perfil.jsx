import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import AuthLayout from "../components/AuthLayout";
import FormField from "../components/FormField";
import PasswordField from "../components/PasswordField";
import PrimaryButton from "../components/PrimaryButton";
import AlertBanner from "../components/AlertBanner";
import { atualizarUsuario, excluirUsuario } from "../api/usuarios";
import { extrairErroApi } from "../api/client";
import { lerSessao, limparSessao, salvarSessao } from "../auth/sessao";
import {
  aplicarMascaraCelular,
  aplicarMascaraCpf,
  celularValido,
  emailValido,
  idadeMinimaOk,
  nomeCompletoValido,
  senhaValida,
  somenteDigitos,
} from "../utils/validators";
import "./Perfil.css";

// Traduz o campo que a API acusou para o campo do formulário.
const CAMPO_PARA_ERRO = {
  nome_completo: "nomeCompleto",
  email: "email",
  celular: "celular",
  data_nascimento: "dataNascimento",
  senha: "senha",
  contato: "email",
};

function formularioInicial(usuario) {
  return {
    nomeCompleto: usuario.nome_completo || "",
    email: usuario.email || "",
    celular: usuario.celular ? aplicarMascaraCelular(usuario.celular) : "",
    rg: usuario.rg || "",
    dataNascimento: usuario.data_nascimento || "",
    senha: "",
  };
}

export default function Perfil() {
  const navigate = useNavigate();
  const [usuario, setUsuario] = useState(() => lerSessao());
  const [form, setForm] = useState(() => {
    const sessao = lerSessao();
    return sessao ? formularioInicial(sessao) : null;
  });

  const [enviando, setEnviando] = useState(false);
  const [erroApi, setErroApi] = useState(null);
  const [campoComErro, setCampoComErro] = useState(null);
  const [sucesso, setSucesso] = useState(null);
  const [confirmandoExclusao, setConfirmandoExclusao] = useState(false);
  const [excluindo, setExcluindo] = useState(false);

  useEffect(() => {
    if (!usuario) navigate("/login", { replace: true });
  }, [usuario, navigate]);

  // Só os campos que realmente mudaram vão no PATCH. Mandar o formulário
  // inteiro faria a API checar unicidade de e-mail contra o próprio registro
  // a cada gravação, sem necessidade.
  const alteracoes = useMemo(() => {
    if (!usuario || !form) return {};
    const mudou = {};

    if (form.nomeCompleto.trim() !== (usuario.nome_completo || "")) {
      mudou.nome_completo = form.nomeCompleto.trim();
    }
    const emailNovo = form.email.trim().toLowerCase();
    if (emailNovo !== (usuario.email || "")) mudou.email = emailNovo;

    const celularNovo = somenteDigitos(form.celular);
    if (celularNovo !== (usuario.celular || "")) mudou.celular = celularNovo;

    if (form.rg.trim() !== (usuario.rg || "")) mudou.rg = form.rg.trim();

    if (form.dataNascimento !== (usuario.data_nascimento || "")) {
      mudou.data_nascimento = form.dataNascimento;
    }
    if (form.senha) mudou.senha = form.senha;

    return mudou;
  }, [form, usuario]);

  const temAlteracao = Object.keys(alteracoes).length > 0;

  if (!usuario || !form) return null;

  function alterar(campo, valor) {
    setForm((atual) => ({ ...atual, [campo]: valor }));
    setSucesso(null);
    setErroApi(null);
    setCampoComErro(null);
  }

  function validarLocalmente() {
    if (!nomeCompletoValido(form.nomeCompleto)) {
      return ["nomeCompleto", "Informe o nome completo, apenas letras."];
    }
    // A conta não pode ficar sem e-mail e sem celular: é por eles que o
    // código de verificação chega.
    if (!form.email.trim() && !somenteDigitos(form.celular)) {
      return ["email", "Mantenha ao menos um e-mail ou um celular."];
    }
    if (form.email.trim() && !emailValido(form.email)) {
      return ["email", "E-mail inválido."];
    }
    if (form.celular && !celularValido(form.celular)) {
      return ["celular", "Celular inválido. Use DDD + 9 dígitos."];
    }
    if (form.dataNascimento && !idadeMinimaOk(form.dataNascimento)) {
      return ["dataNascimento", "É preciso ter ao menos 18 anos."];
    }
    if (form.senha && !senhaValida(form.senha)) {
      return ["senha", "A senha precisa de 8+ caracteres, com letras e números."];
    }
    return null;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setErroApi(null);
    setSucesso(null);
    setCampoComErro(null);

    if (!temAlteracao) {
      setErroApi("Nenhuma alteração para salvar.");
      return;
    }

    const problema = validarLocalmente();
    if (problema) {
      setCampoComErro(problema[0]);
      setErroApi(problema[1]);
      return;
    }

    setEnviando(true);
    try {
      const atualizado = await atualizarUsuario(usuario.id_usuario, alteracoes);
      setUsuario(atualizado);
      salvarSessao(atualizado);
      setForm(formularioInicial(atualizado));
      setSucesso("Dados atualizados com sucesso.");
    } catch (err) {
      const { campo, mensagem } = extrairErroApi(err);
      setErroApi(mensagem);
      if (campo && CAMPO_PARA_ERRO[campo]) setCampoComErro(CAMPO_PARA_ERRO[campo]);
    } finally {
      setEnviando(false);
    }
  }

  async function handleExcluir() {
    setErroApi(null);
    setExcluindo(true);
    try {
      await excluirUsuario(usuario.id_usuario);
      limparSessao();
      navigate("/login", { replace: true, state: { contaExcluida: true } });
    } catch (err) {
      setErroApi(extrairErroApi(err).mensagem);
      setConfirmandoExclusao(false);
    } finally {
      setExcluindo(false);
    }
  }

  function sair() {
    limparSessao();
    navigate("/login", { replace: true });
  }

  return (
    <AuthLayout title="Meus dados" subtitle="Altere suas informações de cadastro">
      <AlertBanner>{erroApi}</AlertBanner>
      {sucesso ? <AlertBanner tone="success">{sucesso}</AlertBanner> : null}

      <form onSubmit={handleSubmit} noValidate>
        <FormField
          label="Nome completo"
          value={form.nomeCompleto}
          onChange={(e) => alterar("nomeCompleto", e.target.value)}
          error={campoComErro === "nomeCompleto" ? erroApi : null}
          autoComplete="name"
        />

        <FormField
          label="E-mail"
          placeholder="voce@exemplo.com"
          value={form.email}
          onChange={(e) => alterar("email", e.target.value)}
          error={campoComErro === "email" ? erroApi : null}
          autoComplete="email"
        />

        <FormField
          label="Telefone"
          placeholder="(11) 99999-9999"
          value={form.celular}
          onChange={(e) => alterar("celular", aplicarMascaraCelular(e.target.value))}
          error={campoComErro === "celular" ? erroApi : null}
          autoComplete="tel"
        />

        <FormField
          label="RG"
          placeholder="Opcional"
          value={form.rg}
          onChange={(e) => alterar("rg", e.target.value)}
        />

        <FormField
          label="CPF"
          value={aplicarMascaraCpf(usuario.cpf || "")}
          disabled
          hint="O CPF não pode ser alterado: é o identificador da sua conta."
        />

        <FormField
          label="Data de nascimento"
          type="date"
          value={form.dataNascimento}
          onChange={(e) => alterar("dataNascimento", e.target.value)}
          error={campoComErro === "dataNascimento" ? erroApi : null}
        />

        <PasswordField
          label="Nova senha"
          placeholder="Deixe em branco para manter a atual"
          value={form.senha}
          onChange={(e) => alterar("senha", e.target.value)}
          error={campoComErro === "senha" ? erroApi : null}
          autoComplete="new-password"
        />

        <PrimaryButton type="submit" loading={enviando} disabled={!temAlteracao}>
          Salvar alterações
        </PrimaryButton>
      </form>

      <div className="perfil-perigo">
        <h2 className="perfil-perigo__titulo">Excluir conta</h2>

        {confirmandoExclusao ? (
          <>
            <p className="perfil-perigo__texto">
              Tem certeza? Sua conta deixa de aparecer e você não consegue mais entrar.
            </p>
            <div className="perfil-perigo__acoes">
              <button
                type="button"
                className="perfil-perigo__botao"
                onClick={handleExcluir}
                disabled={excluindo}
              >
                {excluindo ? "Excluindo..." : "Sim, excluir minha conta"}
              </button>
              <button
                type="button"
                className="perfil-perigo__cancelar"
                onClick={() => setConfirmandoExclusao(false)}
                disabled={excluindo}
              >
                Cancelar
              </button>
            </div>
          </>
        ) : (
          <button
            type="button"
            className="perfil-perigo__botao"
            onClick={() => setConfirmandoExclusao(true)}
          >
            Excluir minha conta
          </button>
        )}
      </div>

      <p className="auth-footer">
        <button type="button" className="auth-footer__link" onClick={sair}>
          Sair da conta
        </button>
      </p>
    </AuthLayout>
  );
}
