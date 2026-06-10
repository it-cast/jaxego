---
name: feedback-patterns
category: ux-advanced
description: Sistema completo de feedback de ações do usuário — toast, snackbar, banner, modal, inline validation, status badges, progress indicators. Inclui matriz de decisão por contexto (qual padrão usar quando), snippets React/Angular/Ionic, tom de mensagem, hierarquia de severidade e accessibility. Resolve "cliquei e nada aconteceu" e "erro grave que some em 3 segundos".
---

# Feedback Patterns — Padrões de Feedback ao Usuário

> Toda ação tem que ter feedback. Se for >100ms sem feedback, usuário acha que não funcionou e clica de novo.

Esta skill define **qual tipo de feedback usar em cada contexto**, com snippets prontos e tom de mensagem.

---

## 1. Quando esta skill é obrigatória

| Momento | Por quê |
|---|---|
| Toda phase com forms (validação inline) | Feedback de campo |
| Toda phase com submits (toast/banner) | Confirmação ou erro |
| Toda phase com pagamento (modal de confirmação) | Ação de alto risco |
| Toda phase com delete (confirmação + undo) | Ação destrutiva |
| Toda phase com estado de objeto (badges) | Status visível |

## 2. Quando NÃO usar

- Phase backend pura
- Phase de infra (CI/CD, deploy)
- Phase só de polish visual sem mudar interações

---

## 3. Os 8 tipos de feedback (mapeados)

### 3.1 Toast / Snackbar (efêmero)

**Quando usar:**
- Confirmação de ação não-crítica
- Notificação que não bloqueia
- Status update

**Não usar para:**
- Erros graves
- Confirmação de ação destrutiva
- Quando usuário PRECISA ler

**Boas práticas:**
- Posição consistente (geralmente bottom-right ou top-center)
- Auto-dismiss 3-5s
- Permitir dismiss manual (X)
- Empilhar verticalmente se múltiplos
- Animar entrada/saída suavemente
- Cor por tipo (success verde, info azul, warning amarelo)

**Exemplos:**

```
✅ "Item salvo" (success, 3s, dismissable)
✅ "3 mensagens novas" (info, 5s)
✅ "Pedido em andamento" (info, persistente até mudar status)

❌ "Erro fatal: dados perdidos" (deve ser modal/banner)
❌ "Confirme com sua senha para deletar" (deve ser modal)
```

**Implementação React (com sonner):**

```jsx
import { toast } from 'sonner';

function SaveButton() {
  const handleSave = async () => {
    try {
      await api.save();
      toast.success('Rascunho salvo');
    } catch (e) {
      toast.error('Não foi possível salvar', {
        description: 'Verifique sua conexão',
        action: {
          label: 'Tentar novamente',
          onClick: () => handleSave()
        }
      });
    }
  };

  return <button onClick={handleSave}>Salvar</button>;
}
```

**Implementação Angular/Ionic:**

```typescript
import { ToastController } from '@ionic/angular/standalone';

@Component({...})
export class SaveButtonComponent {
  toastCtrl = inject(ToastController);

  async handleSave() {
    try {
      await this.api.save();
      const toast = await this.toastCtrl.create({
        message: 'Rascunho salvo',
        duration: 3000,
        position: 'bottom',
        color: 'success'
      });
      await toast.present();
    } catch (e) {
      const toast = await this.toastCtrl.create({
        message: 'Não foi possível salvar',
        duration: 5000,
        position: 'bottom',
        color: 'danger',
        buttons: [
          { text: 'Tentar novamente', handler: () => this.handleSave() }
        ]
      });
      await toast.present();
    }
  }
}
```

### 3.2 Inline validation (validação de campo)

**Quando usar:**
- Validação de formulário em tempo real
- Feedback enquanto usuário digita

**Boas práticas:**
- Validar **on blur**, NÃO on change (frustrante validar a cada tecla)
- Mostrar erro abaixo do campo (não em tooltip)
- Cor + ícone (não só cor — daltônicos)
- Mensagem ajuda a corrigir (não só relata)
- Sucesso só se relevante (email único validado)

