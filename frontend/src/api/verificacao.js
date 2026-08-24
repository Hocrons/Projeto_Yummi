import { api } from "./client";

/** Pede (ou reenvia) o código de verificação. A API recusa antes de 60s. */
export async function enviarCodigo(idUsuario) {
  const { data } = await api.post("/verificacao/enviar", { id_usuario: idUsuario });
  return data.dados;
}

/** Valida o código. Dando certo, a conta sai de "pendente" e o login libera. */
export async function validarCodigo(idUsuario, codigo) {
  const { data } = await api.post("/verificacao/validar", {
    id_usuario: idUsuario,
    codigo: codigo.trim(),
  });
  return data.dados;
}
