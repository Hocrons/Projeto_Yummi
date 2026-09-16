/**
 * Busca CEP na API do ViaCEP e preenche os campos de endereço.
 * Usado no formulário de cadastro de restaurante.
 *
 * API: https://viacep.com.br/ws/{cep}/json/
 * Sem chave, sem autenticação, gratuita.
 */
(function () {
    "use strict";

    const campoCep = document.getElementById("cep");
    const campoRua = document.getElementById("rua");
    const campoBairro = document.getElementById("bairro");
    const campoCidade = document.getElementById("cidade");
    const campoEstado = document.getElementById("estado");
    const statusEl = document.getElementById("cep-status");

    if (!campoCep) return; // página não tem o form de restaurante

    function mostrarStatus(msg, tipo) {
        if (!statusEl) return;
        statusEl.textContent = msg;
        statusEl.className = "cep-status cep-status--" + (tipo || "info");
    }

    function limparStatus() {
        if (!statusEl) return;
        statusEl.textContent = "";
        statusEl.className = "cep-status";
    }

    function soDigitos(txt) {
        return (txt || "").replace(/\D/g, "");
    }

    async function buscarCep() {
        const cep = soDigitos(campoCep.value);
        if (cep.length !== 8) {
            limparStatus();
            return;
        }

        mostrarStatus("Buscando CEP...", "info");

        try {
            const resp = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
            if (!resp.ok) throw new Error("Falha na consulta");
            const dados = await resp.json();

            if (dados.erro) {
                mostrarStatus("CEP não encontrado. Confira e tente novamente.", "erro");
                return;
            }

            if (campoRua) campoRua.value = dados.logradouro || "";
            if (campoBairro) campoBairro.value = dados.bairro || "";
            if (campoCidade) campoCidade.value = dados.localidade || "";
            if (campoEstado) campoEstado.value = dados.uf || "";

            // Foca no número, próximo passo natural
            const campoNumero = document.getElementById("numero");
            if (campoNumero) campoNumero.focus();

            mostrarStatus("Endereço encontrado! Complete o número.", "sucesso");
        } catch (e) {
            mostrarStatus("Erro ao buscar CEP. Tente novamente.", "erro");
        }
    }

    // Busca quando o CEP tiver 8 dígitos (ao sair do campo ou digitar)
    campoCep.addEventListener("blur", buscarCep);

    // Aplica máscara simples: 00000-000
    campoCep.addEventListener("input", function () {
        let v = soDigitos(campoCep.value).slice(0, 8);
        if (v.length > 5) {
            v = v.slice(0, 5) + "-" + v.slice(5);
        }
        campoCep.value = v;
    });
})();