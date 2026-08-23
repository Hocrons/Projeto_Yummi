import { api } from "./client";

export async function cadastrarUsuario({
  nomeCompleto,
  email,
  celular,
  cpf,
  dataNascimento,
  senha,
}) {
  const payload = {
    nome_completo: nomeCompleto,
    cpf: cpf.replace(/\D/g, ""),
    data_nascimento: dataNascimento,
    senha,
  };

  if (email) payload.email = email.trim().toLowerCase();
  if (celular) payload.celular = celular.replace(/\D/g, "");

  const { data } = await api.post("/usuarios", payload);
  return data.dados;
}
