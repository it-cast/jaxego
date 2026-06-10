# Brazilian Forms — formulários com campos BR corretos

> Skill obrigatória para qualquer form que tenha CPF, CNPJ, CEP, telefone BR, ou outros campos específicos do Brasil.

## Campos cobertos

- CPF
- CNPJ
- CEP + endereço (via ViaCEP)
- Telefone BR (celular e fixo)
- RG (quando necessário)
- PIS/PASEP
- Inscrição Estadual
- Título de Eleitor
- CNH
- Conta bancária (banco/agência/conta)

## CPF

### Validação (dígito verificador)

```typescript
export function isValidCPF(raw: string): boolean {
  const cpf = raw.replace(/\D/g, '');
  
  if (cpf.length !== 11) return false;
  
  // Rejeita sequências tipo 111.111.111-11
  if (/^(\d)\1{10}$/.test(cpf)) return false;
  
  // Dígito verificador
  let sum = 0;
  for (let i = 0; i < 9; i++) sum += parseInt(cpf[i]) * (10 - i);
  let d1 = 11 - (sum % 11);
  if (d1 >= 10) d1 = 0;
  if (d1 !== parseInt(cpf[9])) return false;
  
  sum = 0;
  for (let i = 0; i < 10; i++) sum += parseInt(cpf[i]) * (11 - i);
  let d2 = 11 - (sum % 11);
  if (d2 >= 10) d2 = 0;
  if (d2 !== parseInt(cpf[10])) return false;
  
  return true;
}
```

### Máscara

`000.000.000-00` via inputmode numeric + máscara progressiva:

```typescript
export function maskCPF(value: string): string {
  const digits = value.replace(/\D/g, '').slice(0, 11);
  return digits
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1-$2');
}
```

### HTML

```html
<label for="cpf">CPF</label>
<input 
  id="cpf" 
  name="cpf"
  type="text"
  inputmode="numeric"
  autocomplete="off"
  placeholder="000.000.000-00"
  maxlength="14"
  aria-describedby="cpf-error"
/>
```

**NUNCA** `type="number"` — perde leading zeros, navegador não permite máscara.

### Mensagem de erro

- ❌ "CPF inválido"
- ✅ "CPF deve ter 11 dígitos" (se comprimento errado)
- ✅ "CPF com dígito verificador inválido" (se formato ok mas DV errado)
- ✅ "CPF não pode ser uma sequência" (111.111.111-11)

### Anti-patterns

- ❌ Validar só length sem DV
- ❌ Permitir CPF sequencial como "111.111.111-11"
- ❌ Guardar CPF com máscara no banco. **Sempre só dígitos no banco**, format na apresentação
- ❌ Mostrar CPF completo em UI de admin (usar `000.000.000-XX` ou mask parcial)

## CNPJ

### Validação

```typescript
export function isValidCNPJ(raw: string): boolean {
  const cnpj = raw.replace(/\D/g, '');
  
  if (cnpj.length !== 14) return false;
  if (/^(\d)\1{13}$/.test(cnpj)) return false;
  
  const weights1 = [5,4,3,2,9,8,7,6,5,4,3,2];
  const weights2 = [6,5,4,3,2,9,8,7,6,5,4,3,2];
  
  let sum = 0;
  for (let i = 0; i < 12; i++) sum += parseInt(cnpj[i]) * weights1[i];
  let d1 = sum % 11 < 2 ? 0 : 11 - (sum % 11);
  if (d1 !== parseInt(cnpj[12])) return false;
  
  sum = 0;
  for (let i = 0; i < 13; i++) sum += parseInt(cnpj[i]) * weights2[i];
  let d2 = sum % 11 < 2 ? 0 : 11 - (sum % 11);
  if (d2 !== parseInt(cnpj[13])) return false;
  
  return true;
}
```

### Máscara

`00.000.000/0000-00`:

```typescript
export function maskCNPJ(value: string): string {
  return value.replace(/\D/g, '').slice(0, 14)
    .replace(/(\d{2})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1/$2')
    .replace(/(\d{4})(\d)/, '$1-$2');
}
```

## CEP + Endereço (via ViaCEP)

### Padrão canônico

1. Campo CEP primeiro, com máscara `00000-000`
2. Ao completar 8 dígitos: auto-consulta ViaCEP
3. Se encontrado: preenche logradouro, bairro, cidade, UF automaticamente (readonly por default, editável pelo usuário)
4. Se não encontrado: mantém campos editáveis + mensagem "CEP não encontrado. Preencha manualmente."

```typescript
async function fetchCEP(cep: string): Promise<ViaCEPResult | null> {
  const digits = cep.replace(/\D/g, '');
  if (digits.length !== 8) return null;
  
  try {
    const r = await fetch(`https://viacep.com.br/ws/${digits}/json/`, { 
      signal: AbortSignal.timeout(5000) 
    });
    if (!r.ok) return null;
    const data = await r.json();
    if (data.erro) return null;
    return data;
  } catch {
    return null;
  }
}

