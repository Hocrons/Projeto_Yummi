import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000/api";

export const api = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
});

export function extrairErroApi(error) {
  const resposta = error?.response?.data?.erro;
  if (resposta?.mensagem) {
    return { campo: resposta.campo || null, mensagem: resposta.mensagem };
  }
  if (error?.request) {
    return {
      campo: null,
      mensagem: "Não foi possível falar com o servidor. Verifique se a API está rodando.",
    };
  }
  return { campo: null, mensagem: "Algo deu errado. Tente novamente." };
}
