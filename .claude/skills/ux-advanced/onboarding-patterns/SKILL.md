---
name: onboarding-patterns
description: Padrões de onboarding e first-run experience no {PROJETO}. Cobre role selection (cliente vs profissional), progressive permissions, empty first-run states, coachmarks e splash screens. Use no fluxo de cadastro e primeiros acessos.
type: ux-advanced
project: global-brasil-conecta
---

# Skill: Onboarding Patterns

> A primeira impressão define o LTV. Um onboarding ruim = churn na primeira semana.

---

## 1. Quando usar

- `apps/mobile/src/app/shared/pages/auth/` (register, login)
- Primeira vez que o usuário entra em cada área
- Empty states no primeiro uso (zero quotes, zero services)
- Pedidos de permissão (câmera, notificações)

---

## 2. Role selection (Cliente vs Profissional)

Essa é a primeira decisão do usuário. Deve ser visual, clara e sem ambiguidade.

```html
<div class="role-selection">
  <h2 class="role-title">Como você quer usar o {PROJETO}?</h2>
  <p class="role-subtitle">Você pode mudar isso depois</p>

  <div class="role-cards">
    <!-- Card Cliente -->
    <button class="role-card" [class.role-card--selected]="role() === 'client'"
            (click)="selectRole('client')" type="button">
      <div class="role-icon-wrap role-icon-wrap--client">
        <ion-icon name="person-outline"></ion-icon>
      </div>
      <h3>Sou Cliente</h3>
      <p>Preciso contratar serviços</p>
      <ul class="role-benefits">
        <li><ion-icon name="checkmark"></ion-icon> Encontre profissionais verificados</li>
        <li><ion-icon name="checkmark"></ion-icon> Pagamento protegido</li>
        <li><ion-icon name="checkmark"></ion-icon> Compare propostas</li>
      </ul>
    </button>

    <!-- Card Profissional -->
    <button class="role-card" [class.role-card--selected]="role() === 'professional'"
            (click)="selectRole('professional')" type="button">
      <div class="role-icon-wrap role-icon-wrap--pro">
        <ion-icon name="briefcase-outline"></ion-icon>
      </div>
      <h3>Sou Profissional</h3>
      <p>Quero oferecer meus serviços</p>
      <ul class="role-benefits">
        <li><ion-icon name="checkmark"></ion-icon> Receba pedidos de clientes</li>
        <li><ion-icon name="checkmark"></ion-icon> Pagamento garantido</li>
        <li><ion-icon name="checkmark"></ion-icon> Gerencie sua agenda</li>
      </ul>
    </button>
  </div>
</div>
```

```scss
.role-cards {
  display: flex;
  flex-direction: column;
  gap: var(--sp-md);
}

.role-card {
  width: 100%;
  padding: var(--sp-lg);
  border-radius: var(--radius-lg);
  border: 2px solid var(--app-border-subtle);
  background: var(--app-surface-card);
  text-align: left;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-default);

  &--selected {
    border-color: var(--app-primary-700);
    background: rgba(21, 101, 192, 0.04);
    box-shadow: var(--shadow-card);
  }
}

.role-icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--sp-sm);

  ion-icon { font-size: 24px; }

  &--client {
    background: rgba(21, 101, 192, 0.12);
    color: var(--app-primary-700);
  }

  &--pro {
    background: rgba(255, 87, 34, 0.12);
    color: var(--app-energy-600);
  }
}

.role-benefits {
  list-style: none;
  padding: 0;
  margin: var(--sp-sm) 0 0;

  li {
    display: flex;
    align-items: center;
    gap: var(--sp-xs);
    font-size: var(--type-caption);
    color: var(--app-text-secondary);
    padding: 2px 0;

    ion-icon { color: var(--app-success); font-size: 14px; }
  }
}
```

---

## 3. Progressive permissions (câmera, notificações)

**Regra de ouro:** nunca pedir permissão sem contexto. Sempre explicar POR QUE antes de chamar o prompt do sistema.

