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

- [x] **F1.0 — Backend: leitura de entrega pelo entregador** — `GET active/{id}/lista`
      courier-scoped (IDOR→404), PII por estado (RN-013). 3 testes verdes.
- [x] **F1.1 — Home real** (`tpl-c-home`): toggle online, saldo, score+selo,
      recentes, offer overlay (poll `/offers/active` → accept→entrega-ativa / decline).
- [x] **F1.2 — Entrega ativa** (`tpl-c-active`): página + estados + timeline + CTA
      que roteia para comprovação (pickup/delivery/refusal). `EntregadorService`.
- [~] **F1.3 — Comprovação + Concluída**: `comprovacao.page` (já existia) **fiada**
      no fluxo via CTA da entrega ativa. Falta a tela de sucesso dedicada (`tpl-c-done`).
- [x] **F1.4 — Perfil** (`tpl-c-profile`): nível + breakdown do score (ADR-013) +
      status do cadastro. _Pendência:_ identidade/docs/PIX exigem endpoint
      courier self-profile (registrar como F1.6 backend).
- [x] **F1.5 — Lista real + consolida ganhos→saldo**: `entregas.page` real;
      stub `ganhos` removido; tab aponta para `/saldo`.
- [x] **F1.3b — Tela de entrega concluída** (`tpl-c-done`): sucesso + resumo
      (valor recebido, taxa) + CTA voltar. Comprovação fiada: pickup→entrega ativa;
      delivery+pgto→concluída; recusa→concluída. ng build OK.
- [x] **F1.6 — Courier self-profile** — `GET /v1/couriers/{id}/profile` (nome,
      CPF/phone/email mascarados, veículo, documentos+status) + UI no perfil. ng build OK.
- [ ] **F1.7 — Chave PIX no perfil** — exige migration (campo `pix_key` no courier)
      + endpoint PUT + UI. Adiado (sem migration nesta rodada).
- **Aceite:** loop online→oferta→aceite→coleta→foto→entrega navega ponta a ponta.
  Tudo `ng build` OK e commitado. Restam F1.3b (tela sucesso) e F1.6 (perfil completo).

---

## MR-2 — Admin da área completo

Backend: `platform_admin/*`, `invoices`, admin KYC (`couriers/admin`), `proofs/manual-release`.

- [x] **F2.0 — Backend: lista de entregadores da área** — `GET /v1/admin/couriers`
      (area-scoped, filtro status, CPF mascarado) + teste. _(gap descoberto: admin
      só tinha detalhe/review, sem lista)._
- [x] **F2.1 — Dashboard de filas** (`tpl-a-dash`): `admin/inicio` real com
      contadores clicáveis (KYC pendente/disputas/suspensões). + **navegação lateral
      do shell admin** (não existia).
- [x] **F2.2 — Fila KYC**: aba "Fila de validação" na lista de entregadores →
      `/admin/kyc/:id` (revisão, já existia) → ativar.
- [x] **F2.3 — Listas**: entregadores (fila+todos → detalhe).
- [x] **F2.4 — Lista de lojas**: `GET /v1/admin/merchants` (area-scoped, doc
      mascarado, testado) + página `/admin/lojas` + link no shell.
- **Aceite:** admin navega filas, abre, age. **MR-2 COMPLETA.** ng build + testes verdes.

---

## MR-3 — Admin da plataforma + "criar área"

Backend: `areas` (POST/PATCH/archive — sem UI), `platform_admin/areas/{id}/revenue-share`.

- [x] **F3.1 — CRUD de área**: criar/editar/arquivar em `/plataforma/areas` +
      link no shell. Sobre `/v1/areas` (backend já existia). ng build OK.
- [x] **F3.2 — Revenue-share**: % por área (`setRevenueShare`) na mesma tela.
- [x] **F3.3 — Designar admin de área**: `POST /v1/areas/{id}/admins` (por e-mail,
      cria/atualiza `area_admins`, auditado, testado) + form na tela de áreas.
- **Aceite:** crio área, defino repasse e designo admin pela UI. **MR-3 COMPLETA.**

---

## MR-4 — Loja: fechar lacunas

Superfície mais completa; só refinos.

