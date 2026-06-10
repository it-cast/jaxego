---
name: ui-input-rich-patterns
description: "Padrões de inputs ricos e visuais para web/mobile: color picker que exibe a cor (não só hex), date picker com calendário visual, time picker, date range picker, autocomplete com imagem, tag/chip input, rich text editor, file preview rico, number input com slider, rating input com estrelas. Todas integradas com Angular Material 19 + Ionic 8 + validação, acessibilidade, mobile-first. Use em qualquer formulário que tenha campo visual (cor, data, hora, arquivo, tag) ou input que se beneficiaria de preview visual. Triggers: color picker, date picker, calendário, datepicker, time picker, cor visual, autocomplete, tag input, chip, rating, stars, rich text, editor, formulário visual."
---

# UI Input Rich Patterns

**Mandato:** Campos de input que têm representação visual natural (cor, data, arquivo) NÃO devem mostrar só texto (`#1565C0`, `2026-04-18`). Devem mostrar a **coisa real** — cor colorida, calendário visual, thumbnail. Isso reduz erro de usuário e comunica melhor.

---

## 1. Princípio central

**Toda primitiva visual merece preview visual.**

| Tipo de dado | ❌ Input textual | ✅ Input rico |
|---|---|---|
| Cor | `#1565C0` | Quadrado colorido + picker |
| Data | `2026-04-18` | Calendário visual |
| Hora | `14:30` | Roleta de hora ou timeline |
| Range de datas | `2026-04-18 → 2026-04-30` | Calendário range |
| Arquivo imagem | `avatar.png` | Thumbnail |
| Avaliação | `4` | ⭐⭐⭐⭐☆ |
| Percentual | `75` | Slider + número |
| Categorias (múltiplas) | "cozinha, reforma" | Chips |
| Pessoa (autocomplete) | Texto cru | Item com avatar |

---

## 2. Color Picker

### 2.1 Angular Material + ngx-color-picker

**Instalação:**
```bash
npm install ngx-color-picker
```

**Component:**
```typescript
import { ColorPickerModule } from 'ngx-color-picker';

@Component({
  selector: 'app-color-input',
  standalone: true,
  imports: [ColorPickerModule, FormsModule, MatFormFieldModule, MatInputModule],
  template: `
    <mat-form-field appearance="outline" class="color-field">
      <mat-label>Cor primária</mat-label>
      
      <!-- Preview da cor ao lado -->
      <div 
        matPrefix 
        class="color-preview"
        [style.background]="color"
        [colorPicker]="color"
        (colorPickerChange)="color = $event"
        [cpOutputFormat]="'hex'"
        [cpAlphaChannel]="'disabled'"
        [cpPresetColors]="presetColors"
        [cpPresetLabel]="'Paleta {PROJETO}'"
        aria-label="Abrir seletor de cor"
        tabindex="0">
      </div>
      
      <!-- Input text ao lado -->
      <input 
        matInput 
        [(ngModel)]="color"
        placeholder="#1565C0"
        pattern="^#[0-9A-Fa-f]{6}$"
        [maxlength]="7"
      />
      
      <mat-hint>Clique no quadrado para abrir o seletor</mat-hint>
    </mat-form-field>
  `,
  styles: [`
    .color-preview {
      width: 32px;
      height: 32px;
      border-radius: var(--radius-sm);
      border: 2px solid var(--color-border-default);
      margin-right: var(--space-3);
      cursor: pointer;
      box-shadow: inset 0 0 0 1px rgba(0,0,0,0.1);
      transition: transform var(--motion-fast) var(--ease-out);
    }
    .color-preview:hover {
      transform: scale(1.08);
    }
    .color-preview:focus-visible {
      outline: 3px solid var(--color-primary);
      outline-offset: 2px;
    }
  `]
})
export class ColorInputComponent {
  color = '#1565C0';
  
  // Paleta {PROJETO} pré-definida (sempre mostrar cores do projeto primeiro)
  presetColors = [
    '#1565C0', // primary
    '#00BCD4', // accent
    '#FF6D00', // energy
    '#00C853', // success
    '#FFD600', // warning
    '#FF1744', // error
  ];
}

// Skills aplicadas: ui-input-rich-patterns, design-tokens-system
```

### 2.2 Ionic (mobile) — color input nativo

```html
<ion-item>
  <ion-label position="stacked">Cor de destaque</ion-label>
  <ion-input 
    type="color" 
    [(ngModel)]="color"
    aria-label="Selecione a cor de destaque">
  </ion-input>
  <!-- iOS e Android renderizam picker nativo -->
</ion-item>
```

