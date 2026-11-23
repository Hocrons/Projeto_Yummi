# Yummi App Android — Guia de Integração

## 1. Configurar o Backend Flask

### 1.1 Instalar dependências do backend
```bash
pip install -r requirements.txt
```

`PyJWT` já está declarado em `requirements.txt`. O blueprint mobile já está
implementado em `controllers/mobile_api.py` e registrado em `app.py`; não copie
os arquivos de integração por cima desses arquivos.

Configure uma `SECRET_KEY` fixa no `.env` da VPS e mantenha o mesmo valor entre
reinicializações. Os tokens de login do app dependem dessa chave.

---

## 2. Configurar o App Android

### 2.1 URL do servidor
O app aponta para a VPS em `https://yummy-demo.duckdns.org/`, com certificado TLS
válido. Não use o IP diretamente: a VPS redireciona HTTP para HTTPS, e o TLS deve
ser acessado pelo domínio coberto pelo certificado. Não desative a validação de
certificado no app.

| Situação | URL |
|----------|-----|
| Emulador Android (localhost) | `http://10.0.2.2:5000/` |
| Dispositivo físico (rede local) | `http://192.168.X.X:5000/` |
| Produção (VPS) | `https://yummy-demo.duckdns.org/` |

### 2.2 Importar no Android Studio
1. Abra o Android Studio
2. **File → Open** → selecione a pasta `mobile/`
3. Aguarde o Gradle sync
4. Execute no emulador ou dispositivo

---

## 3. Estrutura do Projeto Android

```
app/
└── src/main/
    ├── java/com/yummi/restaurante/
    │   ├── data/
    │   │   ├── api/
    │   │   │   ├── ApiService.kt         # Endpoints Retrofit
    │   │   │   └── RetrofitClient.kt     # ⚠️ Configure BASE_URL aqui
    │   │   └── model/
    │   │       ├── Auth.kt               # Login request/response
    │   │       └── Product.kt            # Modelo de produto
    │   ├── ui/
    │   │   ├── login/
    │   │   │   ├── LoginActivity.kt
    │   │   │   └── LoginViewModel.kt
    │   │   └── products/
    │   │       ├── ProductListActivity.kt
    │   │       ├── ProductFormActivity.kt
    │   │       ├── ProductsViewModel.kt
    │   │       └── ProductAdapter.kt
    │   └── util/
    │       ├── SessionManager.kt         # Token JWT persistido
    │       └── Extensions.kt
    └── res/
        ├── layout/                       # XML das telas
        ├── values/                       # Cores, strings, temas
        └── drawable/                     # Ícones e backgrounds
```

---

## 4. Fluxo do App

```
LoginActivity
  ↓ POST /api/restaurante/login
  ↓ Salva token JWT no SharedPreferences
ProductListActivity
  ↓ GET /api/restaurante/produtos
  ↓ [FAB +] → ProductFormActivity (novo)
  ↓ [✏️ edit] → ProductFormActivity (editar)
  ↓ [🗑️ delete] → DELETE /api/restaurante/produtos/:id
  ↓ [Sair] → limpa a sessão e retorna ao login
ProductFormActivity
  ↓ POST ou PUT /api/restaurante/produtos
  ↓ RESULT_OK → volta e recarrega lista
```

---

## 5. Paleta de Cores (mesma do site)

| Token | Hex |
|-------|-----|
| Primary | `#FF5C9D` |
| Primary Dark | `#E63980` |
| Primary Soft | `#FFE4EF` |
| Background | `#FFF5F8` |
| Text | `#4A2C40` |
| Muted | `#9A7A8E` |