// Uso
onCEPComplete(cep: string) {
  this.loading = true;
  fetchCEP(cep).then((result) => {
    this.loading = false;
    if (result) {
      this.form.patchValue({
        logradouro: result.logradouro,
        bairro: result.bairro,
        cidade: result.localidade,
        uf: result.uf,
      });
      // Focar no campo "número" (nunca preenche automaticamente)
      this.numeroInput.focus();
    }
  });
}
```

### Campos do endereço

Sempre coletar separadamente:
- CEP
- Logradouro (rua/avenida)
- Número (**nunca** vem do ViaCEP)
- Complemento (opcional)
- Bairro
- Cidade
- UF

**Não** concatenar em um "endereço" único de texto livre — impossível validar ou usar para lógica geográfica.

## Telefone BR

### Formatos aceitos

- Celular: `(00) 00000-0000` (11 dígitos após DDD) 
- Fixo: `(00) 0000-0000` (10 dígitos após DDD)

### Validação

```typescript
export function isValidPhoneBR(raw: string): boolean {
  const digits = raw.replace(/\D/g, '');
  if (digits.length !== 10 && digits.length !== 11) return false;
  
  const ddd = parseInt(digits.substring(0, 2));
  const validDDDs = [11,12,13,14,15,16,17,18,19, 21,22,24, 27,28, 31,32,33,34,35,37,38, 41,42,43,44,45,46, 47,48,49, 51,53,54,55, 61, 62,64, 63, 65,66, 67, 68, 69, 71,73,74,75,77, 79, 81,87, 82, 83, 84, 85,88, 86,89, 91,93,94, 92,97, 95, 96, 98,99];
  if (!validDDDs.includes(ddd)) return false;
  
  // Celular deve começar com 9
  if (digits.length === 11 && digits[2] !== '9') return false;
  
  return true;
}
```

### Máscara

```typescript
export function maskPhoneBR(value: string): string {
  const d = value.replace(/\D/g, '').slice(0, 11);
  if (d.length <= 10) {
    return d.replace(/(\d{2})(\d)/, '($1) $2').replace(/(\d{4})(\d)/, '$1-$2');
  }
  return d.replace(/(\d{2})(\d)/, '($1) $2').replace(/(\d{5})(\d)/, '$1-$2');
}
```

### HTML

```html
<input 
  type="tel"
  inputmode="numeric"
  autocomplete="tel"
  placeholder="(00) 00000-0000"
/>
```

## Autofill

Browser autofill correto poupa o usuário. Atributos:

```html
<!-- Nome completo -->
<input name="full_name" autocomplete="name" />

<!-- Email -->
<input name="email" type="email" autocomplete="email" />

<!-- Telefone -->
<input name="phone" type="tel" autocomplete="tel" />

<!-- Endereço -->
<input name="cep" autocomplete="postal-code" />
<input name="logradouro" autocomplete="address-line1" />
<input name="numero" autocomplete="address-line2" />
<input name="bairro" autocomplete="address-level3" />
<input name="cidade" autocomplete="address-level2" />
<input name="uf" autocomplete="address-level1" />
<input name="pais" autocomplete="country-name" value="Brasil" />
```

CPF/CNPJ não têm autocomplete padrão — usar `autocomplete="off"` para não confundir browser.

## Storage no banco

| Campo | Banco | Apresentação |
|-------|-------|--------------|
| CPF | `cpf VARCHAR(11)` só dígitos | `000.000.000-00` |
| CNPJ | `cnpj VARCHAR(14)` só dígitos | `00.000.000/0000-00` |
| CEP | `cep VARCHAR(8)` só dígitos | `00000-000` |
| Telefone | `phone VARCHAR(11)` só dígitos | `(00) 00000-0000` |

Índice único em CPF/CNPJ quando aplicável.

## LGPD: campos sensíveis

CPF, CNPJ, telefone e endereço são **PII** sob LGPD. Consultar skill `lgpd-compliance` para:
- Consentimento explícito na coleta
- Logs sem PII
- Direito de exclusão
- Criptografia em repouso (opcional mas recomendado)

## Testes obrigatórios

```typescript
describe('CPF validation', () => {
  test.each([
    ['000.000.000-00', false],  // sequência
    ['111.111.111-11', false],
    ['123.456.789-01', false],  // DV errado
    ['123.456.789-09', true],   // DV correto (fictício)
    ['12345678909', true],      // sem máscara
    ['', false],
    ['abc', false],
  ])('%s => %s', (input, expected) => {
    expect(isValidCPF(input)).toBe(expected);
  });
});
```

## Componentes reutilizáveis a criar

No design system do projeto (uma vez só):
- `<cpf-input>` — máscara + validação + erro inline
- `<cnpj-input>` — idem
- `<cep-input>` — máscara + ViaCEP auto-fetch + emite evento com endereço
- `<phone-br-input>` — máscara + validação de DDD

Forms consomem esses componentes. Nenhum form reimplementa máscara.

## Checklist para PLAN.md

Quando a task toca form com campos BR:

- [ ] Máscara aplicada no cliente (sem `type="number"`)
- [ ] Validação client-side com DV (CPF/CNPJ) — não só length
- [ ] Validação server-side redundante (cliente pode ser bypass)
- [ ] Guardar no banco só dígitos
- [ ] CEP integra com ViaCEP, preenche endereço, não bloqueia manual
- [ ] Autocomplete attributes corretos
- [ ] Mensagens de erro específicas (não "inválido")
- [ ] Componente reutilizável do design system usado (não inline)
- [ ] LGPD considerada: consent, log sem PII
