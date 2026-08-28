// Usado em templates/cliente/pedido_sucesso.html
// Consulta /pedido/<id>/status a cada 5s para simular acompanhamento em tempo real.

document.addEventListener("DOMContentLoaded", () => {
    const elStatus = document.getElementById("status-pedido");
    if (!elStatus) return;

    const idPedido = elStatus.dataset.id;

    async function atualizarStatus() {
        try {
            const resposta = await fetch(`/pedido/${idPedido}/status`);
            if (!resposta.ok) return;
            const dados = await resposta.json();
            elStatus.textContent = dados.status;

            if (dados.status === "entregue" || dados.status === "cancelado") {
                clearInterval(intervalo);
            }
        } catch (erro) {
            console.error("Erro ao consultar status do pedido:", erro);
        }
    }

    const intervalo = setInterval(atualizarStatus, 5000);
});
