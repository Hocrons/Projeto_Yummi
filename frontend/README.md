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

Sobe em `http://localhost:5173`. Precisa do backend rodando junto para o
cadastro funcionar de verdade — sem ele, o formulário mostra a mensagem de
erro de conexão em vez de travar.

```bash
npm run build     # gera dist/, pronto pra Vercel/Netlify/Render
npm run preview   # serve o build de produção localmente
```

## Estrutura

```
src/
  api/            client axios + chamadas (client.js, auth.js, usuarios.js)
  components/     AuthLayout, FormField, PasswordField, PrimaryButton,
                   AlertBanner, TermsCheckbox, Logo
  pages/          Login.jsx, Cadastro.jsx
  utils/          validators.js — CPF (módulo 11), e-mail, máscara de
                   celular, idade mínima, senha
```

## Onde estamos

Tela de **Entrar** com validação de e-mail em tempo real e senha com
mostrar/ocultar. Tela de **Criar conta** integrada com `POST
/api/usuarios` — nome completo, e-mail, telefone, CPF, data de nascimento
e senha, com aceite obrigatório dos Termos de Uso.

O cadastro considera sucesso assim que a API responde 201, mas a conta
nasce como `pendente` até a validação por código — a tela de sucesso já
deixa isso registrado.

O login ainda não fala com nada de verdade: a chamada a `POST
/api/auth/login` já está escrita, mas essa rota ainda não existe no
backend (sem OTP, sem OAuth, sem JWT por enquanto). Até lá, tentar entrar
mostra um aviso em vez de travar.

## Validações no front

`src/utils/validators.js` cobre CPF por módulo 11 (rejeitando sequências
tipo 111.111.111-11), e-mail, celular travado em 11 dígitos com DDD, senha
com mínimo de 8 caracteres com letra e número, e idade mínima de 18 anos.
O backend valida tudo de novo do lado dele — isso aqui é só pra dar
feedback na hora.

## Próximo passo

Login de verdade assim que a rota de autenticação existir no backend, e
login social (Google/Facebook) depois disso.