**Exemplos:**

```
✅ "Senha precisa ter 8+ caracteres com 1 número e 1 maiúscula"
✅ "Email já cadastrado. Esqueceu a senha?"
✅ "✓ Email disponível"

❌ "Senha inválida" (não diz como corrigir)
❌ "Erro" (genérico)
❌ Validação on change (mostra erro antes de terminar de digitar)
```

**Implementação React:**

```jsx
function PasswordField() {
  const [value, setValue] = useState('');
  const [error, setError] = useState(null);

  const validate = (val) => {
    if (val.length < 8) {
      return 'Mínimo 8 caracteres';
    }
    if (!/[A-Z]/.test(val)) {
      return 'Precisa ter pelo menos 1 letra maiúscula';
    }
    if (!/[0-9]/.test(val)) {
      return 'Precisa ter pelo menos 1 número';
    }
    return null;
  };

  return (
    <div className="field">
      <label htmlFor="password">Senha</label>
      <input
        id="password"
        type="password"
        value={value}
        onChange={(e) => {
          setValue(e.target.value);
          if (error) setError(null); // limpa erro ao digitar
        }}
        onBlur={() => setError(validate(value))}
        aria-invalid={!!error}
        aria-describedby={error ? 'password-error' : undefined}
      />
      {error && (
        <p id="password-error" role="alert" className="error">
          ⚠ {error}
        </p>
      )}
    </div>
  );
}
```

### 3.3 Banner (persistente, não bloqueante)

**Quando usar:**
- Avisos contextuais importantes (subscription expirando)
- Modo offline detectado
- Manutenção programada
- LGPD / cookie consent
- Versão nova disponível

**Boas práticas:**
- Topo da tela, full-width
- Variantes: info (azul), warning (amarelo), danger (vermelho), success (verde)
- Botão de dismiss SE não-crítico
- Persiste até resolver causa
- Pode ter CTA inline

**Exemplos:**

```
✅ Banner amarelo: "Sua assinatura expira em 3 dias. [Renovar agora]"
✅ Banner vermelho: "Modo offline. Algumas funcionalidades indisponíveis."
✅ Banner azul: "Nova versão disponível. [Ver novidades] [×]"
```

**Implementação:**

```jsx
function SubscriptionBanner({ daysLeft }) {
  if (daysLeft > 7) return null; // só mostra quando próximo

  const variant = daysLeft <= 3 ? 'danger' : 'warning';

  return (
    <div className={`banner banner-${variant}`} role="alert">
      <span>
        Sua assinatura expira em {daysLeft} dia(s).
      </span>
      <button className="btn-primary">Renovar agora</button>
    </div>
  );
}
```

### 3.4 Modal de confirmação (bloqueante)

**Quando usar:**
- Ações destrutivas (delete, cancel subscription)
- Decisões críticas (mudança de plano)
- Confirmação de pagamento
- Side effects irreversíveis

**Não usar para:**
- Confirmação trivial (interrompe fluxo desnecessariamente)
- Notificação simples (use toast)

**Boas práticas:**
- Título descreve ação ("Excluir conta?")
- Body explica consequências (com prazo se houver)
- Botão primário = ação destrutiva (vermelho)
- Botão secundário = cancelar (texto, não botão chamativo)
- Permitir Esc para cancelar
- Foco inicial no botão de cancelar (mais seguro)

**Exemplo:**

```
Title: "Excluir conta de Bruna do Atacarejo?"
Body: "Esta ação é irreversível.
       Todos os dados, pedidos e histórico serão deletados em 30 dias.
       Você ainda pode recuperar até essa data."
Primary: "Sim, excluir conta" (vermelho)
Secondary: "Cancelar" (foco inicial)
```

**Implementação React:**

