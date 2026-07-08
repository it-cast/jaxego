# CORRECAO-212 — Cadastro: toggle centralizado + lat/lng no signup

**Data:** 2026-07-08

## Mudanças

### 1. Toggle Mensal/Anual — centralizado + cor laranja do sistema

**Problema:** botão ativo usava `var(--color-primary, #2563eb)` (azul hardcoded) e o toggle não estava centralizado na tela de planos do cadastro.

**Correção:**
- `packages/shared/src/shared/components/cycle-toggle/cycle-toggle.component.ts`
  - Border do container: `var(--brand)` (laranja do sistema)
  - Botão ativo: `background: var(--brand)` + `color: var(--brand-contrast, #fff)`
  - Badge "2 meses grátis": `var(--success)` (já estava correto)
  - Cores de texto passivas: `var(--text-muted)` e `var(--surface-elevated)`
- `apps/web/src/features/loja/cadastro/cadastro.page.scss`
  - Adicionada `.jx-cadastro__cycle-row { display: flex; justify-content: center; }`

### 2. Lat/lng gravado no signup

**Problema:** o GPS já capturava `latitude`/`longitude` no browser (para reverse geocoding do endereço), mas as coordenadas não eram enviadas ao backend nem gravadas no `merchant`.

**Correção:**

**Frontend:**
- `apps/web/src/features/loja/cadastro/merchant.models.ts` — `SignupRequest` agora tem `lat?: number; lng?: number`
- `apps/web/src/features/loja/cadastro/cadastro.page.ts`
  - Adicionados `private gpsLat` e `private gpsLng` para guardar as coordenadas ao capturar GPS
  - `submit()` passa `lat` e `lng` no request quando disponíveis

**Backend:**
- `apps/api/app/merchants/schemas.py` — `MerchantSignupBody` agora aceita `lat: float | None` e `lng: float | None` (validados: lat -90/90, lng -180/180)
- `apps/api/app/merchants/service.py` — `signup()` usa `body.lat` e `body.lng` em vez de `None` hardcoded

**Comportamento:** se o usuário não usar o GPS, `lat`/`lng` ficam `null` no banco (como antes). Se usar, são gravados com precisão total da API de geolocalização do browser.
