# i18n-Ready Architecture — estrutura multilíngue desde o dia 1

> Skill obrigatória para qualquer projeto com UI, mesmo que lance em idioma único. Preparar arquitetura para i18n no dia 1 custa ~zero; adicionar depois custa refactor completo de templates.

## Princípio central

Separar **strings** (que mudam por locale) de **código** (que não muda) via extração. Toda string visível ao usuário vai para um arquivo de resources. Toda data/número/moeda passa por formatter com locale. Sem isso, cada tela vira obstáculo de tradução.

## Escolha da biblioteca

| Framework | Recomendado | Alternativa |
|-----------|-------------|-------------|
| Angular / Ionic | `@ngx-translate/core` ou Transloco | `@angular/localize` (estático, build-time) |
| React | `react-i18next` ou `react-intl` | `@lingui/react` |
| Vue | `vue-i18n` | — |
| Backend (Python) | `babel` | `gettext` |

**Trade-off:** `@angular/localize` tem build-time replacement (zero runtime) mas exige rebuild por locale. `ngx-translate` é runtime, permite switch sem rebuild. Para apps com usuários multi-locale no mesmo bundle: runtime. Para sites estáticos: build-time.

## Estrutura de arquivos

```
src/
├── assets/i18n/
│   ├── pt-BR.json       ← idioma primário, fonte de verdade
│   ├── en-US.json       ← tradução
│   └── es-ES.json
├── app/
│   └── core/
│       └── i18n/
│           ├── translation.service.ts
│           └── locale.guard.ts
```

`pt-BR.json`:
```json
{
  "common": {
    "save": "Salvar",
    "cancel": "Cancelar",
    "confirm": "Confirmar",
    "loading": "Carregando..."
  },
  "orders": {
    "list.title": "Seus pedidos",
    "list.empty": "Nenhum pedido ainda",
    "list.empty_cta": "Fazer primeiro pedido",
    "detail.status.pending": "Aguardando",
    "detail.status.confirmed": "Confirmado",
    "detail.status.cancelled": "Cancelado"
  },
  "errors": {
    "network.offline": "Sem conexão",
    "network.timeout": "Demorou demais, tente novamente",
    "validation.required": "Campo obrigatório",
    "validation.cpf_invalid": "CPF inválido"
  }
}
```

## Regras

### Zero string hardcoded em template

```html
<!-- ❌ -->
<h1>Seus pedidos</h1>
<button>Confirmar</button>

<!-- ✅ -->
<h1>{{ 'orders.list.title' | translate }}</h1>
<button>{{ 'common.confirm' | translate }}</button>
```

### Zero string hardcoded em componente

```typescript
// ❌
this.toast.show('Pedido enviado');

// ✅
this.toast.show(this.translate.instant('orders.sent'));
```

### Interpolação via placeholder

```json
{"greeting": "Olá, {{name}}! Você tem {{count}} pedido(s)."}
```

```html
<p>{{ 'greeting' | translate: { name: user.name, count: orderCount } }}</p>
```

### Pluralização via ICU expressions

```json
{
  "orders.count": "{count, plural, =0 {Nenhum pedido} =1 {1 pedido} other {{count} pedidos}}"
}
```

Bibliotecas suportam ICU nativamente (ngx-translate-messageformat, react-intl).

### Datas: DatePipe com locale

```html
<!-- ❌ -->
<span>{{ order.created_at.toString().slice(0, 10) }}</span>

<!-- ❌ formatação manual -->
<span>{{ order.created_at | date:'dd/MM/yyyy' }}</span>

<!-- ✅ locale-aware -->
<span>{{ order.created_at | date:'mediumDate':undefined:currentLocale }}</span>
```

Registrar locales em `app.module.ts`:
```typescript
import { registerLocaleData } from '@angular/common';
import localePtBr from '@angular/common/locales/pt';
import localeEn from '@angular/common/locales/en';

registerLocaleData(localePtBr);
registerLocaleData(localeEn);
```

### Números e moeda: pipes locale-aware

