(function () {
    const relatorio = document.querySelector("[data-report-type]");
    if (!relatorio) return;

    const status = relatorio.querySelector("[data-report-refresh-status]");
    const url = relatorio.dataset.refreshUrl;
    const moeda = new Intl.NumberFormat("pt-BR", {
        style: "currency",
        currency: "BRL",
    });

    function atualizarItens(itens) {
        const corpo = relatorio.querySelector("#relatorio-itens");
        if (!corpo) return;
        corpo.replaceChildren();

        if (itens.length === 0) {
            const linha = document.createElement("tr");
            linha.className = "relatorio__vazio";
            const celula = document.createElement("td");
            celula.colSpan = 4;
            celula.textContent = "Nenhum item vendido neste período.";
            linha.append(celula);
            corpo.append(linha);
            return;
        }

        itens.forEach((item) => {
            const linha = document.createElement("tr");
            const nome = document.createElement("td");
            const nomeDestaque = document.createElement("strong");
            nomeDestaque.textContent = item.nome;
            nome.append(nomeDestaque);
            linha.append(nome);

            [item.quantidade, moeda.format(item.preco_unitario), moeda.format(item.faturamento)]
                .forEach((valor) => {
                    const celula = document.createElement("td");
                    celula.textContent = valor;
                    linha.append(celula);
                });
            corpo.append(linha);
        });
    }

    async function atualizarRelatorio() {
        try {
            const resposta = await fetch(url, {
                headers: { Accept: "application/json" },
                credentials: "same-origin",
            });
            if (!resposta.ok) {
                throw new Error(`Falha ao atualizar relatório (HTTP ${resposta.status}).`);
            }

            const dados = await resposta.json();
            if (relatorio.dataset.reportType === "restaurante") {
                relatorio.querySelector("#relatorio-vendas").textContent = dados.numero_vendas;
                relatorio.querySelector("#relatorio-faturamento").textContent =
                    moeda.format(dados.faturamento);
                atualizarItens(dados.itens);
            } else {
                Object.entries(dados).forEach(([periodo, valor]) => {
                    const elemento = relatorio.querySelector(`[data-ganho="${periodo}"]`);
                    if (elemento) elemento.textContent = moeda.format(valor);
                });
            }
            status.textContent = `Atualizado às ${new Date().toLocaleTimeString("pt-BR", {
                hour: "2-digit",
                minute: "2-digit",
            })}`;
        } catch (erro) {
            console.error(erro);
            status.textContent = "Não foi possível atualizar os dados.";
        }
    }

    window.setInterval(atualizarRelatorio, 30000);
})();
