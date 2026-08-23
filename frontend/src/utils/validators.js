export function somenteDigitos(valor) {
  return (valor || "").replace(/\D/g, "");
}

const REGEX_EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function emailValido(email) {
  if (!email) return false;
  return REGEX_EMAIL.test(email.trim()) && email.trim().length <= 254;
}