**Ou se quer controle total em mobile:**
```html
<ion-item button (click)="openColorModal()">
  <div slot="start" class="color-swatch" [style.background]="color"></div>
  <ion-label>
    <h3>Cor</h3>
    <p>{{ color }}</p>
  </ion-label>
</ion-item>

<!-- Modal customizado com grid de cores -->
<ion-modal [isOpen]="showColorModal">
  <ng-template>
    <ion-content class="ion-padding">
      <h2>Escolha uma cor</h2>
      <div class="color-grid">
        <button 
          *ngFor="let c of presetColors"
          class="color-option"
          [style.background]="c"
          [class.selected]="color === c"
          (click)="selectColor(c)"
          [attr.aria-label]="'Cor ' + c">
        </button>
      </div>
    </ion-content>
  </ng-template>
</ion-modal>
```

### 2.3 Regras de acessibilidade color picker

- Contraste: adicione **mini ícone check ✓** quando cor selecionada (não só border), para daltônicos
- Label sempre: "Cor XYZ" ou `aria-label`
- Suporte teclado: setas navegam nas opções da paleta
- Não exija cor pra função crítica (ex: "status em vermelho" sem ícone — daltônicos não veem)

---

## 3. Date Picker com calendário visual

### 3.1 Angular Material Datepicker

**Setup (já vem no Material):**
```typescript
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';

// No módulo ou componente standalone:
imports: [MatDatepickerModule, MatNativeDateModule, MatFormFieldModule, MatInputModule]
```

**Component:**
```html
<mat-form-field appearance="outline">
  <mat-label>Data do serviço</mat-label>
  <input 
    matInput 
    [matDatepicker]="picker"
    [min]="minDate"
    [max]="maxDate"
    [(ngModel)]="serviceDate"
    placeholder="dd/mm/aaaa"
    readonly
  />
  <mat-datepicker-toggle matSuffix [for]="picker"></mat-datepicker-toggle>
  <mat-datepicker #picker></mat-datepicker>
  <mat-hint>Selecione uma data futura</mat-hint>
</mat-form-field>
```

**Localização pt-BR:**
```typescript
// main.ts ou provider
import { MAT_DATE_LOCALE, DateAdapter } from '@angular/material/core';

providers: [
  { provide: MAT_DATE_LOCALE, useValue: 'pt-BR' },
]

// No constructor do component:
constructor(private dateAdapter: DateAdapter<Date>) {
  this.dateAdapter.setLocale('pt-BR');  // dd/mm/yyyy
}
```

**Formato custom (dia da semana visível):**
```typescript
import { MatDateFormats } from '@angular/material/core';

export const BR_DATE_FORMATS: MatDateFormats = {
  parse: { dateInput: 'dd/MM/yyyy' },
  display: {
    dateInput: 'dd/MM/yyyy',
    monthYearLabel: 'MMM yyyy',
    dateA11yLabel: 'EEEE, dd \'de\' MMMM \'de\' yyyy',  // "segunda-feira, 18 de abril de 2026"
    monthYearA11yLabel: 'MMMM yyyy'
  }
};
```

### 3.2 Date range picker (período)

```html
<mat-form-field appearance="outline">
  <mat-label>Período do serviço</mat-label>
  <mat-date-range-input [rangePicker]="rangePicker" [min]="today">
    <input matStartDate [(ngModel)]="startDate" placeholder="Início">
    <input matEndDate [(ngModel)]="endDate" placeholder="Fim">
  </mat-date-range-input>
  <mat-datepicker-toggle matSuffix [for]="rangePicker"></mat-datepicker-toggle>
  <mat-date-range-picker #rangePicker></mat-date-range-picker>
</mat-form-field>
```

### 3.3 Ionic datetime (mobile) — native feel

```html
<ion-item button id="open-date-modal">
  <ion-icon name="calendar-outline" slot="start" aria-hidden="true"></ion-icon>
  <ion-label>
    <h3>Data do serviço</h3>
    <p>{{ serviceDate | date:'dd/MM/yyyy':'':'pt-BR' }}</p>
  </ion-label>
</ion-item>

<ion-modal trigger="open-date-modal">
  <ng-template>
    <ion-datetime 
      presentation="date"
      locale="pt-BR"
      [value]="serviceDate.toISOString()"
      (ionChange)="onDateChange($event)"
      [min]="minDateIso"
      [max]="maxDateIso"
      showDefaultButtons="true"
      doneText="Confirmar"
      cancelText="Cancelar">
    </ion-datetime>
  </ng-template>
</ion-modal>
```

