// Usado em: templates/cliente/ver_cardapio.html e templates/cliente/carrinho.html

document.addEventListener("DOMContentLoaded", () => {
    // ---------- Botões "Adicionar" no cardápio ----------
    document.querySelectorAll(".btn-adicionar").forEach((botao) => {
        botao.addEventListener("click", async () => {
            const idProduto = botao.dataset.id;
            const nomeProduto = botao.dataset.nome;

            botao.disabled = true;
            try {
                const resposta = await fetch("/cliente/carrinho/adicionar", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ id_produto: idProduto }),
                });
                const dados = await resposta.json();

                if (!resposta.ok) {
                    if (dados.conflito_restaurante) {
                        if (confirm(dados.erro + " Deseja esvaziar o carrinho e adicionar este item?")) {
                            await fetch("/cliente/carrinho/limpar", { method: "POST" });
                            botao.click(); // tenta adicionar de novo
                        }
                    } else {
                        mostrarToast(dados.erro || "Não foi possível adicionar o produto.");
                    }
                    return;
                }

                atualizarBadgeCarrinho(dados.totais.qtd_total);
                mostrarToast(`"${nomeProduto}" adicionado ao carrinho!`);
            } catch (erro) {
                console.error(erro);
                mostrarToast("Erro de conexão. Tente novamente.");
            } finally {
                botao.disabled = false;
            }
        });
    });

    // ---------- Botões +/- na página do carrinho ----------
    document.querySelectorAll(".btn-qtd").forEach((botao) => {
        botao.addEventListener("click", async () => {
            const linha = botao.closest(".linha-carrinho");
            const idProduto = botao.dataset.id;
            const delta = parseInt(botao.dataset.delta, 10);
            const spanQtd = linha.querySelector(".qtd-valor");
            const novaQuantidade = parseInt(spanQtd.textContent, 10) + delta;

            const resposta = await fetch("/cliente/carrinho/atualizar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id_produto: idProduto, quantidade: novaQuantidade }),
            });
            const dados = await resposta.json();
            if (!resposta.ok) return;

            atualizarBadgeCarrinho(dados.totais.qtd_total);
            const totalCarrinhoEl = document.getElementById("total-carrinho");
            if (totalCarrinhoEl) {
                totalCarrinhoEl.textContent = `R$ ${dados.totais.total.toFixed(2)}`;
            }

            // Se o item foi removido (quantidade <= 0) ou o carrinho esvaziou, recarrega a página
            if (novaQuantidade <= 0 || dados.totais.qtd_total === 0) {
                location.reload();
            } else {
                spanQtd.textContent = novaQuantidade;
            }
        });
    });
});

function atualizarBadgeCarrinho(qtdTotal) {
    const link = document.querySelector(".navbar__cart");
    if (!link) return;
    let badge = link.querySelector(".badge");
    if (qtdTotal > 0) {
        if (!badge) {
            badge = document.createElement("span");
            badge.className = "badge";
            link.appendChild(badge);
        }
        badge.textContent = qtdTotal;
    } else if (badge) {
        badge.remove();
    }
}
