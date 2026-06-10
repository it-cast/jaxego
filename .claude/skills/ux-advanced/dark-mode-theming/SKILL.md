---
name: dark-mode-theming
description: Padrões de dark mode no {PROJETO} usando tokens CSS. Cobre override de tokens, Ionic dark mode, toggle manual, persistência com Capacitor Preferences, e checklist de teste. Use ao implementar alternância de tema ou tela que precisa suportar dark mode.
type: ux-advanced
project: global-brasil-conecta
---

# Skill: Dark Mode Theming

> Dark mode não é inverter as cores. É redesenhar a hierarquia visual com luz reduzida.

---

## 1. Quando usar

- Implementar toggle de dark/light no perfil do usuário
- Qualquer nova tela que precisa respeitar o tema do sistema
- Corrigir elementos que "quebram" em dark mode (branco sobre branco, etc.)
- Fase 2+ — dark mode não é bloqueante para MVP

---

## 2. Arquitetura de tokens para dark mode

O {PROJETO} usa 3 camadas de tokens. Dark mode é feito na camada alias, não na literal.

```scss
// variables.scss — camada light (padrão)
:root {
  // Alias tokens — mapeiam para literais
  --app-surface-page:    var(--app-gray-50);
  --app-surface-card:    var(--app-white);
  --app-text-primary:    var(--app-gray-900);
  --app-text-secondary:  var(--app-gray-600);
  --app-text-tertiary:   var(--app-gray-400);
  --app-border-subtle:   var(--app-gray-200);
  --app-border-default:  var(--app-gray-300);
}

// Camada dark — sobrescreve apenas os alias tokens
:root.dark,
.dark {
  --app-surface-page:    var(--app-gray-950);
  --app-surface-card:    var(--app-gray-900);
  --app-text-primary:    var(--app-gray-50);
  --app-text-secondary:  var(--app-gray-400);
  --app-text-tertiary:   var(--app-gray-600);
  --app-border-subtle:   var(--app-gray-800);
  --app-border-default:  var(--app-gray-700);
}
```

**Tokens literais dark (a adicionar em variables.scss):**
```scss
:root {
  --app-gray-950: #0a0a0b;
  // Já existem: gray-900, gray-800, etc.
}
```

---

## 3. Ionic dark mode

O Ionic tem seu próprio sistema de dark. Deve ser sincronizado com nossos tokens.

```scss
// variables.scss — seção Ionic dark
:root.dark {
  // Ionic background/text
  --ion-background-color: var(--app-surface-page);
  --ion-text-color: var(--app-text-primary);

  // Ionic item/card backgrounds
  --ion-item-background: var(--app-surface-card);
  --ion-card-background: var(--app-surface-card);

  // Toolbars
  --ion-toolbar-background: var(--app-surface-card);
  --ion-toolbar-color: var(--app-text-primary);

  // Tab bar
  --ion-tab-bar-background: var(--app-surface-card);
  --ion-tab-bar-color: var(--app-text-tertiary);
  --ion-tab-bar-color-selected: var(--app-primary-400); // mais claro no dark

  // Borders
  --ion-border-color: var(--app-border-subtle);
}
```

---

## 4. Toggle manual + persistência

```typescript
// theme.service.ts
@Injectable({ providedIn: 'root' })
export class ThemeService {
  readonly isDark = signal<boolean>(false);

  async init(): Promise<void> {
    // Ler preferência salva ou usar preferência do sistema
    const saved = await Preferences.get({ key: 'theme' });
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const dark = saved.value ? saved.value === 'dark' : prefersDark;
    this.applyTheme(dark);
  }

  async toggle(): Promise<void> {
    const newDark = !this.isDark();
    this.applyTheme(newDark);
    await Preferences.set({ key: 'theme', value: newDark ? 'dark' : 'light' });
  }

  private applyTheme(dark: boolean): void {
    this.isDark.set(dark);
    document.documentElement.classList.toggle('dark', dark);
  }
}
```

```html
<!-- Toggle no perfil -->
<ion-item>
  <ion-icon slot="start" name="moon-outline"></ion-icon>
  <ion-label>Modo escuro</ion-label>
  <ion-toggle
    slot="end"
    [checked]="themeService.isDark()"
    (ionChange)="themeService.toggle()">
  </ion-toggle>
</ion-item>
```

---

## 5. Armadilhas comuns do dark mode

### Gradientes
```scss
// ❌ Gradiente hardcoded fica estranho no dark
background: linear-gradient(135deg, #1565C0, #0D47A1);

// ✅ Usar token que pode ser sobrescrito
background: var(--app-gradient-header);

// dark override:
:root.dark {
  --app-gradient-header: linear-gradient(135deg, #0D47A1, #0a3080);
}
```

### Imagens e ícones
```scss
// Imagens com fundo branco ficam ruins no dark
.category-icon {
  background: var(--app-surface-card);
  // ✅ usa token — no dark vira cinza escuro automaticamente
}

// ❌ Nunca
.category-icon {
  background: #fff; // quebra no dark
}
```

### Box shadows
```scss
// Sombras não funcionam bem no dark (mesmos valores)
:root {
  --shadow-card: 0 2px 8px rgba(0, 0, 0, 0.08);
}

:root.dark {
  // Aumentar opacidade e adicionar border sutil
  --shadow-card: 0 2px 8px rgba(0, 0, 0, 0.4);
  // Ou substituir shadow por border:
  --shadow-card: none; // e adicionar border: 1px solid var(--app-border-subtle)
}
```

---

## 6. Checklist de teste dark mode

Antes de marcar como feito, testar:
- [ ] Texto legível em todos os fundos (contraste ≥ 4.5:1)
- [ ] Gradientes do header e CTA visíveis
- [ ] Tab bar distingue ativo do inativo
- [ ] Cards não se confundem com o fundo da página
- [ ] Campos de formulário têm borda visível
- [ ] Ícones brancos em fundo escuro (e não branco em branco)
- [ ] Imagens de portfolio com fundo correto
- [ ] Toast/Alert legíveis
- [ ] Skeleton loader visível (não some no escuro)

---

## 7. Anti-patterns

- ❌ Nunca inverter todas as cores automaticamente (`filter: invert(1)`) — destrói imagens
- ❌ Nunca hardcodar `#fff` ou `#000` em componentes — sempre token
- ❌ Nunca usar `background: white` — usar `var(--app-surface-card)`
- ❌ Nunca testar dark mode só visualmente — testar contraste com ferramenta
- ❌ Nunca esquecer de salvar a preferência — rebotar o app não pode perder o tema
- ❌ Nunca usar `localStorage` para salvar — usar `Capacitor Preferences`
