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

export async function buscarUsuario(idUsuario) {
  const { data } = await api.get(`/usuarios/${idUsuario}`);
  return data.dados;
}

/**
 * Atualização parcial: manda só os campos que mudaram.
 *
 * A API recusa campo fora da lista de atualizáveis (o `cpf`, por exemplo),
 * então `campos` precisa conter apenas nome_completo, email, celular, rg,
 * data_nascimento ou senha.
 */
export async function atualizarUsuario(idUsuario, campos) {
  const { data } = await api.patch(`/usuarios/${idUsuario}`, campos);
  return data.dados;
}

/**
 * Exclusão lógica: a API marca `status_conta = 'excluido'` e mantém a linha,
 * para não quebrar o histórico de pedidos que a referencia.
 */
export async function excluirUsuario(idUsuario) {
  const { data } = await api.delete(`/usuarios/${idUsuario}`);
  return data;
}
