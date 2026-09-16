/**
 * Comportamento genérico dos dropdowns da navbar.
 * Abre/fecha ao clicar no botão .dropdown__toggle, fecha ao clicar fora.
 */
document.addEventListener("click", function (event) {
    const toggles = document.querySelectorAll(".dropdown__toggle");

    toggles.forEach(function (toggle) {
        const dropdown = toggle.closest(".dropdown");
        if (dropdown.contains(event.target)) {
            // clicou dentro do dropdown -> alterna
            event.preventDefault();
            // fecha outros dropdowns
            document.querySelectorAll(".dropdown.aberto").forEach(function (d) {
                if (d !== dropdown) d.classList.remove("aberto");
            });
            dropdown.classList.toggle("aberto");
        } else {
            // clicou fora -> fecha
            dropdown.classList.remove("aberto");
        }
    });
});