```jsx
function DeleteAccountButton() {
  const [confirming, setConfirming] = useState(false);

  return (
    <>
      <button
        onClick={() => setConfirming(true)}
        className="btn-danger-ghost"
      >
        Excluir conta
      </button>

      {confirming && (
        <Modal onClose={() => setConfirming(false)}>
          <h2>Excluir conta?</h2>
          <p>
            Esta ação é irreversível. Todos os dados serão deletados
            em 30 dias. Você pode recuperar até essa data.
          </p>
          <div className="modal-actions">
            <button
              autoFocus
              onClick={() => setConfirming(false)}
              className="btn-ghost"
            >
              Cancelar
            </button>
            <button
              onClick={async () => {
                await api.deleteAccount();
                toast.success('Conta excluída. Você tem 30 dias para recuperar.');
              }}
              className="btn-danger"
            >
              Sim, excluir conta
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}
```

### 3.5 Empty state (ausência de dados)

Coberto por `ux-advanced/empty-states-polish`. Aqui apenas contextualizar:

- Lista vazia (primeiro uso, sem resultados de busca)
- Erro 404 contextual
- Nenhum filtro aplicado retornou resultado

### 3.6 Loading state (durante operação)

Coberto por `ux-advanced/loading-states`. Aqui apenas contextualizar.

### 3.7 Status badge

**Quando usar:**
- Estado de objeto (pedido pendente, pago, entregue)
- Conexão online/offline
- Health do sistema

**Boas práticas:**
- Cor + ícone + texto (acessibilidade)
- Tooltip com explicação se necessário
- Variantes consistentes em toda app

**Exemplos:**

```jsx
// ✅ Cor + ícone + texto
<Badge variant="warning">
  <ClockIcon /> Pendente
</Badge>

<Badge variant="success">
  <CheckIcon /> Pago
</Badge>

<Badge variant="danger">
  <XIcon /> Falhou
</Badge>

// ❌ Só cor (excluí daltônicos)
<Badge color="yellow">Pendente</Badge>
```

**CSS para badges:**

```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.5;
}

.badge-success {
  background: var(--color-feedback-success-subtle);
  color: var(--color-feedback-success-strong);
}
.badge-warning {
  background: var(--color-feedback-warning-subtle);
  color: var(--color-feedback-warning-strong);
}
.badge-danger {
  background: var(--color-feedback-danger-subtle);
  color: var(--color-feedback-danger-strong);
}
.badge-info {
  background: var(--color-feedback-info-subtle);
  color: var(--color-feedback-info-strong);
}
```

### 3.8 Progress indicator

**Quando usar:**
- Operação longa com etapas conhecidas (upload, multi-step form)
- Steps de wizard
- Carregamento determinístico

**Boas práticas:**
- Mostrar % se possível
- Indicar etapa atual e quantas faltam
- Permitir voltar (em wizards)
- Dar contexto ("Etapa 2 de 5: Endereço")

**Exemplos:**

```jsx
// Linear progress (operação determinística)
<div className="progress">
  <div className="progress-bar" style={{ width: `${percent}%` }} />
  <span className="progress-label">{percent}%</span>
</div>

// Stepper (wizard de checkout)
<Stepper currentStep={2} totalSteps={4}>
  <Step label="Carrinho" status="complete" />
  <Step label="Endereço" status="active" />
  <Step label="Pagamento" status="pending" />
  <Step label="Confirmação" status="pending" />
</Stepper>
```

---

## 4. Matriz de decisão (qual padrão usar quando)

