import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import AuthLayout from "../components/AuthLayout";
import FormField from "../components/FormField";
import PasswordField from "../components/PasswordField";
import PrimaryButton from "../components/PrimaryButton";
import TermsCheckbox from "../components/TermsCheckbox";
import AlertBanner from "../components/AlertBanner";
import {
  aplicarMascaraCelular,
  aplicarMascaraCpf,
  celularValido,
  cpfValido,
  emailValido,
  idadeMinimaOk,
  nomeCompletoValido,
  senhaValida,
} from "../utils/validators";

export default function Cadastro() {
  const [form, setForm] = useState({
    nomeCompleto: "",
    email: "",
    celular: "",
    cpf: "",
    dataNascimento: "",
    senha: "",
  });
  const [aceitaTermos, setAceitaTermos] = useState(false);
  const [tocado, setTocado] = useState({});
  const [sucesso, setSucesso] = useState(false);

  function atualizar(campo, valor) {
    setForm((atual) => ({ ...atual, [campo]: valor }));
  }

  function marcarTocado(campo) {
    setTocado((atual) => ({ ...atual, [campo]: true }));
  }

  const erros = useMemo(() => {
    const lista = {};
    if (tocado.nomeCompleto && !nomeCompletoValido(form.nomeCompleto)) {
      lista.nomeCompleto = "Informe nome e sobrenome (só letras, mín. 3 caracteres).";
    }
    if (tocado.email && !emailValido(form.email)) {
      lista.email = "E-mail inválido";
    }
    if (tocado.celular && !celularValido(form.celular)) {
      lista.celular = "Celular inválido. Use (DD) 9NNNN-NNNN.";
    }
    if (tocado.cpf && !cpfValido(form.cpf)) {
      lista.cpf = "CPF inválido.";
    }
    if (tocado.dataNascimento && !idadeMinimaOk(form.dataNascimento)) {
      lista.dataNascimento = "É preciso ter 18 anos ou mais para se cadastrar.";
    }
    if (tocado.senha && !senhaValida(form.senha)) {
      lista.senha = "Mínimo 8 caracteres, com 1 letra e 1 número.";
    }
    if (tocado.termos && !aceitaTermos) {
      lista.termos = "É preciso aceitar os termos para continuar.";
    }
    return lista;
  }, [form, tocado, aceitaTermos]);

  const formularioValido =
    nomeCompletoValido(form.nomeCompleto) &&
    emailValido(form.email) &&
    celularValido(form.celular) &&
    cpfValido(form.cpf) &&
    idadeMinimaOk(form.dataNascimento) &&
    senhaValida(form.senha) &&
    aceitaTermos;

  function handleSubmit(e) {
    e.preventDefault();
    setTocado({
      nomeCompleto: true,
      email: true,
      celular: true,
      cpf: true,
      dataNascimento: true,
      senha: true,
      termos: true,
    });

    if (!formularioValido) return;
    setSucesso(true);
  }

  return (
    <AuthLayout title="Criar conta">
      {sucesso ? (
        <AlertBanner tone="success">
          Formulário validado. A integração com a API de cadastro ainda vai ser conectada aqui.
        </AlertBanner>
      ) : null}

      <form onSubmit={handleSubmit} noValidate>
        <FormField
          label="Nome completo"
          placeholder="Ana Souza"
          value={form.nomeCompleto}
          onChange={(e) => atualizar("nomeCompleto", e.target.value)}
          onBlur={() => marcarTocado("nomeCompleto")}
          error={erros.nomeCompleto}
          autoComplete="name"
        />

        <FormField
          label="E-mail"
          placeholder="voce@exemplo.com"
          value={form.email}
          onChange={(e) => atualizar("email", e.target.value)}
          onBlur={() => marcarTocado("email")}
          error={erros.email}
          autoComplete="email"
        />

        <FormField
          label="Telefone"
          placeholder="(11) 99999-9999"
          value={form.celular}
          onChange={(e) => atualizar("celular", aplicarMascaraCelular(e.target.value))}
          onBlur={() => marcarTocado("celular")}
          error={erros.celular}
          inputMode="numeric"
          autoComplete="tel"
        />

        <FormField
          label="CPF"
          placeholder="000.000.000-00"
          value={form.cpf}
          onChange={(e) => atualizar("cpf", aplicarMascaraCpf(e.target.value))}
          onBlur={() => marcarTocado("cpf")}
          error={erros.cpf}
          inputMode="numeric"
        />

        <FormField
          label="Data de nascimento"
          type="date"
          value={form.dataNascimento}
          onChange={(e) => atualizar("dataNascimento", e.target.value)}
          onBlur={() => marcarTocado("dataNascimento")}
          error={erros.dataNascimento}
        />

        <PasswordField
          label="Senha"
          placeholder="Mín. 8 caracteres"
          value={form.senha}
          onChange={(e) => atualizar("senha", e.target.value)}
          onBlur={() => marcarTocado("senha")}
          error={erros.senha}
          autoComplete="new-password"
        />

        <TermsCheckbox
          checked={aceitaTermos}
          onChange={(valor) => {
            setAceitaTermos(valor);
            marcarTocado("termos");
          }}
          error={erros.termos}
        />

        <PrimaryButton type="submit">Criar minha conta</PrimaryButton>
      </form>

      <p className="auth-footer">
        Já tem uma conta?{" "}
        <Link to="/login" className="auth-footer__link">
          Entrar
        </Link>
      </p>
    </AuthLayout>
  );
}
