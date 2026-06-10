# Error UX — padrões de experiência em estados de erro

> Skill obrigatória para fases com UI ou endpoint retornando erros visíveis ao usuário.
> Endereça a lacuna do relatório 3: "Algo deu errado" + retry genérico.

## Princípio central

Todo erro visível ao usuário deve responder 3 perguntas:

1. **O que aconteceu?** — específico, não genérico
2. **O que eu posso fazer agora?** — ação concreta
3. **De quem é a responsabilidade?** — minha (usuário), do sistema, ou de terceiros

Mensagem que falha em qualquer uma dessas é inútil.

## Taxonomia de erros

| Categoria | Exemplo | Onde aparece | Prioridade de UX |
|-----------|---------|--------------|------------------|
| **Validação de input** | CPF inválido, email malformado | Inline ao blur, antes do submit | Alta — 100% dos forms |
| **Negócio** | "Este item não está mais disponível no estoque" | Modal ou toast após ação | Alta — feedback claro |
| **Permissão** | "Você não tem acesso a este workspace" | Tela dedicada ou modal | Média |
| **Rede/conectividade** | Offline, timeout | Banner persistente + retry auto | Alta — muito comum |
| **Servidor (5xx)** | Exception não tratada | Página ou modal + contato suporte | Média — raro |
| **Not found (404)** | Rota/recurso inexistente | Página customizada | Baixa |
| **Rate limit (429)** | "Muitas tentativas" | Modal com countdown | Média |

## Regras por categoria

### Validação de input

**Quando mostrar o erro:**
- ❌ Ao submeter o form todo (ruim — forma "scan and fix")
- ✅ Ao `blur` do campo (ao sair do input) + resubmit se o erro persistir

**Formato da mensagem:**
- ❌ "Campo inválido"
- ❌ "Por favor, verifique este campo"
- ✅ "CPF deve ter 11 dígitos. Faltam 2."
- ✅ "Email precisa de um '@'. Você escreveu 'joao.gmail.com'."

**Posicionamento:**
- Abaixo do input, cor `--color-danger-500`, ícone ⚠️ opcional
- `aria-describedby` apontando para a mensagem
- Input recebe `aria-invalid="true"` + borda vermelha

### Negócio

Erro de negócio não é culpa de UX nem de código — é estado real do sistema.

**Formato:**
- Título: o que aconteceu
- Corpo: por que aconteceu (se útil para decisão)
- CTA: o que fazer agora

**Exemplo (concorrência sobre recurso único):**
- ❌ "Erro ao reservar item"
- ✅ Título: "Este item acabou de ser reservado por outro usuário"
  Corpo: "Isso acontece quando há concorrência pelo mesmo recurso. Você pode ver alternativas similares."
  CTA: `[Ver disponíveis]`

### Rede/conectividade

**Offline detectado:**

```typescript
// Detectar usando navigator.onLine + ping real (onLine tem falsos positivos)
async function isOnline(): Promise<boolean> {
  if (!navigator.onLine) return false;
  try {
    const r = await fetch('/api/health', { signal: AbortSignal.timeout(3000) });
    return r.ok;
  } catch {
    return false;
  }
}
```

**Banner persistente (não toast):**
- Posição: top ou bottom, altura ~40px
- Cor: `--color-warning-500` (não danger — offline é estado, não erro)
- Texto: "Sem conexão. Tentando reconectar..."
- Botão: "Tentar agora" (não automatizar infinitamente)

**Mobile:** ver skill `mobile/offline-first` para fila de ações + sync.

### Servidor (5xx)

Exception inesperada. Três níveis de tratamento:

1. **Tela dedicada** para rotas inteiras: `<error-page>` com:
   - Ilustração neutra (não dramática)
   - Texto: "Algo não funcionou como esperado. Nossa equipe foi notificada."
   - ID de rastreamento Sentry exibido em monospace pequeno
   - CTAs: `[Tentar novamente]` `[Voltar ao início]`

2. **Modal** para ações dentro de tela: mesma estrutura, mas dentro de um dialog.

3. **Toast** para ações secundárias: "Não conseguimos salvar. Tentando novamente..." + retry automático.

**IMPORTANTE:**
- Sempre loggar exception no Sentry com `requestId`, `userId`, `endpoint`
- IDs de rastreamento visíveis permitem suporte investigar
- NUNCA expor stack trace ao usuário

### Not found (404)

- Rota inteira: página dedicada com busca + navegação
- Recurso específico (ex: item X não existe): modal explicativo + CTA para listagem

### Rate limit (429)

```
Título: "Muitas tentativas"
Corpo: "Por segurança, limitamos tentativas de login. Você pode tentar novamente em 2 minutos."
CTA: `[OK]` + countdown visual do timer
```