| Ação do usuário | Feedback ideal | Notas |
|---|---|---|
| Salvar formulário simples | Toast success | Auto-dismiss |
| Salvar form longo (5+ min de trabalho) | Toast + redirect ou highlight de "salvo" | Mais explícito |
| Submeter pagamento | Loading dedicado → toast/page success | Crítico |
| Excluir item | Modal confirm → toast + opção desfazer | Reversível |
| Excluir conta (permanente) | Modal com prazo + senha | Crítico |
| Curtir post | Optimistic + animação sutil | Sem espera |
| Erro de validação | Inline + scroll para campo | Específico |
| Erro de rede | Banner persistente + botão retry | Não-bloqueante |
| Sessão expirada | Modal + redirect login | Inevitável |
| Update disponível | Banner não-crítico | Dismiss-able |
| Sem internet | Banner + funcionalidade offline | Persistente |
| Cookie consent (LGPD) | Banner bottom + 2 botões | Persistente até decisão |
| Confirmação trivial (favoritar) | Animação sutil + optimistic | Sem toast nem modal |
| Operação longa (>10s) | Progress + ETA | Modal ou page |
| Erro 500 do server | Toast danger + retry button | Recuperável |
| Item adicionado ao carrinho | Toast OU mini-cart preview | UX choice |
| Filtro aplicado em lista | Skeleton + toast contagem | Feedback claro |
| Login bem-sucedido | Redirect (não precisa toast) | Tela muda = feedback |
| Logout | Redirect para login (sem confirmação se rápido) | Toast só se demorou |
| Convite enviado | Toast + lista atualizada | Confirmação clara |

---

## 5. Hierarquia de severidade

```
INFO (azul/cinza)
  Não-crítico, informacional
  → Toast efêmero ou banner dismiss-able

SUCCESS (verde)
  Ação completou com sucesso
  → Toast efêmero (3-5s)

WARNING (amarelo/âmbar)
  Algo precisa atenção, não é erro
  → Banner persistente (até resolver)

DANGER (vermelho)
  Erro grave OU ação destrutiva
  → Modal bloqueante (se requer ação)
  → Banner persistente (se contextual)
  → NÃO toast (some antes de ler)
```

**Regra:** quanto mais grave, mais bloqueante.

---

## 6. Tom da mensagem

### 6.1 Princípios

- **Linguagem clara** — não código de erro
- **Acionável** — diz como corrigir
- **Empático** — não culpa o usuário
- **Conciso** — 1-2 frases
- **Em pt-BR** para usuário BR
- **Tom respeitoso** — usuário não é problema

### 6.2 Tabela de tom

| Situação | ❌ Errado | ✅ Correto |
|---|---|---|
| Senha fraca | "Senha inválida" | "Mínimo 8 caracteres com 1 número e 1 maiúscula" |
| Email duplicado | "Email já existe" | "Esse email já está cadastrado. Esqueceu a senha?" |
| Erro de rede | "Network error" | "Sem conexão. Verifique sua internet e tente novamente." |
| Erro 500 | "Internal server error" | "Tivemos um problema. Já estamos investigando. Tente novamente em alguns minutos." |
| Pagamento falhou | "Payment failed: code 4567" | "Pagamento não autorizado pelo banco. Verifique os dados ou use outro cartão." |
| Form vazio | "Required" | "Preencha esse campo" |
| Sessão expirada | "Token expired" | "Sua sessão expirou. Faça login novamente." |
| Sem permissão | "Forbidden 403" | "Você não tem permissão para acessar isso. Entre em contato com o admin." |

### 6.3 Erros em pt-BR

```
❌ "Validation failed"
✅ "Verifique os campos destacados"

❌ "Unauthorized"
✅ "Faça login para continuar"

❌ "Bad request"
✅ "Pedido inválido. Verifique os dados."

❌ "Network error: Failed to fetch"
✅ "Não foi possível conectar. Tente novamente."

❌ "Service unavailable"
✅ "Serviço temporariamente indisponível. Tente em alguns minutos."
```

---

## 7. Acessibilidade

### 7.1 Toast e banner

```jsx
// ✅ Anuncia para screen reader
<div role="status" aria-live="polite">
  Item salvo
</div>

// ✅ Erro grave anuncia interrompendo
<div role="alert" aria-live="assertive">
  Pagamento não autorizado
</div>
```

`role="status"` + `aria-live="polite"` → anuncia em pausa
`role="alert"` + `aria-live="assertive"` → anuncia imediatamente

### 7.2 Modal

```jsx
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
  aria-describedby="modal-description"
>
  <h2 id="modal-title">Excluir conta?</h2>
  <p id="modal-description">Esta ação é irreversível.</p>
  <button autoFocus>Cancelar</button>
  <button>Excluir</button>
</div>
```

