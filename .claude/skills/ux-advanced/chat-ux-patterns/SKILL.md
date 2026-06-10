---
name: chat-ux-patterns
description: Padrões de UX para chat em tempo real no {PROJETO}. Cobre bubbles, tipos de mensagem, proposal card, input bar, skeleton e estado offline. Use em qualquer componente de chat (quote-chat, service-chat, pro-chat).
type: ux-advanced
project: global-brasil-conecta
---

# Skill: Chat UX Patterns

> Chat é o core do {PROJETO}. Qualidade do chat = qualidade da proposta = conversão.

---

## 1. Quando usar

- Qualquer componente em `apps/mobile/src/app/client/pages/chat/`
- Qualquer componente em `apps/mobile/src/app/professional/pages/pro-chat/`
- Componentes de mensagem compartilhados (`shared/components/message-*/`)
- Tela de proposta formal dentro do chat

---

## 2. Alinhamento de bubbles

```
REGRA: sender = direita, receiver = esquerda
- Cliente enviando → bubble direita (azul: --app-primary-700)
- Profissional enviando → bubble direita (laranja: --app-energy-500)
- Sistema → centrado, sem bubble (texto muted, itálico)
```

```scss
.bubble {
  max-width: 75%;
  border-radius: 18px;
  padding: var(--sp-sm) var(--sp-md);

  &.bubble--sent {
    align-self: flex-end;
    background: var(--app-primary-700);
    color: var(--app-text-inverse);
    border-bottom-right-radius: 4px;
  }

  &.bubble--received {
    align-self: flex-start;
    background: var(--app-surface-card);
    color: var(--app-text-primary);
    border: 1px solid var(--app-border-subtle);
    border-bottom-left-radius: 4px;
  }

  &.bubble--pro-sent {
    // Profissional enviando — usa laranja se no pro-chat
    background: var(--app-energy-500);
  }
}

.bubble-time {
  font-size: 10px;
  color: rgba(255,255,255,0.6);
  margin-top: 2px;
  text-align: right;

  .bubble--received & {
    color: var(--app-text-tertiary);
  }
}

// Agrupar timestamps — mostrar só a cada 5 minutos
.time-separator {
  text-align: center;
  font-size: 11px;
  color: var(--app-text-tertiary);
  margin: var(--sp-md) 0 var(--sp-sm);
}
```

---

## 3. Tipos de mensagem

| type | Renderização |
|------|-------------|
| `text` | Bubble normal |
| `image` | Thumbnail 200×200, tap para fullscreen |
| `proposal` | Card especial (seção 4) |
| `system` | Texto centrado, muted, sem bubble |
| `delivery_photo` | Grid de fotos 2 colunas com legenda |

```html
<!-- system message -->
<div class="system-message">
  <span>{{ message.content }}</span>
</div>
```

```scss
.system-message {
  text-align: center;
  font-size: 12px;
  font-style: italic;
  color: var(--app-text-tertiary);
  padding: var(--sp-xs) var(--sp-md);
  margin: var(--sp-sm) 0;
}
```

---

## 4. Proposal Card (componente crítico)

O card de proposta é embedded no chat stream. Tem 5 estados.

```scss
.proposal-card {
  border-radius: var(--radius-lg);
  border: 2px solid var(--app-border-subtle);
  overflow: hidden;
  margin: var(--sp-sm) 0;
  background: var(--app-surface-card);
  box-shadow: var(--shadow-card);

  // Estados
  &.proposal--pending  { border-color: var(--app-border-subtle); }
  &.proposal--accepted { border-color: var(--app-success); }
  &.proposal--rejected { border-color: var(--app-feedback-error-bg); opacity: 0.7; }
  &.proposal--revised  { border-color: var(--app-energy-500); }
  &.proposal--expired  { border-color: var(--app-border-default); opacity: 0.5; }
}

.proposal-header {
  background: var(--app-gradient-cta);
  padding: var(--sp-md);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.proposal-price {
  font-size: var(--type-h2);
  font-weight: 700;
  color: var(--app-text-inverse);
}

.proposal-body {
  padding: var(--sp-md);
}

.proposal-actions {
  display: flex;
  gap: var(--sp-sm);
  padding: var(--sp-sm) var(--sp-md);
  border-top: 1px solid var(--app-border-subtle);

  ion-button { flex: 1; }
}
```

