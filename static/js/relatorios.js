(function () {
    const relatorio = document.querySelector("[data-report-type]");
    if (!relatorio) return;

    const tipo = relatorio.dataset.reportType;
    const status = relatorio.querySelector("[data-report-refresh-status]");
    const url = relatorio.dataset.refreshUrl;
    const moeda = new Intl.NumberFormat("pt-BR", {
        style: "currency",
        currency: "BRL",
    });
    let limiteAtual = 5;
    let dadosAtuais = null;

    function atualizarStatus(texto) {
        if (status) status.textContent = texto;
    }

    function atualizarLimite(limite) {
        limiteAtual = limite;
        relatorio.querySelectorAll("[data-report-limit]").forEach((botao) => {
            const ativo = Number(botao.dataset.reportLimit) === limiteAtual;
            botao.classList.toggle("ativo", ativo);
            botao.setAttribute("aria-pressed", String(ativo));
        });
        if (dadosAtuais) renderizar(dadosAtuais);
        else {
            relatorio.querySelectorAll("[data-item-row], [data-entrega-row]")
                .forEach((linha, indice) => {
                    linha.hidden = indice >= limiteAtual;
                });
        }
    }

    function criarCelula(texto) {
        const celula = document.createElement("td");
        celula.textContent = texto;
        return celula;
    }

    function renderizarItens(itens) {
        const corpo = relatorio.querySelector("#relatorio-itens");
        if (!corpo) return;
        corpo.replaceChildren();

        if (itens.length === 0) {
            const linha = document.createElement("tr");
            linha.className = "relatorio__vazio";
            const celula = criarCelula("Nenhum item vendido neste período.");
            celula.colSpan = 4;
            linha.append(celula);
            corpo.append(linha);
            return;
        }

        itens.slice(0, limiteAtual).forEach((item) => {
            const linha = document.createElement("tr");
            const nome = criarCelula("");
            const destaque = document.createElement("strong");
            destaque.textContent = item.nome;
            nome.append(destaque);
            linha.append(
                nome,
                criarCelula(String(item.quantidade)),
                criarCelula(moeda.format(item.preco_unitario)),
                criarCelula(moeda.format(item.faturamento)),
            );
            corpo.append(linha);
        });
    }

    function renderizarEntregas(dados) {
        const lista = relatorio.querySelector("#relatorio-entregas");
        if (!lista) return;
        lista.replaceChildren();

        if (dados.historico.length === 0) {
            const vazio = document.createElement("p");
            vazio.className = "relatorio__vazio";
            vazio.textContent = "Nenhuma entrega concluída neste período.";
            lista.append(vazio);
            return;
        }

        dados.historico.slice(0, limiteAtual).forEach((entrega) => {
            const linha = document.createElement("article");
            linha.className = "relatorio__entrega";

            const numero = document.createElement("strong");
            numero.textContent = `#${String(entrega.id).padStart(4, "0")}`;

            const detalhe = document.createElement("div");
            const restaurante = document.createElement("strong");
            restaurante.textContent = entrega.restaurante;
            const data = document.createElement("span");
            data.textContent = entrega.entregue_em;
            detalhe.append(restaurante, data);

            const valor = document.createElement("div");
            valor.className = "relatorio__valor-entrega";
            const taxa = document.createElement("strong");
            taxa.textContent = moeda.format(entrega.taxa_entrega);
            const legenda = document.createElement("span");
            legenda.textContent = "taxa de entrega";
            valor.append(taxa, legenda);

            const concluida = document.createElement("span");
            concluida.className = "relatorio__status-entrega";
            concluida.textContent = "Concluída";
            linha.append(numero, detalhe, valor, concluida);
            lista.append(linha);
        });
    }

    function renderizarAdmin(dados) {
        const metricas = dados.metricas;
        relatorio.querySelector('[data-admin-metrica="faturamento"]').textContent =
            moeda.format(metricas.faturamento);
        ["pedidos_realizados", "pedidos_concluidos", "pedidos_cancelados"]
            .forEach((chave) => {
                relatorio.querySelector(`[data-admin-metrica="${chave}"]`).textContent =
                    String(metricas[chave]);
            });

        const corpo = relatorio.querySelector("#admin-relatorio-restaurantes");
        corpo.replaceChildren();
        dados.restaurantes.forEach((restaurante, indice) => {
            const linha = document.createElement("tr");
            const nome = criarCelula("");
            const posicao = document.createElement("span");
            posicao.className = "admin-relatorio__rank";
            posicao.textContent = String(indice + 1);
            const nomeTexto = document.createElement("strong");
            nomeTexto.textContent = restaurante.nome;
            nome.append(posicao, nomeTexto);

            const taxa = criarCelula("");
            const taxaWrap = document.createElement("div");
            taxaWrap.className = "admin-relatorio__taxa";
            const barra = document.createElement("span");
            const preenchimento = document.createElement("i");
            preenchimento.style.width = `${restaurante.taxa_conclusao}%`;
            barra.append(preenchimento);
            const porcentagem = document.createElement("strong");
            porcentagem.textContent = `${restaurante.taxa_conclusao}%`;
            taxaWrap.append(barra, porcentagem);
            taxa.append(taxaWrap);

            linha.append(
                nome,
                criarCelula(String(restaurante.pedidos_realizados)),
                criarCelula(String(restaurante.pedidos_concluidos)),
                criarCelula(String(restaurante.pedidos_cancelados)),
                taxa,
                criarCelula(moeda.format(restaurante.faturamento)),
            );
            corpo.append(linha);
        });

        if (dados.restaurantes.length === 0) {
            const linha = document.createElement("tr");
            linha.className = "relatorio__vazio";
            const celula = criarCelula("Nenhum restaurante cadastrado.");
            celula.colSpan = 6;
            linha.append(celula);
            corpo.append(linha);
        }

        const total = document.createElement("tr");
        total.className = "admin-relatorio__total";
        const totalLabel = document.createElement("td");
        const totalLabelText = document.createElement("strong");
        totalLabelText.className = "admin-relatorio__total-label";
        totalLabelText.textContent = "Total geral";
        totalLabel.append(totalLabelText);
        total.append(
            totalLabel,
            criarCelula(String(metricas.pedidos_realizados)),
            criarCelula(String(metricas.pedidos_concluidos)),
            criarCelula(String(metricas.pedidos_cancelados)),
            criarCelula(`${metricas.taxa_conclusao}%`),
            criarCelula(moeda.format(metricas.faturamento)),
        );
        corpo.append(total);
    }

    function renderizar(dados) {
        if (tipo === "restaurante") {
            relatorio.querySelector("#relatorio-vendas").textContent =
                String(dados.numero_vendas);
            relatorio.querySelector("#relatorio-faturamento").textContent =
                moeda.format(dados.faturamento);
            renderizarItens(dados.itens);
        } else if (tipo === "entregador") {
            relatorio.querySelector("[data-ganho]").textContent =
                moeda.format(dados.ganho);
            relatorio.querySelector("[data-entregas]").textContent =
                String(dados.entregas);
            renderizarEntregas(dados);
        } else if (tipo === "admin") {
            renderizarAdmin(dados);
        }
    }

    async function atualizarRelatorio() {
        try {
            const resposta = await fetch(url, {
                headers: { Accept: "application/json" },
                credentials: "same-origin",
                cache: "no-store",
            });
            const dados = await resposta.json();
            if (!resposta.ok) {
                throw new Error(dados.erro || `Falha ao atualizar relatório (HTTP ${resposta.status}).`);
            }

            dadosAtuais = dados;
            renderizar(dados);
            const horario = new Date().toLocaleTimeString("pt-BR", {
                hour: "2-digit",
                minute: "2-digit",
            });
            atualizarStatus(`Atualizado às ${horario}`);
        } catch (erro) {
            console.error(erro);
            atualizarStatus("Não foi possível atualizar os dados.");
        }
    }

    const seletorPeriodo = relatorio.querySelector("[data-period-select]");
    const datasPeriodo = relatorio.querySelector("[data-period-dates]");
    if (seletorPeriodo && datasPeriodo) {
        const campos = datasPeriodo.querySelectorAll("input");
        const atualizarCamposData = () => {
            const personalizado = seletorPeriodo.value === "periodo";
            datasPeriodo.hidden = !personalizado;
            campos.forEach((campo) => {
                campo.disabled = !personalizado;
                campo.required = personalizado;
            });
        };
        seletorPeriodo.addEventListener("change", atualizarCamposData);
        atualizarCamposData();
    }

    relatorio.querySelectorAll("[data-report-limit]").forEach((botao) => {
        botao.addEventListener("click", () => {
            atualizarLimite(Number(botao.dataset.reportLimit));
        });
    });
    atualizarLimite(limiteAtual);
    window.setInterval(atualizarRelatorio, 30000);
})();
