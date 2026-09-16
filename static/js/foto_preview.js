/**
 * Preview em tempo real da foto do restaurante.
 * Usado em templates/restaurante/editar_perfil.html
 */
(function () {
    "use strict";

    const input = document.getElementById("foto-url-input");
    const preview = document.getElementById("foto-preview");
    const fallback = document.getElementById("foto-fallback");
    const status = document.getElementById("foto-status");
    const box = document.getElementById("foto-preview-box");
    if (!input || !box) return;

    function mostrarStatus(msg, tipo) {
        if (!status) return;
        status.textContent = msg || "";
        status.className = "cep-status" + (tipo ? " cep-status--" + tipo : "");
    }

    function atualizarPreview() {
        const url = (input.value || "").trim();

        if (!url) {
            // Vazio: só fallback
            if (preview) preview.style.display = "none";
            if (fallback) fallback.style.display = "flex";
            mostrarStatus("");
            return;
        }

        if (!/^https?:\/\//i.test(url)) {
            mostrarStatus("A URL precisa começar com http:// ou https://", "erro");
            if (preview) preview.style.display = "none";
            if (fallback) fallback.style.display = "flex";
            return;
        }

        // Cria uma imagem temporária pra validar
        const img = new Image();
        mostrarStatus("Carregando imagem...", "info");

        img.onload = function () {
            if (preview) {
                preview.src = url;
                preview.style.display = "block";
            }
            if (fallback) fallback.style.display = "none";
            mostrarStatus("Imagem carregada!", "sucesso");
        };

        img.onerror = function () {
            if (preview) preview.style.display = "none";
            if (fallback) fallback.style.display = "flex";
            mostrarStatus("Não foi possível carregar essa imagem. Confira o link.", "erro");
        };

        img.src = url;
    }

    // Dispara ao sair do campo e também no "paste"
    input.addEventListener("blur", atualizarPreview);
    input.addEventListener("paste", () => setTimeout(atualizarPreview, 50));
})();