```html
<!-- Permission explanation modal — mostrar ANTES do sistema pedir -->
<div class="permission-explain">
  <div class="permission-icon">
    <ion-icon name="notifications-outline"></ion-icon>
  </div>
  <h3>Ative as notificações</h3>
  <p>Saiba quando um profissional responde seu orçamento ou quando seu serviço for concluído.</p>
  <div class="permission-actions">
    <ion-button expand="block" (click)="requestNotifications()">
      Ativar notificações
    </ion-button>
    <ion-button expand="block" fill="clear" (click)="skipForNow()">
      Agora não
    </ion-button>
  </div>
</div>
```

```typescript
// Pedir permissão SOMENTE no momento relevante — nunca na entrada
async requestCameraPermission(): Promise<void> {
  // Verificar antes de pedir
  const current = await Camera.checkPermissions();
  if (current.photos === 'granted') return;

  // Mostrar explicação customizada ANTES do prompt do sistema
  await this.showPermissionExplain('câmera', 'enviar fotos do serviço');

  const result = await Camera.requestPermissions({ permissions: ['photos', 'camera'] });
  if (result.photos === 'denied') {
    // Redirecionar para configurações do sistema
    await this.showSettingsGuide();
  }
}
```

**Timing de permissões:**
| Permissão | Quando pedir |
|-----------|-------------|
| Notificações | Após 1ª proposta recebida ou após cadastro completo |
| Câmera | Ao clicar em "Enviar foto" pela 1ª vez |
| Galeria | Ao clicar em "Adicionar portfolio" pela 1ª vez |
| Localização | Nunca — usar cidade digitada pelo usuário |

---

## 4. Empty first-run states (com valor)

O empty state no primeiro uso deve ser uma OPORTUNIDADE, não um vazio.

```html
<!-- Empty state para Cliente sem orçamentos -->
<div class="first-run-state">
  <div class="first-run-illustration">
    <ion-icon name="search-circle-outline"></ion-icon>
  </div>
  <h3>Encontre o profissional certo</h3>
  <p>Descreva o que você precisa e receba propostas de profissionais verificados.</p>

  <div class="first-run-steps">
    <div class="step">
      <span class="step-num">1</span>
      <span>Descreva o serviço</span>
    </div>
    <div class="step">
      <span class="step-num">2</span>
      <span>Compare propostas</span>
    </div>
    <div class="step">
      <span class="step-num">3</span>
      <span>Contrate com segurança</span>
    </div>
  </div>

  <ion-button expand="block" class="first-run-cta" routerLink="/client/search">
    <ion-icon slot="start" name="search-outline"></ion-icon>
    Solicitar meu primeiro orçamento
  </ion-button>
</div>
```

```scss
.first-run-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--sp-xl) var(--sp-lg);
  gap: var(--sp-md);
}

.first-run-illustration ion-icon {
  font-size: 80px;
  color: var(--app-primary-200);
}

.first-run-steps {
  display: flex;
  flex-direction: column;
  gap: var(--sp-sm);
  width: 100%;
  text-align: left;
  background: var(--app-surface-page);
  border-radius: var(--radius-md);
  padding: var(--sp-md);
}

.step {
  display: flex;
  align-items: center;
  gap: var(--sp-md);
  font-size: 14px;
  color: var(--app-text-secondary);
}

.step-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--app-gradient-cta);
  color: var(--app-text-inverse);
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.first-run-cta {
  --background: var(--app-gradient-cta);
  margin-top: var(--sp-md);
}
```

---

## 5. Splash / loading inicial

```typescript
// No app.component.ts — ocultar splash nativo após app estar pronto
async ngOnInit(): Promise<void> {
  await this.authService.initializeSession();
  await SplashScreen.hide({ fadeOutDuration: 300 });
}
```

---

## 6. Anti-patterns

- ❌ Nunca pedir notificações no primeiro segundo de uso (rate de aceitação cai de 60% para 15%)
- ❌ Nunca mostrar empty state sem CTA — vazio sem ação = usuário frustrado
- ❌ Nunca role selection ambígua — o usuário deve entender imediatamente qual escolher
- ❌ Nunca 4+ passos de onboarding — máximo 3 (idealmente 2)
- ❌ Nunca esconder o "Pular" — forçar onboarding = abandono
- ❌ Nunca pedir localização — violar expectativa sem necessidade real
- ❌ Nunca assumir câmera permitida antes de checar
