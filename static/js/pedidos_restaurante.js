document.addEventListener("DOMContentLoaded", () => {
    const painel = document.getElementById("painel-pedidos");
    const lista = document.getElementById("lista-pedidos-restaurante");
    if (!painel || !lista) return;

    const intervaloMs = 5000;
    let consultando = false;

    async function atualizarPedidos() {
        if (consultando || document.hidden) return;
        consultando = true;

        try {
            const resposta = await fetch(painel.dataset.url, {
                headers: { "Accept": "text/html" },
                cache: "no-store",
            });
            if (resposta.redirected) return;
            if (!resposta.ok) {
                throw new Error(`Consulta de pedidos falhou (${resposta.status}).`);
            }

            const html = await resposta.text();
            const conteudoAtualizado = document.createElement("template");
            conteudoAtualizado.innerHTML = html;
            if (lista.innerHTML !== conteudoAtualizado.innerHTML) {
                lista.replaceChildren(conteudoAtualizado.content.cloneNode(true));
            }
        } catch (erro) {
            console.error("Erro ao atualizar pedidos do restaurante:", erro);
        } finally {
            consultando = false;
        }
    }

    setInterval(atualizarPedidos, intervaloMs);
    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) atualizarPedidos();
    });
});
