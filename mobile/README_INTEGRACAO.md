# Yummi App Android — Guia de Integração

## 1. Configurar o Backend Flask

### 1.1 Instalar dependência JWT
```bash
pip install PyJWT
```

### 1.2 Adicionar os endpoints REST
Copie o arquivo `FLASK_API_ENDPOINTS.py` para `controllers/mobile_api.py` no projeto Flask.

### 1.3 Registrar o blueprint no app.py
```python
from controllers.mobile_api import mobile_api_bp
app.register_blueprint(mobile_api_bp)
```

### 1.4 Adicionar funções ao models/models.py
Copie as funções de `MODELS_ADDITIONS.py` para o final de `models/models.py`.

---

## 2. Configurar o App Android

### 2.1 URL do servidor
Edite `RetrofitClient.kt` e altere `BASE_URL`:

| Situação | URL |
|----------|-----|
| Emulador Android (localhost) | `http://10.0.2.2:5000/` |
| Dispositivo físico (rede local) | `http://192.168.X.X:5000/` |
| Produção | `https://seu-dominio.com/` |

### 2.2 Importar no Android Studio
1. Abra o Android Studio
2. **File → Open** → selecione a pasta `YummiApp/`
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

