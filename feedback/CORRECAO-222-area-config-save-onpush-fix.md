# CORRECAO-222 — Area config save não enviava PATCH ao backend

## Data
2026-07-09

## Sintoma
O botão "Salvar configurações" em `/admin/config` não enviava o PATCH ao backend.
Audit log confirmou: nenhuma entrada `area.config.update` após as últimas mudanças.

## Diagnóstico
Três causas concorrentes com `ChangeDetectionStrategy.OnPush`:

### 1. `Validators.required` em inputs `type="number"` (causa mais provável)
Angular's `NumberValueAccessor` converte input vazio para `null`.
`Validators.required` falha para `null` → `form.invalid = true` → `save()` retornava cedo
(`if (this.form.invalid) { return; }`), sem enviar o PATCH. O botão continuava clicável
(OnPush não atualizou o `[disabled]`), mas o método saía silenciosamente.

### 2. `[disabled]="form.invalid"` com OnPush
Com OnPush, o binding `[disabled]="saving() || form.invalid"` só re-avalia quando um
signal muda. Se o form ficasse inválido após input do user (sem mudança de signal),
o botão poderia manter estado stale — dependendo da ordem dos eventos.

### 3. `patchValue` sem `markForCheck()`
Após `patchValue()` em contexto async (ngOnInit, save), o OnPush component não
re-renderizava o DOM com os valores atualizados sem um `markForCheck()` explícito.

## Correções aplicadas

### `area-config.page.ts`
1. Injetado `ChangeDetectorRef`
2. Removido `Validators.required` dos controls numéricos — `Validators.min` já cobre
   o caso vazio (min(1), min(10), min(30) rejeitam null/0/NaN)
3. Adicionado `this.cdr.markForCheck()` após ambos os `patchValue()` calls
   (ngOnInit e save success)

### `area-config.page.html`
4. Botão: `[disabled]="saving()"` — nunca bloqueado por `form.invalid`; o guard
   interno em `save()` mostra os erros inline via `markAllAsTouched()`

## Verificação
- `ng build admin --configuration=development` → zero erros
- Teste direto no backend (Python/Docker): `update_area` commita corretamente
- DB confirma que backend persiste `max_entregas_simultaneas` quando chamado
