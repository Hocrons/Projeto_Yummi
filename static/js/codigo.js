// Gerencia as 6 caixinhas de dígito das telas de verificação de código
// (usado em templates/cliente/codigo.html)

document.addEventListener("DOMContentLoaded", () => {
    const caixas = document.querySelectorAll(".digito");
    const campoOculto = document.getElementById("codigo-completo");
    const form = document.getElementById("form-codigo");

    if (!caixas.length) return;

    function atualizarCodigoCompleto() {
        campoOculto.value = Array.from(caixas).map((c) => c.value).join("");
    }

    caixas.forEach((caixa, indice) => {
        caixa.addEventListener("input", () => {
            caixa.value = caixa.value.replace(/[^0-9]/g, "");
            if (caixa.value && indice < caixas.length - 1) {
                caixas[indice + 1].focus();
            }
            atualizarCodigoCompleto();
        });

        caixa.addEventListener("keydown", (evento) => {
            if (evento.key === "Backspace" && !caixa.value && indice > 0) {
                caixas[indice - 1].focus();
            }
        });

        // Permite colar o código de 6 dígitos de uma vez em qualquer caixinha
        caixa.addEventListener("paste", (evento) => {
            evento.preventDefault();
            const colado = (evento.clipboardData || window.clipboardData).getData("text").replace(/\D/g, "");
            if (!colado) return;
            colado.split("").slice(0, caixas.length).forEach((digito, i) => {
                if (caixas[i]) caixas[i].value = digito;
            });
            atualizarCodigoCompleto();
            const proximaVazia = Array.from(caixas).find((c) => !c.value);
            (proximaVazia || caixas[caixas.length - 1]).focus();
        });
    });

    form.addEventListener("submit", atualizarCodigoCompleto);
});