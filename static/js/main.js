/**
 * Comportamento dos dropdowns da navbar (Entrar / Criar conta).
 * - Abre ao clicar no botão .dropdown__toggle
 * - Fecha ao clicar fora, ou em outro dropdown
 * - Permite que os <a> dentro do menu naveguem normalmente
 * - Fecha o dropdown após clicar em um link (sem bloquear a navegação)
 */
document.addEventListener("click", function (event) {
    const toggles = document.querySelectorAll(".dropdown__toggle");

    // Se o clique foi dentro de algum dropdown aberto
    let clicouDentroDeAlgum = false;

    toggles.forEach(function (toggle) {
        const dropdown = toggle.closest(".dropdown");
        if (dropdown.contains(event.target)) {
            clicouDentroDeAlgum = true;

            // Se o alvo foi o próprio botão de toggle, alterna
            if (event.target === toggle || toggle.contains(event.target)) {
                event.preventDefault();
                // Fecha outros
                document.querySelectorAll(".dropdown.aberto").forEach(function (d) {
                    if (d !== dropdown) d.classList.remove("aberto");
                });
                dropdown.classList.toggle("aberto");
            }
            // Se o alvo foi um link do menu, deixa navegar normalmente.
            // O dropdown será fechado depois pelo próprio reload da página.
        } else {
            dropdown.classList.remove("aberto");
        }
    });

    // Se clicou fora de qualquer dropdown, garante que nenhum fique aberto
    if (!clicouDentroDeAlgum) {
        document.querySelectorAll(".dropdown.aberto").forEach(function (d) {
            d.classList.remove("aberto");
        });
    }
});