**Ações do proposal:**
- "Aceitar" → IonAlert de confirmação → POST `/proposals/{id}/accept`
- "Pedir ajuste" → IonModal com campo de texto → PUT `/proposals/{id}` (status: revised)
- "Recusar" → IonAlert de confirmação → PUT `/proposals/{id}` (status: rejected)

---

## 5. Chat input bar

```scss
.chat-input-bar {
  display: flex;
  align-items: flex-end;
  gap: var(--sp-sm);
  padding: var(--sp-sm) var(--sp-md);
  padding-bottom: calc(var(--sp-sm) + env(safe-area-inset-bottom));
  background: var(--app-surface-card);
  border-top: 1px solid var(--app-border-subtle);
  box-shadow: 0 -2px 8px rgba(0,0,0,0.06);
}

.chat-input {
  flex: 1;
  --background: var(--app-surface-page);
  --border-radius: var(--radius-lg);
  --padding-start: var(--sp-md);
  --padding-end: var(--sp-sm);
  min-height: 44px;
  max-height: 120px;
}

.send-btn {
  width: 44px;
  height: 44px;
  --border-radius: 50%;
  --background: var(--app-gradient-cta);
  --background-disabled: var(--app-border-subtle);
  flex-shrink: 0;
}

.attach-btn {
  width: 44px;
  height: 44px;
  --border-radius: 50%;
  --background: transparent;
  --color: var(--app-text-tertiary);
  flex-shrink: 0;
}
```

**Keyboard avoidance no Ionic:**
```typescript
// No ngOnInit — Ionic gerencia automaticamente com IonContent
// NÃO usar window.scrollTo ou document.scrollTop manualmente
// NÃO usar @ViewChild + scrollToBottom fora do ionViewWillEnter
ionViewWillEnter() {
  // Scroll para última mensagem
  this.content.scrollToBottom(0);
}
```

---

## 6. Skeleton loader (histórico de mensagens)

```html
<!-- 3 fake bubbles alternando lados -->
<div class="chat-skeleton" *ngIf="loading()">
  <div class="skel-bubble skel-received">
    <ion-skeleton-text [animated]="true" style="width: 55%; height: 40px; border-radius: 18px;"></ion-skeleton-text>
  </div>
  <div class="skel-bubble skel-sent">
    <ion-skeleton-text [animated]="true" style="width: 40%; height: 32px; border-radius: 18px;"></ion-skeleton-text>
  </div>
  <div class="skel-bubble skel-received">
    <ion-skeleton-text [animated]="true" style="width: 65%; height: 56px; border-radius: 18px;"></ion-skeleton-text>
  </div>
</div>
```

---

## 7. Typing indicator

```scss
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: var(--sp-sm) var(--sp-md);
  align-self: flex-start;

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--app-text-tertiary);
    animation: typing-bounce 1.2s ease-in-out infinite;

    &:nth-child(2) { animation-delay: 0.2s; }
    &:nth-child(3) { animation-delay: 0.4s; }
  }

  @media (prefers-reduced-motion: reduce) {
    .dot { animation: none; opacity: 0.5; }
  }
}

@keyframes typing-bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-8px); }
}
```

---

## 8. Anti-patterns

- ❌ Nunca mostrar mensagens do profissional no lado direito quando é o cliente vendo
- ❌ Nunca usar azul para bubbles do profissional (azul = cliente)
- ❌ Nunca mostrar timestamp em CADA mensagem — agrupar por blocos de 5 min
- ❌ Nunca fazer scroll automático quando usuário está lendo histórico acima
- ❌ Nunca renderizar proposal card como bubble normal
- ❌ Nunca enviar mensagem com Enter em mobile — Enter = nova linha
