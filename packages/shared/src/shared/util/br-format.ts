/**
 * Brazilian form masking + validation (brazilian-forms). Server is the authority
 * (validate-docbr); these are UX conveniences. CNPJ supports the alphanumeric
 * format (jul/2026) — we keep alphanumerics, not just digits.
 */

/** Keep alphanumerics (CNPJ alphanumeric jul/2026) uppercased. */
export function normalizeDoc(raw: string): string {
  return raw.replace(/[^0-9A-Za-z]/g, '').toUpperCase();
}

/** Mask a CNPJ as 00.000.000/0001-00 (digits or alphanumeric body). */
export function maskCnpj(raw: string): string {
  const v = normalizeDoc(raw).slice(0, 14);
  const p = [v.slice(0, 2), v.slice(2, 5), v.slice(5, 8), v.slice(8, 12), v.slice(12, 14)];
  let out = p[0];
  if (p[1]) out += '.' + p[1];
  if (p[2]) out += '.' + p[2];
  if (p[3]) out += '/' + p[3];
  if (p[4]) out += '-' + p[4];
  return out;
}

/** Mask a CPF as 000.000.000-00. */
export function maskCpf(raw: string): string {
  const v = raw.replace(/\D/g, '').slice(0, 11);
  const p = [v.slice(0, 3), v.slice(3, 6), v.slice(6, 9), v.slice(9, 11)];
  let out = p[0];
  if (p[1]) out += '.' + p[1];
  if (p[2]) out += '.' + p[2];
  if (p[3]) out += '-' + p[3];
  return out;
}

/** Mask a BR mobile phone as (DD) 9XXXX-XXXX. */
export function maskPhone(raw: string): string {
  const v = raw.replace(/\D/g, '').slice(0, 11);
  if (v.length <= 2) return v.length ? `(${v}` : '';
  if (v.length <= 7) return `(${v.slice(0, 2)}) ${v.slice(2)}`;
  return `(${v.slice(0, 2)}) ${v.slice(2, 7)}-${v.slice(7)}`;
}

/** Normalise a masked BR mobile to E.164 (+55DDXXXXXXXXX). */
export function phoneToE164(masked: string): string {
  const v = masked.replace(/\D/g, '');
  return v ? `+55${v}` : '';
}

/** Mask a CEP as 00000-000. */
export function maskCep(raw: string): string {
  const v = raw.replace(/\D/g, '').slice(0, 8);
  return v.length > 5 ? `${v.slice(0, 5)}-${v.slice(5)}` : v;
}

/** True when a CNPJ has the full 14-char body (alphanumeric tolerant). */
export function isCnpjComplete(masked: string): boolean {
  return normalizeDoc(masked).length === 14;
}

/** True when a CPF has 11 digits. */
export function isCpfComplete(masked: string): boolean {
  return masked.replace(/\D/g, '').length === 11;
}

/** True when a BR mobile has 11 digits (DDD + 9 digits). */
export function isPhoneComplete(masked: string): boolean {
  return masked.replace(/\D/g, '').length === 11;
}

/** True when a CEP has 8 digits. */
export function isCepComplete(masked: string): boolean {
  return masked.replace(/\D/g, '').length === 8;
}
