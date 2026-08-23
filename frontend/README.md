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
                   AlertBanner, TermsCheckbox, Logo
  pages/          Login.jsx, Cadastro.jsx
  utils/          validators.js — CPF (módulo 11), e-mail, máscara de
                   celular, idade mínima, senha
```

## Onde estamos

Tela de **Entrar** com validação de e-mail em tempo real e senha com
mostrar/ocultar.

Tela de **Criar conta** com o formulário completo (nome, e-mail, telefone,
CPF, data de nascimento, senha) e todas as validações client-side: CPF por
módulo 11, máscara de celular, idade mínima de 18 anos, senha com letra e
número, aceite obrigatório dos Termos de Uso. Por enquanto o envio só
valida os dados localmente — a chamada pra API de cadastro ainda não foi
conectada.

## Próximo passo

Ligar o formulário de cadastro em `POST /api/usuarios` e tratar os erros
que a API devolve (campo inválido, e-mail/CPF já cadastrado).