- Focus trap dentro do modal (Tab cicla entre elementos)
- Esc fecha
- Foco volta para elemento que abriu modal ao fechar

### 7.3 Inline validation

```jsx
<input
  aria-invalid={!!error}
  aria-describedby={error ? 'field-error' : undefined}
/>
{error && (
  <p id="field-error" role="alert">
    {error}
  </p>
)}
```

### 7.4 Status badge

```jsx
// ✅ Texto + ícone (não só cor)
<span className="badge badge-warning">
  <ClockIcon aria-hidden="true" />
  Pendente
</span>
```

---

## 8. Anti-patterns com correção

### Anti-pattern 1: Toast para erro grave

```
❌ ERRADO:
toast.error('Pagamento falhou'); // some em 5s, usuário não percebe

✅ CORRETO:
- Modal bloqueante OU
- Banner persistente OU
- Página dedicada de erro com instruções
```

### Anti-pattern 2: Modal para confirmação trivial

```
❌ ERRADO:
"Tem certeza que quer favoritar este item?" [Sim] [Não]
(interrompe fluxo desnecessariamente)

✅ CORRETO:
Optimistic update + animação sutil (heart pop)
```

### Anti-pattern 3: Silently fail

```
❌ ERRADO:
async function save() {
  try {
    await api.save();
    // sem feedback
  } catch (e) {
    console.error(e);
    // sem feedback
  }
}

✅ CORRETO:
async function save() {
  try {
    await api.save();
    toast.success('Salvo');
  } catch (e) {
    toast.error('Não foi possível salvar', {
      action: { label: 'Tentar novamente', onClick: save }
    });
  }
}
```

### Anti-pattern 4: Mensagens só com cor

```html
<!-- ❌ ERRADO -->
<span style="color: red">Erro</span>
<span style="color: green">OK</span>

<!-- ✅ CORRETO -->
<span style="color: red"><XIcon /> Erro</span>
<span style="color: green"><CheckIcon /> OK</span>
```

### Anti-pattern 5: Toast empilhado em 10+

```
❌ ERRADO:
Usuário fez 10 ações rápidas, 10 toasts aparecem empilhados.

✅ CORRETO:
- Limite de 3 toasts visíveis simultaneamente
- Mais antigos saem para dar lugar aos novos
- OU consolidar ("3 itens salvos")
```

### Anti-pattern 6: "Sucesso" sem detalhe quando útil

```
❌ ERRADO:
toast.success('Sucesso'); // qual sucesso?

✅ CORRETO:
toast.success('Email enviado para joao@example.com');
toast.success('Pedido #1234 confirmado');
```

### Anti-pattern 7: "Erro" sem ação

```
❌ ERRADO:
toast.error('Erro'); // o que faço?

✅ CORRETO:
toast.error('Não foi possível salvar', {
  description: 'Sua sessão expirou',
  action: { label: 'Fazer login', onClick: redirectToLogin }
});
```

### Anti-pattern 8: Posições inconsistentes

```
❌ ERRADO:
Toast às vezes top-right, às vezes bottom-center, às vezes meio.

✅ CORRETO:
1 posição em todo app (geralmente bottom-right desktop, top mobile).
Documentar em design system.
```

---

## 9. Casos práticos por contexto

### 9.1 Formulário de checkout (Áugure)

```
Campo CPF inválido         → inline validation (on blur)
Campo cartão inválido      → inline + ícone bandeira
Submit clicked             → button disabled + spinner inline
Submit em processamento    → progress bar com steps
Pagamento aprovado         → page redirect para confirmação
Pagamento recusado         → modal explicando motivo + botão tentar
Cartão expirou             → banner amarelo persistente
```

### 9.2 SaaS dashboard

```
Salvou config              → toast success
Erro de save               → toast danger + retry
Item deletado              → toast com botão "Desfazer" (10s)
Filtro aplicado            → skeleton + count badge
Sessão expirando           → banner amarelo nos últimos 5 min
Sessão expirada            → modal com login redirect
Update disponível          → banner azul dismiss-able
Sem permissão              → page dedicada (não toast)
```

