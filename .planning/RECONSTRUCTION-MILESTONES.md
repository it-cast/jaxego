# Milestones da Reconstrução — Jaxegô v1.1

> Quebra do `RECONSTRUCTION-PLAN.md` em milestones executáveis, em ordem.
> Cada fase entra **compilada + testada + commitada** (sem autopilot puro;
> testes humanos só no MR-6, como decidido pelo dono).
> Regra de "pronto" por fase: tela funcional ligada a endpoint real, rota
> alcançável, fiel ao protótipo, zero hex, `ng build` + suíte backend verdes.

## Ordem de execução

```
MR-0 ✅  →  MR-1  →  MR-2  →  MR-3  →  MR-4  →  MR-5  →  MR-6
```

---

## MR-0 — Fundação de navegação ✅ CONCLUÍDA

Destrava tudo (login→superfície, dados autenticados, sessão persistente).

- [x] F0.1 `GET /v1/auth/me` + `resolve_surface` (5 testes)
- [x] F0.2 `authInterceptor` (Bearer — não existia; 401 em tudo)
- [x] F0.3 Roteamento pós-login por papel (corrige loop login→/entrar)
- [x] F0.4 Refresh-on-load (sobrevive a F5)
- **Verificado:** suíte backend (~500) verde + `ng build` OK. Commits `0e70bc2`→HEAD.

---

## MR-1 — App do entregador completo  ⏳ PRÓXIMA

A superfície mais quebrada. Backend pronto: `dispatch/offers/*` (accept/decline),
`proofs/*`, `withdrawals/*`, `scores/couriers/{id}/score`, `couriers/{id}/availability`.

> ⚠️ **Lacuna cross-layer descoberta (corrigida por leitura):** os estados JÁ são
> avançados pelos proofs (`proofs/service`: coleta→COLETADA, entrega→ENTREGUE,
> recusa→RECUSADA) — não falta endpoint de transição. O que falta é o entregador
> **ler a própria entrega**: `deliveries GET /{id}` é só `merchant_scope`. A tela
> `tpl-c-active` precisa de um GET courier-scoped. Por isso F1.0 é leitura, não transição.

- [ ] **F1.0 — Backend: leitura de entrega pelo entregador** — `GET` da entrega
      ativa + detalhe, escopado ao courier do usuário (IDOR→404), reusando a
      serialização com minimização de PII por estado (endereço só pós-COLETADA).
      Testes. Pré-requisito de F1.2/F1.5.
- [ ] **F1.1 — Home real** (`tpl-c-home`): toggle online (`PATCH availability`),
      ganhos/saldo (`withdrawals/balance`), score+selo (`scores/{id}`), entregas
      recentes (`deliveries`), **offer overlay** fiado (`dispatch/active` → accept/decline).
- [ ] **F1.2 — Entrega ativa** (`tpl-c-active`): página nova + máquina de estados,
      avanço, mapa lazy, timeline, liga `location-polling.service`.
- [ ] **F1.3 — Comprovação + Concluída** (`tpl-c-proof`/`tpl-c-done`): fiar
      `comprovacao.page` no fluxo; confirmar pgto direto; tela de sucesso.
- [ ] **F1.4 — Perfil** (`tpl-c-profile`): breakdown de score, documentos, chave PIX.
- [ ] **F1.5 — Ganhos/extrato + lista** (`tpl-c-earnings`): consolida `saldo.page`,
      remove stub `ganhos`, lista de entregas real.
- **Aceite:** loop online→oferta→aceite→coleta→foto→entrega→concluída fecha; zero stub.

---

## MR-2 — Admin da área completo

Backend: `platform_admin/*`, `invoices`, admin KYC (`couriers/admin`), `proofs/manual-release`.

- [ ] **F2.1 — Dashboard de filas** (`tpl-a-dash`): substitui stub `admin/inicio`;
      contadores reais clicáveis + KPIs.
- [ ] **F2.2 — Fila KYC** (rota+página usando `queue-table` órfão) → detalhe (existe) → ativar.
- [ ] **F2.3 — Listas**: entregadores (→ detalhe existente) + lojas da área.
- **Aceite:** admin vê filas, clica, age (aprovar KYC, ativar, resolver disputa).

---

## MR-3 — Admin da plataforma + "criar área"

Backend: `areas` (POST/PATCH/archive — sem UI), `platform_admin/areas/{id}/revenue-share`.

- [ ] **F3.1 — CRUD de área**: criar/editar/arquivar (a tela que não existe).
- [ ] **F3.2 — Revenue-share + designar admin de área** (fecha "criei área → quem opera").
- **Aceite:** crio área nova, designo admin, defino revenue-share pela UI, auditado.

---

## MR-4 — Loja: fechar lacunas

Superfície mais completa; só refinos.

- [ ] **F4.1 — "Procurando entregador"** (`tpl-m-searching`) com polling até aceite.
- [ ] **F4.2 — Dashboard** (`tpl-m-dash`) com KPIs/em-curso reais.
- **Aceite:** loja cria → procura → acompanha no detalhe.

---

## MR-5 — Separação física em 4 apps (mecânico, por último)

Feito depois que os fluxos existem, para não mover código quebrado. ADR-001.

- [ ] **F5.1 — `packages/shared`**: design system (`jx-*`), models, http, auth, tokens.
- [ ] **F5.2 — `apps/entregador`** (Ionic + Capacitor) consumindo shared.
- [ ] **F5.3 — `apps/admin` + `apps/loja`** consumindo shared.
- **Aceite:** os 4 apps buildam isolados; `apps/api` intacto.

---

## MR-6 — Validação ao vivo + release (testes humanos AQUI)

- [ ] **F6.1 — HUMAN-UAT ao vivo** (`pytest -m mysql` + B2): migrations reversíveis,
      triggers append-only, geofence, concorrência. Popular `HUMAN-UAT-BACKLOG`.
- [ ] **F6.2 — Blockers Safe2Pay** (TD-10-01/03, TD-15-01): confirmar contrato → ADR → adapter.
- [ ] **F6.3 — Lighthouse/p95 + APK assinado** (TD-14-03/04).
- **Aceite:** UAT por superfície verde; blockers resolvidos; deploy go.
