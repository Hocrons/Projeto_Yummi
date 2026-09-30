/**
 * Aplicação / remoção de cupom de desconto no carrinho.
 * Trabalha junto com static/js/carrinho.js.
 */
(function () {
    "use strict";

    const BASE_CLIENTE = "/cliente";

    document.addEventListener("DOMContentLoaded", () => {
        const btnAplicar = document.getElementById("btn-aplicar-cupom");
        const btnRemover = document.getElementById("btn-remover-cupom");
        const input = document.getElementById("cupom-input");
        const msg = document.getElementById("cupom-msg");

        if (btnAplicar) {
            btnAplicar.addEventListener("click", aplicarCupom);
        }
        if (input) {
            input.addEventListener("keydown", (e) => {
                if (e.key === "Enter") {
                    e.preventDefault();
                    aplicarCupom();
                }
            });
        }
        if (btnRemover) {
            btnRemover.addEventListener("click", removerCupom);
        }

        async function aplicarCupom() {
            const codigo = (input.value || "").trim();
            if (!codigo) {
                mostrarMsg("Digite um código.", "erro");
                return;
            }

            btnAplicar.disabled = true;
            btnAplicar.textContent = "...";

            try {
                const resp = await fetch(`${BASE_CLIENTE}/carrinho/cupom`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ codigo }),
                });
                const dados = await resp.json();

                if (!resp.ok || !dados.ok) {
                    mostrarMsg(dados.erro || "Não foi possível aplicar o cupom.", "erro");
                    return;
                }

                mostrarCupomAplicado(dados.cupom);
                atualizarTotais(dados.totais);
                mostrarMsg("Cupom aplicado!", "sucesso");

                if (typeof mostrarToast === "function") {
                    mostrarToast(`Cupom ${dados.cupom} aplicado!`);
                }
            } catch (e) {
                console.error(e);
                mostrarMsg("Erro de conexão. Tente novamente.", "erro");
            } finally {
                btnAplicar.disabled = false;
                btnAplicar.textContent = "Aplicar";
            }
        }

        async function removerCupom() {
            try {
                const resp = await fetch(`${BASE_CLIENTE}/carrinho/cupom/remover`, {
                    method: "POST",
                });
                const dados = await resp.json();
                if (!resp.ok || !dados.ok) return;

                mostrarFormularioCupom();
                atualizarTotais(dados.totais);
                mostrarMsg("Cupom removido.", "info");

                if (typeof mostrarToast === "function") {
                    mostrarToast("Cupom removido.");
                }
            } catch (e) {
                console.error(e);
            }
        }

        function mostrarCupomAplicado(codigo) {
            const tag = document.getElementById("cupom-tag");
            const divAplicado = document.getElementById("cupom-aplicado");
            const form = document.getElementById("cupom-form");
            if (tag) tag.textContent = codigo;
            if (divAplicado) divAplicado.hidden = false;
            if (form) form.hidden = true;
        }

        function mostrarFormularioCupom() {
            const divAplicado = document.getElementById("cupom-aplicado");
            const form = document.getElementById("cupom-form");
            const input = document.getElementById("cupom-input");
            if (divAplicado) divAplicado.hidden = true;
            if (form) form.hidden = false;
            if (input) input.value = "";
        }

        function atualizarTotais(totais) {
            const sub = document.getElementById("subtotal-carrinho");
            const desc = document.getElementById("desconto-carrinho");
            const linhaDesc = document.getElementById("linha-desconto");
            const tot = document.getElementById("total-carrinho");

            if (sub) sub.textContent = `R$ ${Number(totais.subtotal).toFixed(2)}`;
            if (desc) desc.textContent = `− R$ ${Number(totais.desconto).toFixed(2)}`;
            if (linhaDesc) linhaDesc.hidden = !totais.desconto;
            if (tot) tot.textContent = `R$ ${Number(totais.total).toFixed(2)}`;
        }

        function mostrarMsg(texto, tipo) {
            if (!msg) return;
            msg.textContent = texto || "";
            msg.className = "cupom-box__msg";
            if (tipo) msg.classList.add(`cupom-box__msg--${tipo}`);
        }
    });
})();