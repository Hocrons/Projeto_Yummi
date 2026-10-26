/**
 * Notificações globais de status de pedido para o cliente.
 */
(function () {
    "use strict";

    const INTERVALO_MS = 10000;
    const STORAGE_KEY = "yummy_status_pedidos";

    const INFO_STATUS = {
        "pendente": { icone: "⏳", titulo: "Pedido aguardando aceite", descricao: "O restaurante ainda não confirmou." },
        "preparando": { icone: "🍳", titulo: "Pedido em preparo", descricao: "O restaurante está preparando seu pedido." },
        "localizando_entregador": { icone: "📡", titulo: "Procurando entregador", descricao: "Estamos buscando alguém para levar seu pedido." },
        "indo_ao_restaurante": { icone: "🛵", titulo: "Entregador a caminho", descricao: "O entregador está indo retirar o pedido." },
        "saiu_para_entrega": { icone: "🚀", titulo: "Pedido saiu para entrega", descricao: "Logo chega aí!" },
        "entregue": { icone: "✅", titulo: "Pedido entregue", descricao: "Bom apetite!" },
        "cancelado": { icone: "❌", titulo: "Pedido cancelado", descricao: "O pedido foi cancelado." },
    };

    function carregarUltimoEstado() {
        try {
            const raw = sessionStorage.getItem(STORAGE_KEY);
            return raw ? JSON.parse(raw) : {};
        } catch (e) { return {}; }
    }

    function salvarUltimoEstado(estado) {
        try {
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify(estado));
        } catch (e) {}
    }

    let container = null;
    function obterContainer() {
        if (container) return container;
        container = document.createElement("div");
        container.id = "notif-container";
        container.className = "notif-container";
        document.body.appendChild(container);
        return container;
    }

    function dispararPushNotification(info, pedido) {
        if (!("Notification" in window) || Notification.permission !== "granted") return;

        const titulo = `${info.icone} ${info.titulo}`;
        const opcoes = {
            body: `Pedido #${pedido.id} · ${pedido.nome_fantasia}\n${info.descricao}`,
            icon: "/static/img/logo.png",
            badge: "/static/img/logo.png",
            tag: `pedido-${pedido.id}`,
            renotify: true,
            requireInteraction: true,
        };

        try {
            const notificacao = new Notification(titulo, opcoes);
            notificacao.onclick = function () {
                window.focus();
                window.location.href = "/cliente/pedidos";
                notificacao.close();
            };
        } catch (e) { console.warn("Push falhou:", e); }
    }

    function mostrarBanner(pedido, statusNovo) {
        const info = INFO_STATUS[statusNovo] || { icone: "🔔", titulo: "Status atualizado", descricao: `Pedido #${pedido.id}` };

        dispararPushNotification(info, pedido);

        const el = document.createElement("div");
        el.className = "notif-banner";
        el.dataset.pedido = pedido.id;

        // Adicionado a div da barra de progresso no final
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
            <div class="notif-banner__progress"></div>
        `;

        el.querySelector(".notif-banner__fechar").addEventListener("click", (e) => {
            e.stopPropagation();
            removerBanner(el);
        });

        el.addEventListener("click", (evento) => {
            if (evento.target.closest(".notif-banner__fechar")) return;
            window.location.href = "/cliente/pedidos";
        });

        obterContainer().appendChild(el);
        setTimeout(() => removerBanner(el), 7000);
    }

    function removerBanner(el) {
        if (!el || !el.parentNode) return;
        el.classList.add("notif-banner--saindo");
        setTimeout(() => {
            if (el.parentNode) el.parentNode.removeChild(el);
        }, 300);
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

                if (estadoAnterior[id] && estadoAnterior[id] !== p.status) {
                    mostrarBanner(p, p.status);
                }
            });

            salvarUltimoEstado(novoEstado);
        } catch (erro) {
            console.debug("Notificações: falha ao consultar pedidos", erro);
        }
    }

    setTimeout(verificarPedidos, 3000);
    setInterval(verificarPedidos, INTERVALO_MS);
})();