**Para datas + horas em um campo só:**
```html
<ion-datetime presentation="date-time" locale="pt-BR" ...></ion-datetime>
```

### 3.4 Regras — date picker

- **Sempre mostrar calendário** — digitar data crua é frustrante
- **Validar min/max** (não deixa escolher data passada em agendamento futuro)
- **pt-BR locale** (segunda vira "segunda-feira", não "monday")
- **Dia da semana visível** no label a11y (screen reader)
- **Teclado:** setas navegam dias, Page Up/Down muda mês
- **Mobile:** usar `ion-datetime` (nativo) em vez de inject Material no Ionic
- **Não permitir** data inválida digitada (parsa e corrige, ou rejeita)

---

## 4. Time Picker

### 4.1 Angular — com ngx-mat-timepicker ou custom

```bash
npm install @angular-material-components/datetime-picker
# ou custom:
```

**Alternativa simples sem lib: input type=time**
```html
<mat-form-field appearance="outline">
  <mat-label>Horário</mat-label>
  <input matInput type="time" [(ngModel)]="serviceTime" step="900"><!-- step 15min -->
</mat-form-field>
```

### 4.2 Ionic time picker

```html
<ion-datetime 
  presentation="time"
  locale="pt-BR"
  [value]="time"
  hourCycle="h23"
  [minuteValues]="[0, 15, 30, 45]"><!-- 15 min steps -->
</ion-datetime>
```

### 4.3 Range de horário (ex: profissional disponível 9h-18h)

Use **2 time pickers** lado a lado OU um **dual slider** visual:

```html
<div class="time-range-slider">
  <label>Disponível entre:</label>
  <mat-slider min="0" max="24" step="0.5" discrete>
    <input matSliderStartThumb [(ngModel)]="startHour">
    <input matSliderEndThumb [(ngModel)]="endHour">
  </mat-slider>
  <div class="range-display">
    {{ formatHour(startHour) }} — {{ formatHour(endHour) }}
  </div>
</div>
```

---

## 5. File preview rico (imagem/PDF)

Ver skill `br/file-upload-ux` (obrigatória).

Adições para preview:
- **Imagem:** `<img [src]="url" loading="lazy">` com `object-fit: cover`, borda, remove button
- **PDF:** ícone + nome + tamanho + "ver" que abre em new tab
- **Progress:** mat-progress-spinner ou ion-progress-bar durante upload
- **Error state:** ícone vermelho + mensagem ("Imagem muito grande, max 5MB")

```html
<div class="file-upload">
  <input type="file" #fileInput hidden accept="image/*" (change)="onFile($event)">
  
  <ng-container *ngIf="!file; else preview">
    <button mat-stroked-button (click)="fileInput.click()">
      <mat-icon>upload</mat-icon>
      Selecionar imagem
    </button>
    <small>JPG ou PNG · máx 5 MB</small>
  </ng-container>
  
  <ng-template #preview>
    <div class="preview-card">
      <img [src]="file.previewUrl" alt="Preview do arquivo" />
      <div class="preview-info">
        <strong>{{ file.name }}</strong>
        <small>{{ file.size | fileSize }}</small>
      </div>
      <button mat-icon-button (click)="remove()" aria-label="Remover arquivo">
        <mat-icon>close</mat-icon>
      </button>
    </div>
  </ng-template>
</div>
```

---

## 6. Tag/chip input (múltipla seleção)

Para categorias, habilidades, tags.

### 6.1 Angular Material MatChipsModule

```typescript
import { MatChipsModule, MatChipInputEvent } from '@angular/material/chips';
import { COMMA, ENTER } from '@angular/cdk/keycodes';
```

```html
<mat-form-field appearance="outline">
  <mat-label>Serviços que você oferece</mat-label>
  <mat-chip-grid #chipGrid aria-label="Serviços">
    <mat-chip-row 
      *ngFor="let service of services"
      (removed)="remove(service)">
      {{ service }}
      <button matChipRemove [attr.aria-label]="'Remover ' + service">
        <mat-icon>cancel</mat-icon>
      </button>
    </mat-chip-row>
  </mat-chip-grid>
  <input 
    placeholder="Adicionar serviço..."
    [matChipInputFor]="chipGrid"
    [matChipInputSeparatorKeyCodes]="[ENTER, COMMA]"
    (matChipInputTokenEnd)="add($event)"
  />
  <mat-hint>Pressione Enter para adicionar</mat-hint>
</mat-form-field>
```

### 6.2 Com autocomplete (sugestões)