### 9.3 Mobile app

```
Pull to refresh             → spinner + haptic
Curtir post                 → optimistic + heart animation
Mensagem enviada            → check sutil ao lado da mensagem
Mensagem falhou             → ícone vermelho + tap para retry
Conexão perdida             → banner discreto offline mode
Conexão recuperada          → toast verde "Online"
Push notification           → banner sistema (não in-app)
```

---

## 10. Checklist de validação

```
TIPOS:
□ Toda phase tem mapeamento ação → feedback?
□ Toast usado só para não-crítico?
□ Modal usado só para confirmar destrutivo?
□ Banner usado para persistente contextual?
□ Inline validation em todos os campos de form?

TOM:
□ Mensagens em pt-BR?
□ Mensagens são acionáveis (não só relatam)?
□ Tom respeitoso (não acusatório)?
□ Erros têm próxima ação clara?

ACESSIBILIDADE:
□ Status comunicado por cor + ícone + texto?
□ aria-live em toasts?
□ role="alert" em erros graves?
□ Modal tem focus trap + Esc?
□ Inline validation tem aria-invalid + aria-describedby?

TIMING:
□ Toast efêmero 3-5s?
□ Banner persistente até resolver?
□ Modal não dismiss automaticamente?

CONSISTÊNCIA:
□ Posição de toast consistente em toda app?
□ Variantes (success/warning/danger/info) consistentes?
□ Padrões de cor seguem `quality/color-system`?
```

---

## 11. Como integra com outras skills

### 11.1 → `ux-advanced/loading-states`
Loading e feedback são sequenciais (loading → success/error feedback).

### 11.2 → `ux-advanced/empty-states-polish`
Empty é tipo de feedback (ausência de dados).

### 11.3 → `quality/error-ux-patterns`
Mensagens de erro detalhadas vão lá.

### 11.4 → `quality/color-system`
Cores de feedback (success/warning/danger/info) vêm dos tokens.

### 11.5 → `quality/accessibility-pro`
ARIA roles e live regions cobertos.

### 11.6 → PLAN.md de phase

```markdown
## Phase 4 — Form de cadastro

### Skills Consultadas
- `ux-advanced/feedback-patterns` — inline validation + toast success
- `ux-advanced/loading-states` — spinner no submit
- `quality/error-ux-patterns` — mensagens de erro
- `br/brazilian-forms` — máscaras CPF/CEP
```

---

## 12. Erros comuns

### Erro 1: Pular feedback "porque é rápido"
Mesmo ação <500ms precisa de feedback visual. Mudança de cor, animação sutil.

### Erro 2: Sempre toast
Toast vira muleta. Para erros graves, modal/banner. Para trivial, animação inline.

### Erro 3: Mensagens em inglês para usuário BR
Mesmo que código tenha "validation_failed", UI mostra "Verifique os campos".

### Erro 4: Validação on every keystroke
Frustrante. Sempre on blur ou no submit.

### Erro 5: Pular acessibilidade
Toast invisível para screen reader = usuário cego não sabe que ação completou.

---

## 13. Bibliotecas

### React
- **sonner** — toasts modernos
- **react-hot-toast** — alternativa
- **react-aria** — acessibilidade
- **headlessui** (modais)

### Angular/Ionic
- **@ionic/angular IonToastController** — toasts nativos
- **@ionic/angular IonAlertController** — modais de confirmação
- **@ngrx/component-store** — gerenciar estado de feedback
- **@angular/cdk overlay** — overlays customizados

---

## 14. Referências

- **NN/g — Toast/Snackbar guidelines**
- **Material Design — Snackbars and toasts**
- **WCAG 2.1 — Status Messages (success criterion 4.1.3)**
- **A11y Project — alerts and toasts**

---

**Última atualização:** v0.7.1 (densificação batch 2)
**Densidade:** 14 seções, 8 tipos de feedback com snippets, matriz de decisão 20+ contextos, anti-patterns com correção, checklist de 16 itens
