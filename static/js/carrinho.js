// Usado em: templates/cliente/ver_cardapio.html e templates/cliente/carrinho.html

const BASE_CLIENTE = "/cliente";

document.addEventListener("DOMContentLoaded", () => {

    // ---------- Botões "Adicionar" no cardápio ----------
    document.querySelectorAll(".btn-adicionar").forEach((botao) => {
        botao.addEventListener("click", async () => {
            const idProduto = botao.dataset.id;
            const nomeProduto = botao.dataset.nome;

            botao.disabled = true;
            try {
                const resposta = await fetch(`${BASE_CLIENTE}/carrinho/adicionar`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ id_produto: idProduto }),
                });
                const dados = await resposta.json();

                if (!resposta.ok) {
                    if (dados.conflito_restaurante) {
                        if (confirm(dados.erro + " Deseja esvaziar o carrinho e adicionar este item?")) {
                            await fetch(`${BASE_CLIENTE}/carrinho/limpar`, { method: "POST" });
                            botao.click();
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
            const linha = botao.closest(".carrinho-item");
            const idProduto = botao.dataset.id;
            const delta = parseInt(botao.dataset.delta, 10);
            const spanQtd = linha.querySelector(".qtd-valor");
            const novaQuantidade = parseInt(spanQtd.textContent, 10) + delta;

            // Feedback visual imediato (desabilita por um instante)
            botao.disabled = true;

            try {
                const resposta = await fetch(`${BASE_CLIENTE}/carrinho/atualizar`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ id_produto: idProduto, quantidade: novaQuantidade }),
                });
                const dados = await resposta.json();
                if (!resposta.ok) return;

                atualizarBadgeCarrinho(dados.totais.qtd_total);

                // Se o item foi removido ou o carrinho esvaziou, recarrega
                if (novaQuantidade <= 0 || dados.totais.qtd_total === 0) {
                    location.reload();
                    return;
                }

                // Atualiza quantidade no card
                spanQtd.textContent = novaQuantidade;

                // Atualiza subtotal do card
                const precoUnit = parseFloat(
                    linha.querySelector(".carrinho-item__preco-unit").textContent
                        .replace("R$", "").replace("cada", "").trim()
                );
                const sub = linha.querySelector(".carrinho-item__subtotal");
                if (sub) {
                    sub.textContent = `R$ ${(precoUnit * novaQuantidade).toFixed(2)}`;
                }

                // Atualiza resumo lateral
                const resumoLinha = document.querySelector(
                    `.carrinho-resumo__linha .carrinho-resumo__linha-qtd`
                );
                atualizarResumo(dados.carrinho, dados.totais);
            } catch (erro) {
                console.error(erro);
                mostrarToast("Erro de conexão. Tente novamente.");
            } finally {
                botao.disabled = false;
            }
        });
    });

    // ---------- Botão "Limpar carrinho" ----------
    const btnLimpar = document.getElementById("btn-limpar-carrinho");
    if (btnLimpar) {
        btnLimpar.addEventListener("click", async () => {
            if (!confirm("Tem certeza que deseja limpar todo o carrinho?")) return;
            await fetch(`${BASE_CLIENTE}/carrinho/limpar`, { method: "POST" });
            location.reload();
        });
    }
});

function atualizarResumo(carrinho, totais) {
    // Atualiza lista de linhas do resumo (re-renderização simples)
    const container = document.querySelector(".carrinho-resumo__linhas");
    if (container) {
        container.innerHTML = "";
        for (const [pid, item] of Object.entries(carrinho.itens)) {
            const div = document.createElement("div");
            div.className = "carrinho-resumo__linha";
            div.innerHTML = `
                <span class="carrinho-resumo__linha-qtd">${item.quantidade}×</span>
                <span class="carrinho-resumo__linha-nome">${item.nome}</span>
                <span class="carrinho-resumo__linha-preco">R$ ${(item.preco * item.quantidade).toFixed(2)}</span>
            `;
            container.appendChild(div);
        }
    }

    // Atualiza subtotal
    const totalEl = document.getElementById("total-carrinho");
    if (totalEl) {
        totalEl.textContent = `R$ ${totais.total.toFixed(2)}`;
    }
}

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