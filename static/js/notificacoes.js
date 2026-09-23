/**
 * Notificações globais de status de pedido para o cliente.
 *
 * Roda em TODAS as páginas do cliente logado.
 * A cada 10 segundos consulta /cliente/api/pedidos-ativos e compara com
 * o último status conhecido (guardado em sessionStorage). Se algum status
 * mudou, mostra um banner no topo centralizado.
 *
 * Sem som. Sem spam: só notifica quando o status MUDA de verdade.
 */
(function () {
    "use strict";

    const INTERVALO_MS = 10000;
    const STORAGE_KEY = "yummy_status_pedidos";

    // Mapa de status → { icone, titulo, cor }
    const INFO_STATUS = {
        "pendente": {
            icone: "⏳",
            titulo: "Pedido aguardando aceite",
            descricao: "O restaurante ainda não confirmou.",
        },
        "preparando": {
            icone: "🍳",
            titulo: "Pedido em preparo",
            descricao: "O restaurante está preparando seu pedido.",
        },
        "localizando_entregador": {
            icone: "📡",
            titulo: "Procurando entregador",
            descricao: "Estamos buscando alguém para levar seu pedido.",
        },
        "indo_ao_restaurante": {
            icone: "🛵",
            titulo: "Entregador a caminho",
            descricao: "O entregador está indo retirar o pedido.",
        },
        "saiu_para_entrega": {
            icone: "🚀",
            titulo: "Pedido saiu para entrega",
            descricao: "Logo chega aí!",
        },
        "entregue": {
            icone: "✅",
            titulo: "Pedido entregue",
            descricao: "Bom apetite!",
        },
        "cancelado": {
            icone: "❌",
            titulo: "Pedido cancelado",
            descricao: "O pedido foi cancelado.",
        },
    };

    function carregarUltimoEstado() {
        try {
            const raw = sessionStorage.getItem(STORAGE_KEY);
            return raw ? JSON.parse(raw) : {};
        } catch (e) {
            return {};
        }
    }

    function salvarUltimoEstado(estado) {
        try {
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify(estado));
        } catch (e) {
            /* ignora */
        }
    }

    // Cria o container dos banners (uma vez)
    let container = null;
    function obterContainer() {
        if (container) return container;
        container = document.createElement("div");
        container.id = "notif-container";
        container.className = "notif-container";
        document.body.appendChild(container);
        return container;
    }

    function mostrarBanner(pedido, statusNovo) {
        const info = INFO_STATUS[statusNovo] || {
            icone: "🔔",
            titulo: "Status atualizado",
            descricao: `Pedido #${pedido.id}`,
        };

        const el = document.createElement("div");
        el.className = "notif-banner";
        el.dataset.pedido = pedido.id;

        el.innerHTML = `
            <div class="notif-banner__icone">${info.icone}</div>
            <div class="notif-banner__texto">
                <div class="notif-banner__titulo">${info.titulo}</div>
                <div class="notif-banner__desc">
                    <strong>#${pedido.id}</strong> · ${pedido.nome_fantasia}
                    <span class="notif-banner__status">${info.descricao}</span>
                </div>
            </div>
            <button type="button" class="notif-banner__fechar" aria-label="Fechar">×</button>
        `;

        // Fechar no X
        el.querySelector(".notif-banner__fechar").addEventListener("click", () => {
            removerBanner(el);
        });

        // Fechar ao clicar no corpo (vai pra "Meus pedidos")
        el.addEventListener("click", (evento) => {
            if (evento.target.closest(".notif-banner__fechar")) return;
            window.location.href = "/cliente/pedidos";
        });

        obterContainer().appendChild(el);

        // Auto-fecha em 7 segundos
        setTimeout(() => removerBanner(el), 7000);
    }

    function removerBanner(el) {
        if (!el || !el.parentNode) return;
        el.classList.add("notif-banner--saindo");
        setTimeout(() => {
            if (el.parentNode) el.parentNode.removeChild(el);
        }, 260);
    }

    async function verificarPedidos() {
        try {
            const resposta = await fetch("/cliente/api/pedidos-ativos", {
                headers: { "Accept": "application/json" },
                cache: "no-store",
            });
            if (!resposta.ok) return;

            const dados = await resposta.json();
            const pedidos = dados.pedidos || [];
            const estadoAnterior = carregarUltimoEstado();
            const novoEstado = {};

            pedidos.forEach((p) => {
                const id = String(p.id);
                novoEstado[id] = p.status;

                // Se já conhecíamos esse pedido e o status mudou → notifica
                if (estadoAnterior[id] && estadoAnterior[id] !== p.status) {
                    mostrarBanner(p, p.status);
                }
            });

            salvarUltimoEstado(novoEstado);
        } catch (erro) {
            // silencioso — não incomoda o usuário
            console.debug("Notificações: falha ao consultar pedidos", erro);
        }
    }

    // Primeira checagem depois de 3s (pra não competir com o load da página)
    setTimeout(verificarPedidos, 3000);

    // Depois a cada 10s
    setInterval(verificarPedidos, INTERVALO_MS);
})();