- [x] **F4.1 — "Procurando entregador"**: após criar → detalhe; banner + polling
      5s enquanto CRIADA até o aceite (reduced-motion aware). ng build OK.
- [x] **F4.2 — Dashboard** (`tpl-m-dash`): já real (DeliveryService + KPIs + em-curso).
- **Aceite:** loja cria → procura → acompanha no detalhe. ✅

---

## MR-5 — Separação física dos apps ✅ CONCLUÍDA

Estratégia escolhida (baixo risco, verificável): **build targets separados por app**
no mesmo workspace, compartilhando o código-fonte (sem mover arquivos = zero
reescrita de imports = zero quebra). Cada app tem rotas + bootstrap próprios e
empacota só a sua superfície.

- [x] **F5.1 — Rotas por superfície** (`app.routes.ts`): grupos nomeados
      (auth/entregador/loja/admin/plataforma/public) + mapas por app
      (`entregadorAppRoutes`/`lojaAppRoutes`/`adminAppRoutes`).
- [x] **F5.2 — Bootstrap por app**: `main.{entregador,loja,admin}.ts` +
      `makeAppConfig(routes)` (providers idênticos, rotas por app).
- [x] **F5.3 — Projetos no `angular.json`**: `entregador` (Capacitor →
      `dist/entregador/browser`), `loja`, `admin` — cada um build próprio +
      `serve`. Scripts `build:entregador|loja|admin|apps`.
- **Aceite:** `ng build entregador|loja|admin` **e** `web` (combinado) buildam ✅.
  Cada app empacota só sua superfície (bundles menores). `apps/api` intacto.
- _Nota:_ mover as features para pastas físicas `apps/{admin,loja,entregador}/` é
  refinamento opcional futuro; a separação de **apps/builds/deploy** já está feita.

---

## Matriz de cobertura do protótipo (autoridade de completude)

> Cada tela do `prototipo.html` + caso de uso central → fase → status.
> ✅ entregue · 🟡 parcial · ❌ falta. Atualizada em 2026-06-16.

### App do entregador (mobile)

| Tela protótipo | Rota | Fase | Status |
|---|---|---|---|
| `tpl-c-home` (início/ganhos/oferta) | `/entregador/inicio` | F1.1 | ✅ |
| `tpl-c-active` (entrega ativa) | `/entregador/entrega-ativa` | F1.2 | ✅ |
| `tpl-c-proof` (comprovação) | `/entregador/entrega/:id/comprovar/:kind` | Phase 9/F1.3 | ✅ (fiada) |
| `tpl-c-done` (concluída) | — | **F1.3b** | ❌ falta tela de sucesso |
| `tpl-c-profile` (perfil/score) | `/entregador/perfil` | F1.4 | 🟡 score✅; identidade/docs/PIX dependem de **F1.6** |
| `tpl-c-earnings` (extrato/saque) | `/entregador/saldo` | — | ✅ |
| `tpl-c-coverage` (bairros/preços) | `/entregador/cobertura` | — | ✅ |
| oferta (sheet+timer) | overlay na home | F1.1 | ✅ |

### Painel da loja (web)

| Tela protótipo | Rota | Status |
|---|---|---|
| `tpl-m-dash` (dashboard+em curso) | `/loja/painel` | ✅ (KPIs reais via DeliveryService) |
| `tpl-m-new` (nova entrega) | `/loja/entregas/nova` | ✅ |
| `tpl-m-searching` (procurando entregador) | — | ❌ **F4.1** |
| `tpl-m-detail` (detalhe+timeline) | `/loja/entregas/:id` | ✅ |
| `tpl-m-list` (entregas) | `/loja/entregas` | ✅ |
| `tpl-m-plan` (plano & faturas) | `/loja/plano` + `/loja/faturas` | ✅ |

### Admin da área (web)

