# Yummi — Frontend

Front-end do Yummi, feito em React + Vite. Sem framework de UI pesado nem
biblioteca de estilo — só `react-router-dom` para as rotas e `axios` para
as chamadas HTTP.

## Rodando

```bash
npm install
cp .env.example .env   # ajuste VITE_API_URL se a API não estiver em 127.0.0.1:5000
npm run dev
```

Sobe em `http://localhost:5173`.

```bash
npm run build     # gera dist/, pronto pra Vercel/Netlify/Render
npm run preview   # serve o build de produção localmente
```

## Estrutura

```
src/
  api/            client axios + chamadas (client.js, auth.js)
  components/     AuthLayout, FormField, PasswordField, PrimaryButton,
                   AlertBanner, Logo
  pages/          Login.jsx
  utils/          validators.js — validação de e-mail
```

## Onde estamos

Primeira entrega: tela de **Entrar**, com validação de e-mail em tempo real
e campo de senha com opção de mostrar/ocultar. A chamada de login já está
escrita (`POST /api/auth/login`), mas essa rota ainda não existe no
backend — por enquanto a tela trata o erro e avisa quem estiver testando,
em vez de travar.

Próximo passo: tela de cadastro, integrada com o CRUD de usuário que já
está pronto no backend.
