/**
 * Modal de confirmação de entrega com código (4 dígitos).
 * Usado em templates/entregador/painel.html
 */
(function () {
    "use strict";

    const modal = document.getElementById("modal-codigo");
    if (!modal) return;

    const form = document.getElementById("form-codigo-entrega");
    const campoOculto = document.getElementById("codigo-modal-completo");
    const caixas = modal.querySelectorAll(".digito-modal");
    const btnFechar = document.getElementById("btn-fechar-modal");

    function limparCaixas() {
        caixas.forEach((c) => (c.value = ""));
        campoOculto.value = "";
    }

    function abrir(idPedido) {
        // action do form: /entregador/pedido/<id>/entregue
        form.action = "/entregador/pedido/" + idPedido + "/entregue";
        limparCaixas();
        modal.hidden = false;
        caixas[0].focus();
    }

    function fechar() {
        modal.hidden = true;
        limparCaixas();
    }

    // Botões "Cheguei no local"
    document.querySelectorAll(".btn-abrir-modal-codigo").forEach((btn) => {
        btn.addEventListener("click", () => abrir(btn.dataset.id));
    });

    // Fechar
    btnFechar.addEventListener("click", fechar);
    modal.addEventListener("click", (e) => {
        if (e.target === modal) fechar();
    });

    // Navegação entre as caixinhas
    caixas.forEach((caixa, i) => {
        caixa.addEventListener("input", () => {
            caixa.value = caixa.value.replace(/\D/g, "").slice(0, 1);
            if (caixa.value && i < caixas.length - 1) caixas[i + 1].focus();
            campoOculto.value = Array.from(caixas).map((c) => c.value).join("");
        });

        caixa.addEventListener("keydown", (e) => {
            if (e.key === "Backspace" && !caixa.value && i > 0) {
                caixas[i - 1].focus();
            }
        });

        // Colar 4 dígitos de uma vez
        caixa.addEventListener("paste", (e) => {
            e.preventDefault();
            const colado = (e.clipboardData || window.clipboardData).getData("text").replace(/\D/g, "");
            if (!colado) return;
            colado.split("").slice(0, caixas.length).forEach((d, idx) => {
                if (caixas[idx]) caixas[idx].value = d;
            });
            campoOculto.value = Array.from(caixas).map((c) => c.value).join("");
            const proxima = Array.from(caixas).find((c) => !c.value);
            (proxima || caixas[caixas.length - 1]).focus();
        });
    });

    // Garante que o campo oculto é preenchido no submit
    form.addEventListener("submit", () => {
        campoOculto.value = Array.from(caixas).map((c) => c.value).join("");
    });
})();