| Tela protótipo | Rota | Fase | Status |
|---|---|---|---|
| `tpl-a-dash` (painel de filas) | `/admin/inicio` | F2.1 | ❌ stub |
| fila de KYC (lista pendentes) | — | F2.2 | ❌ sem rota/página |
| `tpl-a-kyc` (revisão item-a-item) | `/admin/kyc/:courierId` | — | ✅ (detalhe; falta como chegar) |
| detalhe do entregador (score/suspensão) | `/admin/entregadores/:courierId` | — | ✅ (falta lista p/ chegar) |
| lista de entregadores | — | F2.3 | ❌ |
| lista de lojas | — | F2.3 | ❌ |
| `tpl-a-config` (configurações) | `/admin/config` | — | ✅ |
| disputas | `/admin/disputas` | — | ✅ |
| API keys | `/admin/api-keys` | — | ✅ |

### Admin da plataforma (web)

| Função | Rota | Fase | Status |
|---|---|---|---|
| visão geral | `/plataforma/visao-geral` | — | ✅ |
| pessoas | `/plataforma/pessoas` | — | ✅ |
| disputas | `/plataforma/disputas` | — | ✅ |
| **criar/editar/arquivar área** | — | F3.1 | ❌ backend existe, UI não |
| revenue-share por área | — | F3.2 | ❌ |
| designar admin de área | — | F3.2 | ❌ |

### Público

| Tela | Rota | Status |
|---|---|---|
| `tpl-track` (rastreio) | `/r/:token` | ✅ |

### Casos de uso transversais

| Caso de uso | Status |
|---|---|
| Login → superfície correta por papel | ✅ MR-0 |
| Sessão sobrevive a F5 (refresh-on-load) | ✅ MR-0 |
| Loja cria entrega → dispara oferta → entregador aceita → executa → comprova | ✅ (loja+entregador prontos; falta `tpl-m-searching` para o "ao vivo" da loja) |
| Admin valida KYC → ativa entregador | 🟡 detalhe pronto; **falta a fila** (F2.2) |
| Plataforma cria área → designa admin → define revenue-share | ❌ MR-3 |
| Pagamento cartão/PIX com split (Safe2Pay) | 🟡 código contra Stub; **blocker de contrato** (MR-6 / TD-10) |
| Validação ao vivo (MySQL/B2): migrations, triggers, geofence | ❌ MR-6 |

### Polimentos de fidelidade ao protótipo (status)

- [x] Tabbar do entregador = Início/Ganhos/Bairros/Perfil
- [x] Navegação no shell da loja (Painel/Entregas/Favoritos/Faturas/Plano)
- [x] Mapa na entrega ativa do entregador + fonte de tiles configurável (Mapbox/MapTiler-ready)
- [x] Badge "PAGAMENTO DIRETO 💵" (token `payment.direct`) em entrega-ativa/listas/detalhe
- [x] Nº do pedido na comprovação (`proof.submitReference`)
- [x] "Ganhos/liberado hoje" na home (computado do extrato)
- [x] Mapa no detalhe da entrega da loja (coords expostas ao lojista dono)
- [ ] **Ligar/Mensagem** (entrega ativa / detalhe loja) — **bloqueado**: telefone é
      mascarado por privacidade (RN-022); botão real exige número não-mascarado ao
      dono OU proxy-call. Não implementado como botão "fake".
- [ ] **F1.7 — Chave PIX no perfil** — bloqueado por migration (`pix_key`).

### Fases novas/explicitadas para fechar 100%

- **F1.3b** — Tela de entrega concluída (`tpl-c-done`): sucesso + resumo (valor, taxa, +score) + CTAs.
- **F1.6** — Backend: courier self-profile (`GET /v1/couriers/{id}/profile`: nome, CPF mascarado, veículo, documentos, chave PIX) para completar o perfil.

---

## MR-6 — Validação ao vivo + release (testes humanos AQUI)

- [ ] **F6.1 — HUMAN-UAT ao vivo** (`pytest -m mysql` + B2): migrations reversíveis,
      triggers append-only, geofence, concorrência. Popular `HUMAN-UAT-BACKLOG`.
- [ ] **F6.2 — Blockers Safe2Pay** (TD-10-01/03, TD-15-01): confirmar contrato → ADR → adapter.
- [ ] **F6.3 — Lighthouse/p95 + APK assinado** (TD-14-03/04).
- **Aceite:** UAT por superfície verde; blockers resolvidos; deploy go.
