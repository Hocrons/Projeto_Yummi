/**
 * Alternância entre tema claro (fofo rosa) e tema escuro (Hello Kitty Dark).
 * - O tema é aplicado no <html data-theme="light|dark">
 * - Salvo em localStorage
 * - Se não tiver salvo, usa o sistema operacional
 */
(function () {
    "use strict";

    const root = document.documentElement;
    const btn = document.getElementById("theme-toggle");

    function getTemaAtual() {
        return root.getAttribute("data-theme") || "light";
    }

    function aplicarTema(tema) {
        root.setAttribute("data-theme", tema);
        localStorage.setItem("tema", tema);
    }

    // Se o JS rodar antes do inline do <head> (não deve, mas por garantia)
    if (!root.getAttribute("data-theme")) {
        const salvo = localStorage.getItem("tema");
        const sistema = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
        aplicarTema(salvo || sistema);
    }

    // Botão de toggle
    if (btn) {
        btn.addEventListener("click", function () {
            const atual = getTemaAtual();
            aplicarTema(atual === "dark" ? "light" : "dark");
        });
    }

    // Se o usuário mudar o tema do SO e não tiver preferência salva, acompanha
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function (e) {
        if (!localStorage.getItem("tema")) {
            aplicarTema(e.matches ? "dark" : "light");
        }
    });
})();