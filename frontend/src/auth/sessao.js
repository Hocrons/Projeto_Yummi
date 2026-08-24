/**
 * Guarda quem está logado entre uma página e outra.
 *
 * ATENÇÃO — isto NÃO é autenticação. É um remendo temporário até o JWT
 * (RNF05) existir. O dado fica no sessionStorage, que o usuário pode editar
 * pelo DevTools, e a API ainda não exige credencial nenhuma para atualizar ou
 * excluir um usuário. Ou seja: hoje qualquer um que alcance a API consegue
 * alterar qualquer cadastro.
 *
 * Quando o JWT entrar, o token substitui isto e o back-end passa a conferir,
 * a cada requisição, se quem pede é mesmo o dono do cadastro.
 */
const CHAVE = "yummi.usuario";

export function salvarSessao(usuario) {
  sessionStorage.setItem(CHAVE, JSON.stringify(usuario));
}

export function lerSessao() {
  const bruto = sessionStorage.getItem(CHAVE);
  if (!bruto) return null;
  try {
    return JSON.parse(bruto);
  } catch {
    // Conteúdo corrompido: descarta em vez de derrubar a aplicação.
    sessionStorage.removeItem(CHAVE);
    return null;
  }
}

export function limparSessao() {
  sessionStorage.removeItem(CHAVE);
}