```html
<!-- ❌ -->
<span>R$ {{ amount.toFixed(2).replace('.', ',') }}</span>

<!-- ✅ -->
<span>{{ amount | currency:'BRL':'symbol':'1.2-2':currentLocale }}</span>
<span>{{ percentage | percent:'1.1-2':currentLocale }}</span>
```

### Strings de erro externalizadas

```typescript
// ❌ hardcoded na exception
throw new Error('CPF deve ter 11 dígitos');

// ✅ error code, mensagem via i18n no UI
throw new AppError('VALIDATION_CPF_INVALID', { length: cpf.length });

// no UI:
catch (err) {
  if (err instanceof AppError) {
    this.toast.error(this.translate.instant(`errors.${err.code.toLowerCase()}`, err.details));
  }
}
```

## Backend i18n

Quando backend retorna mensagens visíveis ao usuário:

### `Accept-Language` header

```python
# middleware
from babel import Locale

async def locale_middleware(request: Request, call_next):
    header = request.headers.get('Accept-Language', 'pt-BR')
    locale = Locale.parse(header.split(',')[0].replace('-', '_'))
    request.state.locale = locale
    return await call_next(request)
```

### Mensagens via lookup

```python
# backend/app/i18n/messages.py
MESSAGES = {
    'pt-BR': {
        'RESOURCE_NOT_FOUND': 'Recurso não encontrado',
        'VALIDATION_CPF_INVALID': 'CPF inválido',
    },
    'en-US': {
        'RESOURCE_NOT_FOUND': 'Resource not found',
        'VALIDATION_CPF_INVALID': 'Invalid CPF',
    },
}

def t(code: str, locale: str = 'pt-BR', **kwargs) -> str:
    msg = MESSAGES.get(locale, MESSAGES['pt-BR']).get(code, code)
    return msg.format(**kwargs)

# uso
raise HTTPException(404, detail={
    'code': 'RESOURCE_NOT_FOUND',
    'message': t('RESOURCE_NOT_FOUND', request.state.locale),
})
```

### Datas e números via Babel

```python
from babel.dates import format_datetime
from babel.numbers import format_currency

format_datetime(datetime.utcnow(), locale='pt_BR')
# '22 de abr. de 2026, 10:00:00'

format_currency(Decimal('450.50'), 'BRL', locale='pt_BR')
# 'R$ 450,50'
```

## Locale routing

### URL-based (preferido para SEO)

```
/pt-BR/orders
/en-US/orders
/es-ES/orders
```

```typescript
// app-routing.module.ts
{
  path: ':locale',
  canActivate: [LocaleGuard],
  children: [
    { path: 'orders', component: OrdersComponent },
    // ...
  ]
}
```

`LocaleGuard` valida locale suportado, seta no `TranslationService`, redireciona para default se inválido.

### Detecção automática

```typescript
detectLocale(): string {
  // 1. URL
  const url = this.router.url.match(/^\/([a-z]{2}-[A-Z]{2})\//);
  if (url) return url[1];
  
  // 2. User preference (localStorage, cookie)
  const saved = localStorage.getItem('locale');
  if (saved && this.supported.includes(saved)) return saved;
  
  // 3. Browser
  const browser = navigator.language;
  const matched = this.supported.find(l => l.startsWith(browser.split('-')[0]));
  if (matched) return matched;
  
  // 4. Default
  return 'pt-BR';
}
```

## RTL (right-to-left)

Se há chance de suportar árabe, hebraico, persa:

```html
<html [attr.dir]="isRtl ? 'rtl' : 'ltr'" [lang]="currentLocale">
```

CSS com `logical properties` no lugar de `left`/`right`:
```css
/* ❌ */
.card { margin-left: 16px; padding-right: 8px; }

/* ✅ RTL-aware */
.card { margin-inline-start: 16px; padding-inline-end: 8px; }
```

## Formatação locale-aware — armadilhas

### Timezone vs locale

São independentes. `pt-BR` não implica `America/Sao_Paulo` — pode ser Portugal, Moçambique, Angola.

```typescript
// guardar sempre UTC no banco
// apresentar no timezone do usuário
const userTz = Intl.DateTimeFormat().resolvedOptions().timeZone;  // ex: 'America/Sao_Paulo'
```

