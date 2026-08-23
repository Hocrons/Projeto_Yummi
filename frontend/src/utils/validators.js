export function somenteDigitos(valor) {
  return (valor || "").replace(/\D/g, "");
}

const REGEX_EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function emailValido(email) {
  if (!email) return false;
  return REGEX_EMAIL.test(email.trim()) && email.trim().length <= 254;
}

export function aplicarMascaraCelular(valor) {
  const digitos = somenteDigitos(valor).slice(0, 11);
  const ddd = digitos.slice(0, 2);
  const primeira = digitos.slice(2, 7);
  const segunda = digitos.slice(7, 11);

  if (digitos.length === 0) return "";
  if (digitos.length <= 2) return `(${ddd}`;
  if (digitos.length <= 7) return `(${ddd}) ${primeira}`;
  return `(${ddd}) ${primeira}-${segunda}`;
}

export function celularValido(valor) {
  const digitos = somenteDigitos(valor);
  return digitos.length === 11 && digitos[2] === "9";
}

export function cpfValido(valor) {
  const cpf = somenteDigitos(valor);
  if (cpf.length !== 11) return false;
  if (/^(\d)\1{10}$/.test(cpf)) return false;

  const calcularDigito = (base) => {
    let soma = 0;
    let peso = base.length + 1;
    for (const char of base) {
      soma += Number(char) * peso;
      peso -= 1;
    }
    const resto = (soma * 10) % 11;
    return resto === 10 ? 0 : resto;
  };

  const digito1 = calcularDigito(cpf.slice(0, 9));
  const digito2 = calcularDigito(cpf.slice(0, 9) + digito1);

  return cpf.endsWith(`${digito1}${digito2}`);
}

export function aplicarMascaraCpf(valor) {
  const digitos = somenteDigitos(valor).slice(0, 11);
  const partes = [
    digitos.slice(0, 3),
    digitos.slice(3, 6),
    digitos.slice(6, 9),
    digitos.slice(9, 11),
  ].filter(Boolean);

  if (partes.length <= 1) return partes[0] || "";
  if (partes.length === 2) return `${partes[0]}.${partes[1]}`;
  if (partes.length === 3) return `${partes[0]}.${partes[1]}.${partes[2]}`;
  return `${partes[0]}.${partes[1]}.${partes[2]}-${partes[3]}`;
}

export function idadeMinimaOk(dataNascimentoISO, idadeMinima = 18) {
  if (!dataNascimentoISO) return false;
  const nascimento = new Date(dataNascimentoISO);
  if (Number.isNaN(nascimento.getTime())) return false;

  const hoje = new Date();
  let idade = hoje.getFullYear() - nascimento.getFullYear();
  const aindaNaoFezAniversario =
    hoje.getMonth() < nascimento.getMonth() ||
    (hoje.getMonth() === nascimento.getMonth() && hoje.getDate() < nascimento.getDate());
  if (aindaNaoFezAniversario) idade -= 1;

  return idade >= idadeMinima;
}

export function nomeCompletoValido(nome) {
  const limpo = (nome || "").trim();
  return limpo.length >= 3 && limpo.length <= 100 && /^[A-Za-zÀ-ÿ\s]+$/.test(limpo);
}

export function senhaValida(senha) {
  if (!senha || senha.length < 8 || senha.length > 128) return false;
  return /[A-Za-z]/.test(senha) && /\d/.test(senha);
}
