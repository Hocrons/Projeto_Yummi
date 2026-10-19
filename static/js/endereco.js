document.addEventListener("DOMContentLoaded", () => {
    console.log("Script endereco.js executado com sucesso.");

    const inputCep = document.getElementById("cep");
    const inputRua = document.getElementById("rua");
    const inputNumero = document.getElementById("numero");
    const inputBairro = document.getElementById("bairro");
    const inputCidade = document.getElementById("cidade");
    const inputSearch = document.getElementById("google-autocomplete");
    const inputLat = document.getElementById("lat");
    const inputLon = document.getElementById("lon");

    // ---------------------------------------------------------------
    // Helper: guarda as coordenadas nos campos hidden (se existirem)
    // ---------------------------------------------------------------
    function preencherCoordenadas(lat, lon) {
        if (!inputLat || !inputLon) return;
        if (lat === null || lat === undefined || lon === null || lon === undefined) return;
        inputLat.value = lat;
        inputLon.value = lon;
    }

    // ---------------------------------------------------------------
    // 1. ViaCEP (Gratuito - Busca ao desfocar o campo CEP)
    // ---------------------------------------------------------------
    if (inputCep) {
        inputCep.addEventListener("blur", () => {
            const cep = inputCep.value.replace(/\D/g, "");

            if (cep.length === 8) {
                if (inputRua) inputRua.value = "Carregando...";
                if (inputBairro) inputBairro.value = "Carregando...";
                if (inputCidade) inputCidade.value = "Carregando...";

                fetch(`https://viacep.com.br/ws/${cep}/json/`)
                    .then((res) => res.json())
                    .then((data) => {
                        if (!data.erro) {
                            if (inputRua) inputRua.value = data.logradouro || "";
                            if (inputBairro) inputBairro.value = data.bairro || "";
                            if (inputCidade) inputCidade.value = data.localidade || "";
                            if (inputCep) inputCep.value = data.cep || cep;
                            if (inputNumero) inputNumero.focus();

                        } else {
                            if (typeof mostrarToast === "function") {
                                mostrarToast("CEP não encontrado.");
                            } else {
                                alert("CEP não encontrado.");
                            }
                            limparCampos();
                        }
                    })
                    .catch(() => {
                        if (typeof mostrarToast === "function") {
                            mostrarToast("Erro ao buscar CEP.");
                        } else {
                            alert("Erro ao buscar CEP.");
                        }
                        limparCampos();
                    });
            }
        });
    }

    function limparCampos() {
        if (inputRua) inputRua.value = "";
        if (inputBairro) inputBairro.value = "";
        if (inputCidade) inputCidade.value = "";
        preencherCoordenadas("", "");
    }

    // ---------------------------------------------------------------
    // 2. Busca explícita de endereço via API do servidor
    // ---------------------------------------------------------------
    if (inputSearch) {
        const botaoBusca = document.getElementById("buscar-endereco");
        const listaSugestoes = document.createElement("ul");
        listaSugestoes.style.cssText = "position:absolute; z-index:1000; background:#fff; border:1px solid #ccc; width:100%; list-style:none; padding:0; margin:0; max-height:200px; overflow-y:auto; border-radius:0 0 8px 8px; box-shadow:0 4px 6px rgba(0,0,0,0.1);";

        inputSearch.parentNode.style.position = "relative";
        inputSearch.parentNode.appendChild(listaSugestoes);

        botaoBusca.addEventListener("click", async () => {
            const query = inputSearch.value.trim();
            if (query.length < 3) {
                if (typeof mostrarToast === "function") mostrarToast("Informe pelo menos 3 caracteres.");
                return;
            }

            botaoBusca.disabled = true;
            listaSugestoes.innerHTML = "";
            try {
                const response = await fetch(`/api/geocoding/search?q=${encodeURIComponent(query)}`, {
                    headers: { "Accept": "application/json" },
                });
                const data = await response.json();
                if (!response.ok || !data.ok) {
                    throw new Error(data.erro || "Não foi possível buscar esse endereço.");
                }

                data.resultados.forEach((item) => {
                    const li = document.createElement("li");
                    li.style.cssText = "padding:10px; cursor:pointer; border-bottom:1px solid #eee; font-size:0.9em; text-align:left; color:#333;";
                    li.textContent = item.display_name;

                    li.addEventListener("click", () => {
                        const addr = item.address || {};
                        if (inputRua) inputRua.value = addr.road || addr.pedestrian || addr.suburb || "";
                        if (inputNumero) inputNumero.value = addr.house_number || "";
                        if (inputBairro) inputBairro.value = addr.suburb || addr.neighbourhood || addr.district || "";
                        if (inputCidade) inputCidade.value = addr.city || addr.town || addr.municipality || "";
                        if (inputCep && addr.postcode) inputCep.value = addr.postcode.replace(/\D/g, "");

                        preencherCoordenadas(item.lat, item.lon);
                        inputSearch.value = item.display_name;
                        listaSugestoes.innerHTML = "";

                        if (inputNumero && !addr.house_number) inputNumero.focus();
                    });
                    listaSugestoes.appendChild(li);
                });

                if (!data.resultados.length && typeof mostrarToast === "function") {
                    mostrarToast("Nenhum endereço encontrado.");
                }
            } catch (error) {
                console.error("Erro na busca de endereço:", error);
                if (typeof mostrarToast === "function") mostrarToast(error.message);
            } finally {
                botaoBusca.disabled = false;
            }
        });

        document.addEventListener("click", (e) => {
            if (e.target !== inputSearch && e.target !== botaoBusca) listaSugestoes.innerHTML = "";
        });
    }
});