### Ordenação de strings

```typescript
// ❌ ASCII sort
names.sort()  // 'Ávila' vem depois de 'Zambrano'

// ✅ locale-aware
names.sort((a, b) => a.localeCompare(b, currentLocale))
```

### Comparação case-insensitive

```typescript
// ❌ algumas línguas quebram (turco 'İ' vs 'i')
str.toLowerCase() === other.toLowerCase()

// ✅
str.localeCompare(other, currentLocale, { sensitivity: 'accent' }) === 0
```

## Workflow de tradução

### Extração automática

```bash
# Angular com Transloco
npx transloco-keys-manager extract

# gera scripts/i18n-report.json
# novas chaves faltando: lista
# chaves órfãs: lista (não usadas em nenhum template)
```

CI bloqueia PR com chaves faltando:
```yaml
- name: Check i18n coverage
  run: |
    npx transloco-keys-manager extract --strict
    # falha se diff em pt-BR.json
```

### Review de tradução

- Não usar Google Translate cego
- Tradutor profissional ou nativo para strings visíveis
- Reviewer do projeto confere contexto (UI + screenshot)
- Cada chave tem comentário de contexto:

```json
{
  "orders.list.empty": "Nenhum pedido ainda",
  "_comment_orders.list.empty": "Aparece quando user não tem pedidos. Tom: convidativo, não melancólico."
}
```

## Testing i18n

```typescript
describe('orders page', () => {
  it('renders in pt-BR by default', () => {
    expect(screen.getByText('Seus pedidos')).toBeInTheDocument();
  });
  
  it('renders in en-US when locale changed', async () => {
    await setLocale('en-US');
    expect(screen.getByText('Your orders')).toBeInTheDocument();
  });
  
  it('has no hardcoded strings', () => {
    const template = fixture.nativeElement.innerHTML;
    const hardcoded = detectHardcodedText(template);  // regex custom
    expect(hardcoded).toEqual([]);
  });
});
```

Pseudo-locale para detectar strings não traduzidas em QA:
```typescript
// substitui chars por accented: "Save" → "Šåvé"
if (env.pseudoLocale) {
  const pseudo = Object.fromEntries(
    Object.entries(original).map(([k, v]) => [k, pseudolocalize(v)])
  );
  translations['pseudo'] = pseudo;
}
```

Qualquer string ainda em inglês simples = hardcoded detectado visualmente.

## Anti-patterns

- Concatenar strings traduzidas (`'Você tem ' + count + ' pedidos'` → usar ICU)
- Assumir ordem de palavras igual entre línguas (`<b>Nome:</b> {{ x }}` — em línguas SOV a ordem muda)
- `toFixed(2)` para dinheiro (não respeita separador local)
- Salvar strings localizadas no banco (use codes, traduza na apresentação)
- Misturar locales na UI (parte em pt, parte em en porque falta tradução) → fallback explícito com pseudo-locale é melhor
- Refatorar i18n "depois do MVP" — custa 5-10x mais
- Hardcode de símbolo de moeda (`'R$ '`) em vez de CurrencyPipe

## Checklist para PLAN.md

- [ ] Biblioteca i18n instalada (ngx-translate / Transloco / etc.)
- [ ] `src/assets/i18n/pt-BR.json` (fonte de verdade) existe
- [ ] Zero string hardcoded em templates novos desta fase
- [ ] Zero string hardcoded em componentes (toasts, alerts, logs de erro)
- [ ] Datas via DatePipe com locale; nunca format manual
- [ ] Moedas via CurrencyPipe; nunca `R$ ${x.toFixed(2)}`
- [ ] Pluralização via ICU (não if/else)
- [ ] Error codes no backend; mensagens traduzidas no cliente
- [ ] `Accept-Language` middleware no backend (se serve mensagens ao user)
- [ ] Locale detection em URL ou preferência salva
- [ ] CI roda `extract --strict` bloqueando chaves faltando
- [ ] Comentário de contexto em chaves não-óbvias