```html
<mat-chip-grid #chipGrid>
  <mat-chip-row *ngFor="let s of selected" (removed)="remove(s)">
    {{ s }}
    <button matChipRemove>
      <mat-icon>cancel</mat-icon>
    </button>
  </mat-chip-row>
</mat-chip-grid>
<input 
  [matChipInputFor]="chipGrid"
  [matAutocomplete]="auto"
  [formControl]="searchCtrl"
/>
<mat-autocomplete #auto (optionSelected)="selected($event)">
  <mat-option *ngFor="let s of filtered$ | async" [value]="s">
    {{ s }}
  </mat-option>
</mat-autocomplete>
```

### 6.3 Ionic chips

```html
<ion-item>
  <ion-label position="stacked">Habilidades</ion-label>
  <div class="chips-container">
    <ion-chip 
      *ngFor="let skill of skills" 
      (click)="remove(skill)">
      {{ skill }}
      <ion-icon name="close-circle" aria-hidden="true"></ion-icon>
    </ion-chip>
    <ion-input 
      placeholder="+ Adicionar"
      (keydown.enter)="addFromInput($event)">
    </ion-input>
  </div>
</ion-item>
```

---

## 7. Rating input (estrelas)

### 7.1 Custom component

```typescript
@Component({
  selector: 'app-star-rating',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div 
      class="rating" 
      role="radiogroup"
      [attr.aria-label]="label">
      <button 
        *ngFor="let star of [1,2,3,4,5]; trackBy: trackByIndex"
        type="button"
        role="radio"
        [attr.aria-checked]="star <= value"
        [attr.aria-label]="star + ' de 5 estrelas'"
        (click)="setValue(star)"
        (mouseenter)="hoverValue = star"
        (mouseleave)="hoverValue = null"
        class="star">
        <mat-icon [class.filled]="star <= (hoverValue || value)">
          {{ star <= (hoverValue || value) ? 'star' : 'star_border' }}
        </mat-icon>
      </button>
    </div>
  `,
  styles: [`
    .rating {
      display: inline-flex;
      gap: var(--space-1);
    }
    .star {
      background: none;
      border: none;
      padding: var(--space-2);
      cursor: pointer;
      color: var(--color-neutral-400);
      transition: transform var(--motion-fast) var(--ease-out),
                  color var(--motion-fast) var(--ease-out);
      min-width: 44px;
      min-height: 44px;
    }
    .star:hover, .star:focus-visible {
      transform: scale(1.15);
    }
    .star .filled {
      color: #FFC107;
    }
    .star:focus-visible {
      outline: 2px solid var(--color-primary);
      outline-offset: 2px;
      border-radius: var(--radius-sm);
    }
  `]
})
export class StarRatingComponent {
  @Input() value = 0;
  @Input() label = 'Avaliação';
  @Output() valueChange = new EventEmitter<number>();
  hoverValue: number | null = null;

  setValue(v: number) {
    this.value = v;
    this.valueChange.emit(v);
  }
  trackByIndex(i: number) { return i; }
}

// Skills aplicadas: ui-input-rich-patterns, accessibility-pro
```

---

## 8. Number input com slider

Para "preço em R$" ou "quantidade":

```html
<mat-form-field appearance="outline">
  <mat-label>Orçamento máximo (R$)</mat-label>
  <input matInput type="number" [(ngModel)]="budget" min="50" max="5000" step="10">
  <span matTextPrefix>R$&nbsp;</span>
</mat-form-field>

<mat-slider min="50" max="5000" step="50" discrete>
  <input matSliderThumb [(ngModel)]="budget">
</mat-slider>

<!-- Mostra valor grande, visual -->
<div class="budget-display">
  <strong>{{ budget | currency:'BRL':'symbol':'1.0-0':'pt-BR' }}</strong>
  <small>por serviço</small>
</div>
```

---

## 9. Autocomplete com imagem (pessoas/categorias)

```html
<mat-form-field appearance="outline">
  <mat-label>Profissional</mat-label>
  <input matInput [matAutocomplete]="auto" [formControl]="control">
  <mat-autocomplete #auto displayWith="displayName">
    <mat-option *ngFor="let p of filteredPros$ | async" [value]="p">
      <div class="autocomplete-option">
        <img [src]="p.avatar || 'assets/default-avatar.svg'" 
             class="avatar" 
             [alt]="p.nome">
        <div class="info">
          <strong>{{ p.nome }}</strong>
          <small>{{ p.categoria }} · ⭐ {{ p.rating }}</small>
        </div>
      </div>
    </mat-option>
  </mat-autocomplete>
</mat-form-field>