Após countdown chegar a zero, CTA vira `[Tentar agora]`.

## Retry patterns

### Retry automático (rede, 5xx intermitente)

- Retry count máximo: 3
- Backoff exponencial: 1s, 2s, 4s
- Feedback visual: "Tentando novamente... (2 de 3)"
- Após falhar: mostrar erro final com CTA manual

```typescript
async function withRetry<T>(fn: () => Promise<T>, opts = { tries: 3, baseMs: 1000 }): Promise<T> {
  let lastErr: unknown;
  for (let i = 0; i < opts.tries; i++) {
    try {
      return await fn();
    } catch (err) {
      lastErr = err;
      if (i < opts.tries - 1) {
        await new Promise(r => setTimeout(r, opts.baseMs * 2 ** i));
      }
    }
  }
  throw lastErr;
}
```

### Retry manual

Botão explícito "Tentar novamente":
- Desabilita-se enquanto requisição em curso
- Loading state visual (spinner inline ou skeleton)
- Se falhar de novo: mensagem ajustada "Ainda não funcionou. Tente em alguns minutos."

## Toast vs. Modal vs. Inline vs. Página

| Tipo | Quando usar | Duração | Anti-patterns |
|------|-------------|---------|---------------|
| **Inline** | Validação de input, erro localizado | Persistente até correção | Não modal para erro de campo |
| **Toast** | Feedback não bloqueante | 4-6s, pausa em hover | Não para erro crítico (fica invisível para quem não viu a tempo) |
| **Modal** | Ação destrutiva falhou, confirmação necessária | Persistente até descartar | Não para erro de UX corrigível (é muito peso) |
| **Página** | Erro bloqueia toda a rota (404, 500, acesso negado) | Persistente | Não para erro de campo |

## Componentes a construir

Todo projeto deve ter estes componentes no design system:

1. `<error-inline>` — mensagem abaixo de input
2. `<error-banner>` — banner persistente (offline, manutenção)
3. `<error-toast>` — toast efêmero
4. `<error-modal>` — dialog de erro bloqueante
5. `<error-page>` — fullscreen (404, 500, 403)
6. `<error-boundary>` — React boundary / Angular ErrorHandler que captura exception e renderiza `error-modal` ou `error-page`

## Logging

Para cada erro exibido ao usuário, loggar:

```typescript
logger.warn('user_visible_error', {
  error_type: 'validation' | 'business' | 'network' | 'server' | 'not_found' | 'rate_limit',
  error_code: 'INVALID_CPF' | 'PROPOSAL_ALREADY_ACCEPTED' | ...,
  page: window.location.pathname,
  user_action: 'submit_proposal',
  request_id: '...',
  user_id: '...',
  // NUNCA logar: input value com PII, password, token
});
```

Permite analisar quais erros acontecem mais, quais causam abandono, quais precisam melhorar.

## Copy-lib por locale

Criar em `docs/identidade-visual/error-copy.{locale}.json`:

```json
{
  "network.offline": "Sem conexão. Tentando reconectar...",
  "network.timeout": "Demorou demais. Tente novamente.",
  "network.generic": "Não conseguimos conectar ao servidor.",
  "validation.cpf.invalid": "CPF deve ter 11 dígitos válidos.",
  "validation.email.invalid": "Email precisa de '@' e domínio.",
  "business.resource.already_taken": "Este recurso já foi reservado por outro usuário.",
  "business.payment.insufficient": "Saldo insuficiente. Escolha outra forma de pagamento.",
  "server.generic": "Algo não funcionou como esperado. Nossa equipe foi notificada.",
  "not_found.page": "Essa página não existe.",
  "not_found.resource": "Esse item não foi encontrado. Pode ter sido removido."
}
```

Componentes consomem por chave, nunca hardcode.

## Checklist para PLAN.md (fases com UI)

Copiar para `## Error UX checklist`:

- [ ] Todo input de form tem validação inline com mensagem específica
- [ ] Estados de erro não usam "Ops!" nem "Algo deu errado" genérico
- [ ] Erro de rede mostra banner + retry auto com backoff
- [ ] Erro 5xx mostra ID de rastreamento Sentry visível
- [ ] 404 customizado se fase adiciona rotas novas
- [ ] Rate limit tem countdown visual
- [ ] Toast vs modal: decisão documentada (não usar toast para erro crítico)
- [ ] `<error-boundary>` ou equivalente no root para capturar exceptions
- [ ] Copy de erro vem de `error-copy.{locale}.json`, nenhum hardcode
- [ ] Logging de user_visible_error em todos os estados acima
