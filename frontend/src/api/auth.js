import { api } from "./client";

export async function entrar({ identificador, senha }) {
  const payload = { senha };
  if (identificador.includes("@")) {
    payload.email = identificador.trim().toLowerCase();
  } else {
    payload.celular = identificador.replace(/\D/g, "");
  }

  const { data } = await api.post("/auth/login", payload);
  return data.dados;
}
