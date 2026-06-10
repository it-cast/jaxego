---
name: trust-safety-ux
description: Padrões de UX para transmitir segurança e confiança no {PROJETO}. Cobre visualização de escrow, badges de verificação, indicadores de segurança no pagamento e exibição de avaliações. A confiança é o diferencial competitivo do {PROJETO}.
type: ux-advanced
project: global-brasil-conecta
---

# Skill: Trust & Safety UX

> "Seu dinheiro está seguro" — essa promessa precisa ser visível em cada tela.

---

## 1. Quando usar

- Qualquer tela de pagamento ou checkout
- Perfil do profissional (badges, avaliações)
- Tela de acompanhamento de serviço (escrow status)
- Header de proposta formal

---

## 2. Escrow visualization

O escrow tem 3 estados visuais. **Nunca usar vermelho para dinheiro retido** — implica problema.

| Estado | Icon | Cor | Token | Copy |
|--------|------|-----|-------|------|
| `retained` | `lock-closed-outline` | Âmbar | `--app-feedback-warning` | "Seu dinheiro está protegido" |
| `pending_release` | `time-outline` | Info azul | `--app-primary-500` | "Aguardando sua confirmação" |
| `released` | `checkmark-circle-outline` | Verde | `--app-success` | "Pagamento liberado ao profissional" |

```scss
.escrow-card {
  display: flex;
  align-items: center;
  gap: var(--sp-md);
  padding: var(--sp-md);
  border-radius: var(--radius-md);
  border: 1px solid;

  &.escrow--retained {
    background: var(--app-feedback-warning-bg);
    border-color: var(--app-feedback-warning);

    .escrow-icon { color: var(--app-feedback-warning); }
  }

  &.escrow--pending_release {
    background: rgba(21, 101, 192, 0.08);
    border-color: var(--app-primary-500);

    .escrow-icon { color: var(--app-primary-500); }
  }

  &.escrow--released {
    background: var(--app-feedback-success-bg);
    border-color: var(--app-success);

    .escrow-icon { color: var(--app-success); }
  }

  // Pulso sutil no estado retido (dinheiro ativo)
  &.escrow--retained .escrow-icon {
    animation: escrow-pulse 3s ease-in-out infinite;

    @media (prefers-reduced-motion: reduce) {
      animation: none;
    }
  }
}

.escrow-amount {
  font-size: var(--type-h3);
  font-weight: 700;
  color: var(--app-text-primary);
}

.escrow-label {
  font-size: var(--type-caption);
  color: var(--app-text-secondary);
}

@keyframes escrow-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}
```

---

## 3. Badges de verificação do profissional

```scss
.pro-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-full);

  ion-icon { font-size: 12px; }

  &.badge--verified {
    background: rgba(21, 101, 192, 0.1);
    color: var(--app-primary-700);
    // "Verificado" — identidade confirmada
  }

  &.badge--top_rated {
    background: rgba(255, 152, 0, 0.12);
    color: var(--app-feedback-warning);
    // "Top Avaliado" — nota > 4.8 com 10+ reviews
  }

  &.badge--fast {
    background: var(--app-feedback-success-bg);
    color: var(--app-success);
    // "Responde rápido" — tempo médio < 2h
  }
}
```

**Regras de exibição:**
- Máximo 2 badges por profissional no card de lista
- Tooltip obrigatório ao tap: explicar o que o badge significa
- Badge "Verificado" sempre primeiro (hierarquia de confiança)

---

## 4. Indicadores de segurança no pagamento

```html
<!-- Antes do formulário de pagamento -->
<div class="security-banner">
  <ion-icon name="lock-closed" class="security-icon"></ion-icon>
  <div class="security-text">
    <strong>Pagamento 100% seguro</strong>
    <span>Processado via {gateway-pagamento} · Criptografia SSL</span>
  </div>
</div>

<!-- Fee breakdown (obrigatório antes de confirmar) -->
<div class="fee-breakdown">
  <div class="fee-row">
    <span>Serviço</span>
    <span>R$ {{ servicePrice | number:'1.2-2' }}</span>
  </div>
  <div class="fee-row fee-row--platform">
    <span>Taxa da plataforma (12%)</span>
    <span>R$ {{ platformFee | number:'1.2-2' }}</span>
  </div>
  <div class="fee-row fee-row--total">
    <strong>Total</strong>
    <strong>R$ {{ total | number:'1.2-2' }}</strong>
  </div>
</div>
```

```scss
.security-banner {
  display: flex;
  align-items: center;
  gap: var(--sp-sm);
  padding: var(--sp-sm) var(--sp-md);
  background: var(--app-feedback-success-bg);
  border-radius: var(--radius-md);
  margin-bottom: var(--sp-md);

  .security-icon {
    font-size: 20px;
    color: var(--app-success);
    flex-shrink: 0;
  }

  strong { font-size: 13px; color: var(--app-text-primary); display: block; }
  span   { font-size: 12px; color: var(--app-text-secondary); }
}

.fee-breakdown {
  background: var(--app-surface-page);
  border-radius: var(--radius-md);
  padding: var(--sp-md);
  margin-bottom: var(--sp-md);
}

.fee-row {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: var(--app-text-secondary);
  padding: var(--sp-xs) 0;

  &--platform { color: var(--app-text-tertiary); font-size: 13px; }

  &--total {
    border-top: 1px solid var(--app-border-subtle);
    margin-top: var(--sp-xs);
    padding-top: var(--sp-sm);
    color: var(--app-text-primary);
    font-size: 16px;
  }
}
```

---

## 5. Rating display

```html
<!-- Rating compact (em cards de lista) -->
<span class="rating-compact">
  <ion-icon name="star" class="star-icon"></ion-icon>
  {{ rating | number:'1.1-1' }}
  <span class="review-count">({{ count }})</span>
</span>

<!-- Rating display (em perfil completo) -->
<div class="rating-full">
  @for (star of [1,2,3,4,5]; track star) {
    <ion-icon
      [name]="star <= Math.round(rating) ? 'star' : 'star-outline'"
      class="star-icon">
    </ion-icon>
  }
  <span class="rating-value">{{ rating | number:'1.1-1' }}</span>
  <span class="review-count">{{ count }} avaliações</span>
</div>
```

```scss
.star-icon { color: var(--app-rating); font-size: 14px; }

.rating-compact {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 13px;
  font-weight: 600;
  color: var(--app-text-primary);

  .review-count {
    color: var(--app-text-tertiary);
    font-weight: 400;
    font-size: 12px;
  }
}
```

---

## 6. Anti-patterns

- ❌ Nunca usar vermelho para dinheiro retido em escrow (indica problema — use âmbar)
- ❌ Nunca esconder a taxa de 12% — sempre mostrar breakdown completo
- ❌ Nunca mostrar saldo de escrow sem contexto do serviço
- ❌ Nunca confundir "Em andamento" com "Pago" — status diferentes, cores diferentes
- ❌ Nunca mostrar o preço total sem a taxa antes do pagamento (viola LGPD + trust)
- ❌ Nunca usar estrelas sem o número de reviews (1 review 5★ ≠ 100 reviews 5★)
