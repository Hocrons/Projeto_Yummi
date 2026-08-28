// Comportamento global do site (carregado em toda página via base.html)

document.addEventListener("DOMContentLoaded", () => {
    // Dropdown "Entrar" no header
    const toggle = document.querySelector(".dropdown__toggle");
    if (toggle) {
        const dropdown = toggle.closest(".dropdown");
        toggle.addEventListener("click", (e) => {
            e.stopPropagation();
            dropdown.classList.toggle("aberto");
        });
        document.addEventListener("click", () => dropdown.classList.remove("aberto"));
    }

    // Some sozinho com as mensagens flash depois de alguns segundos
    document.querySelectorAll(".flash").forEach((el) => {
        setTimeout(() => {
            el.style.transition = "opacity .4s ease";
            el.style.opacity = "0";
            setTimeout(() => el.remove(), 400);
        }, 4000);
    });
});

// Pequeno helper de toast reutilizado por outras páginas (ex: carrinho.js)
function mostrarToast(mensagem) {
    const toast = document.getElementById("toast");
    if (!toast) {
        alert(mensagem);
        return;
    }
    toast.textContent = mensagem;
    toast.hidden = false;
    clearTimeout(window.__toastTimeout);
    window.__toastTimeout = setTimeout(() => (toast.hidden = true), 2500);
}
