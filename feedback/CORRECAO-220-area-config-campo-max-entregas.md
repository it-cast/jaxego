# CORRECAO-220 — Campo max_entregas_simultaneas na tela de config da área

## Data
2026-07-09

## Problema
Após mover `max_concurrent` para `areas.config`, a tela `/admin/config` não
exibia o campo, impossibilitando o admin de configurar o limite via UI.

## Solução

### `area-config.service.ts`
- Adicionado `max_entregas_simultaneas: number` à interface `AreaConfig`

### `area-config.page.ts`
- Form control: `max_entregas_simultaneas` com `Validators.min(1)` / `Validators.max(10)`
- `normalise()`: default 1
- `buildConfig()`: inclui `Number(v.max_entregas_simultaneas)`
- `computeDiff()`: label `'Entregas simultâneas'` (aparece no modal de confirmação de audit)
- `rangeError()`: mensagem para o campo
- `patchValue()`: carrega valor salvo ao inicializar

### `area-config.page.html`
- Novo `<label>` com `<input type="number" min="1" max="10">` e hint explicativo
- No fieldset de Despacho (já existente, `--2col`)

### `area-config.page.scss`
- `.jx-area-config__hint` para o texto descritivo abaixo do input
- `grid-column: 1 / -1` no último filho ímpar do `--2col` para o campo ocupar
  a linha inteira quando há 3 campos (sem quebrar o layout de 2 colunas anterior)