<!-- CSS -->
<style>
.autocomplete-option {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) 0;
}
.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}
.info {
  display: flex;
  flex-direction: column;
}
</style>
```

---

## 10. Rich text editor (descrição de serviço)

Para campos de descrição longa com formatação (negrito, itálico, listas, links):

### 10.1 Angular — Quill ou TipTap

**TipTap (recomendado, moderno):**
```bash
npm install ngx-tiptap @tiptap/core @tiptap/starter-kit
```

```typescript
@Component({
  selector: 'app-rich-text',
  imports: [NgxTiptapModule],
  template: `
    <div class="editor-wrapper">
      <div class="toolbar">
        <button (click)="toggleBold()" [class.active]="editor.isActive('bold')">
          <mat-icon>format_bold</mat-icon>
        </button>
        <button (click)="toggleItalic()" [class.active]="editor.isActive('italic')">
          <mat-icon>format_italic</mat-icon>
        </button>
        <button (click)="toggleBulletList()" [class.active]="editor.isActive('bulletList')">
          <mat-icon>format_list_bulleted</mat-icon>
        </button>
      </div>
      <tiptap-editor [editor]="editor"></tiptap-editor>
    </div>
  `
})
export class RichTextComponent {
  editor = new Editor({ extensions: [StarterKit] });
  
  toggleBold() { this.editor.chain().focus().toggleBold().run(); }
  toggleItalic() { this.editor.chain().focus().toggleItalic().run(); }
  toggleBulletList() { this.editor.chain().focus().toggleBulletList().run(); }
}
```

### 10.2 Mobile — menos é mais

Em mobile, **raramente use rich text**. Textarea simples com placeholder bem claro serve melhor. Se precisar markdown, preview ao lado.

---

## 11. Validação visual consistente

Todos os inputs ricos devem seguir:

| Estado | Indicador visual |
|---|---|
| Default | Border neutra |
| Focus | Border primary + focus ring |
| Invalid | Border vermelha + ícone erro + hint vermelha |
| Disabled | Opacidade 0.5, cursor not-allowed |
| Success (após save) | Check verde sutil (<500ms) |

```scss
.rich-input {
  &.ng-invalid.ng-touched {
    border-color: var(--color-error);
    
    .error-hint {
      color: var(--color-error);
      display: flex;
      align-items: center;
      gap: var(--space-1);
    }
  }
  
  &.ng-valid.ng-dirty .success-icon {
    opacity: 1;
    animation: pop-in var(--motion-normal) var(--ease-out);
  }
}
```

---

## 12. Checklist por input

### Color picker
- [ ] Preview colorido visível (não só hex)
- [ ] Paleta do projeto como preset
- [ ] Aceita hex direto também (pra dev)
- [ ] Touch target ≥ 44px
- [ ] `aria-label` ou label explícito

### Date picker
- [ ] Calendário visual (não só digitar)
- [ ] Locale pt-BR
- [ ] Min/max configurados
- [ ] Dia da semana na label a11y
- [ ] Teclado funciona (setas + Enter)

### File upload (ver `file-upload-ux`)
- [ ] Preview da imagem/PDF
- [ ] Progress durante upload
- [ ] Botão remover
- [ ] Validação de tipo + tamanho com mensagem em pt-BR

### Tag/chip
- [ ] Adicionar com Enter
- [ ] Remover com botão + Backspace
- [ ] Aria-label em cada chip
- [ ] Autocomplete se lista grande

### Rating
- [ ] role=radiogroup / radio
- [ ] Preview no hover
- [ ] Teclado funciona
- [ ] aria-label "X de 5 estrelas"

### Rich text
- [ ] Toolbar acessível (botões nomeados)
- [ ] Ctrl+B, Ctrl+I funcionam
- [ ] Export pra texto puro opção

---

## 13. Anti-patterns

❌ Mostrar hex (`#1565C0`) sem preview colorido
❌ Data como `2026-04-18` cru sem calendário
❌ `<input type="date">` puro em mobile (UX nativa mas inconsistente)
❌ Time input em incrementos de 1min (roleta infinita — use 15min)
❌ Color picker em desktop sem paleta pré-definida do projeto
❌ Tag input sem atalho de Enter pra adicionar
❌ Rating sem feedback hover ou sem aria-label
❌ Autocomplete sem debounce (consulta a cada tecla)
❌ Textarea genérico pra descrição longa quando precisa formatação
❌ Datepicker em inglês num app pt-BR
❌ Campo "preço" sem símbolo R$ e formato brasileiro
❌ Input number sem min/max (usuário digita -500 ou 99999999)
❌ Input rico que não funciona por teclado

---

## Skills aplicadas
ui-input-rich-patterns
