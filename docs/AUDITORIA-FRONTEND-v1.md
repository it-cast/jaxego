# Auditoria de Frontend — Jaxegô v1.0 (estado real × planejado)

> Gerada em 2026-06-15. Varredura arquivo-a-arquivo de `apps/web/src/features`,
> cruzada com endpoints de `apps/api/app/*/router.py`, `app.routes.ts`, o
> `prototipo.html` e o `STATE.md`. Legenda de estado:
>
> - **REAL** — página com template + lógica + service HTTP, fluxo plausível.
> - **PARCIAL** — existe mas com furo (sem rota, sem dado, sem caminho de chegada).
> - **STUB** — só `<jx-empty-state>` / placeholder "em breve".
> - **FALTANDO** — planejado/no protótipo, sem página nem rota.
>
> ⚠️ "REAL" aqui = código coerente, **não** = validado ao vivo (MySQL/B2/Safe2Pay reais nunca foram exercidos — ver `HUMAN-UAT-BACKLOG.md` vazio).

---

## 0. Bloqueador transversal (atinge tudo)

| Item | Estado | Evidência |
|---|---|---|
| Roteamento pós-login por papel | **QUEBRADO** | `login.page.ts:87` navega para `/`; `app.routes.ts:13-17` redireciona `/` → `/entrar`. Comentário: "surface routing in T-06" — nunca feito. **Loga e volta pro login.** |

Enquanto isso não existir, nenhuma superfície é alcançável sem digitar URL na mão. É o primeiro a consertar.

---

## 1. App do entregador (mobile) — superfície mais incompleta

| Rota | Página | Linhas | Estado | Observação |
|---|---|---|---|---|
| `/entregador/inicio` | `inicio.page.ts` | 121 | **STUB funcional** | 4 estados de dispatch como empty-states, dirigidos por `@Input()` que **nenhum pai preenche**; sem service. Sem ganhos/saldo/score/recentes do protótipo (`tpl-c-home`). `offer-active` = placeholder "T-11". |
| `/entregador/entregas` | `entregas.page.ts` | 20 | **STUB** | empty-state puro. |
| `/entregador/ganhos` | `ganhos.page.ts` | 20 | **STUB** | empty-state puro. Duplica conceito de `/saldo` (que é real). |
| `/entregador/perfil` | `perfil.page.ts` | 41 | **STUB** | "em breve" + theme toggle. Sem score breakdown/documentos/PIX do protótipo. |
| `/entregador/cobertura` | `cobertura-precos.page.ts` | 213 | **REAL** | bairros + preços + validação de piso. |
| `/entregador/entrega/:id/comprovar/:kind` | `comprovacao.page.ts` | 130 | **REAL** | captura foto + GPS. |
| `/entregador/saldo` | `saldo/saldo.page.ts` | 235 | **REAL** | extrato + saque. |
| `/entregador/cadastro` | `cadastro/cadastro.page.ts` | 350 | **REAL** | wizard KYC (público). |
| — oferta (receber/aceitar) | `oferta/offer-sheet.component.ts` | comp. | **PARCIAL** | componente + `offer.service` + timer existem; **sem rota/página que monte o fluxo**. |
| — entrega ativa (coletar→entregar, máquina 7 estados) | `entrega-ativa/` | — | **FALTANDO** | só `location-polling.service.ts`. **Nenhuma página.** É o centro do protótipo (`tpl-c-active`). |

**Veredito:** o entregador navega só em cobertura, saldo, comprovação e cadastro. Home, lista, ganhos, perfil = placeholders. O **loop de execução de entrega não existe como tela**, apesar de o backend (`dispatch /active /accept /decline`, `proofs/*`) estar pronto.

---

## 2. Loja (web) — superfície mais completa

| Rota | Página | Linhas | Estado |
|---|---|---|---|
| `/loja/cadastro` | `cadastro.page.ts` | 302 | **REAL** |
| `/loja/plano` | `plano.page.ts` + 6 componentes | 182 | **REAL** |
| `/loja/painel` | `dashboard.page.ts` | 96 | **REAL** (verificar dados ao vivo) |
| `/loja/entregas/nova` | `nova-entrega.page.ts` | 263 | **REAL** |
| `/loja/entregas` | `entregas-list.page.ts` | 100 | **REAL** |
| `/loja/entregas/:id` | `entrega-detalhe.page.ts` | 104 | **REAL** |
| `/loja/favoritos` | `favoritos.page.ts` | 166 | **REAL** |
| `/loja/faturas` | `financeiro/fatura.page.ts` | 120 | **REAL** |
| `/loja/entregas/:id/recibo` | `financeiro/recibo.page.ts` | 100 | **REAL** |
| `/loja/inicio` | `inicio.page.ts` | 47 | thin (menor) |

**Veredito:** loja está majoritariamente construída. Pendência real = validação ao vivo + Safe2Pay (Stub).

---

## 3. Admin da área (web)

| Rota | Página | Linhas | Estado | Observação |
|---|---|---|---|---|
| `/admin/inicio` | `inicio.page.ts` | 17 | **STUB** | empty-state. Dashboard do protótipo (`tpl-a-dash`, "Filas que precisam de você") **não construído**. |
| `/admin/kyc/:courierId` | `kyc/kyc-detalhe.page.ts` | 138 | **REAL** | revisão item-a-item. |
| — fila KYC (lista de pendentes) | `kyc/queue-table.component.ts` | comp. | **FALTANDO** | componente existe, **sem rota/página**. Não há como CHEGAR no detalhe KYC pela UI. |
| `/admin/config` | `area-config.page.ts` | 208 | **REAL** |
| `/admin/bairros` | `neighborhoods.page.ts` | 156 | **REAL** |
| `/admin/api-keys` | `api-keys.page.ts` | 402 | **REAL** |
| `/admin/disputas` | `governanca/disputas.page.ts` | 189 | **REAL** |
| `/admin/entregadores/:courierId` | `governanca/entregador-detalhe.page.ts` | 181 | **REAL** | mas — sem lista de entregadores para chegar nele. |
| — lista de entregadores da área | — | — | **FALTANDO** | sem página de listagem. |

---

## 4. Admin da plataforma (super-admin, web)

| Rota | Página | Linhas | Estado | Observação |
|---|---|---|---|---|
| `/plataforma/visao-geral` | `visao-geral.page.ts` | 110 | **REAL** |
| `/plataforma/pessoas` | `pessoas.page.ts` | 160 | **REAL** |
| `/plataforma/disputas` | `disputas.page.ts` | 105 | **REAL** |
| — criar/editar/arquivar área | — | — | **FALTANDO** | backend `areas/router.py` tem `POST/PATCH/archive`; **zero UI**. "Adicionar área" inacessível. |
| — revenue-share por área | — | — | **FALTANDO** | `platform_admin PUT /areas/{id}/revenue-share` existe; sem UI. |

---

## 5. Público

| Rota | Página | Estado |
|---|---|---|
| `/r/:token` | `public-tracking.page.ts` (116) | **REAL** |

---

## 6. Cobertura CRUD — backend existe × UI

| Recurso | Backend | UI | Gap |
|---|---|---|---|
| Áreas (criar/editar/arquivar) | ✅ `areas/router.py` | ❌ | **FALTANDO UI** |
| Revenue-share por área | ✅ `platform_admin` | ❌ | **FALTANDO UI** |
| Fila KYC (listar pendentes) | ✅ (couriers/admin) | ❌ (só detalhe) | **FALTANDO UI** |
| Lista de entregadores (área) | ✅ `platform_admin/couriers` | ❌ | **FALTANDO UI** |
| Dispatch (oferta/aceite) | ✅ `dispatch/*` | ⚠️ componente, sem página | **PARCIAL** |
| Entrega ativa (máquina 7 estados) | ✅ `deliveries`, `proofs` | ❌ | **FALTANDO UI** |
| Avaliação loja→entregador | ✅ `ratings POST` | ❓ verificar | suspeita de gap |
| Suspensões | `suspensions/router.py` vazio? | ⚠️ UI em governança | verificar backend |

---

## 7. Fluxos quebrados de ponta a ponta (prioridade)

1. **Login → superfície** (bloqueia tudo) — `login.page.ts:87`.
2. **Entregador: online → oferta → aceite → entrega ativa → coleta → comprovação** — falta montar oferta + criar página de entrega ativa.
3. **Admin: ver fila KYC → abrir → aprovar/ativar** — falta tela de fila.
4. **Plataforma: criar área → designar admin** — falta tela de criar área.
5. **Home do entregador e do admin** — substituir stubs pelos dashboards do protótipo.

---

## 8. Ordem sugerida de reconstrução (para priorização do dono)

Sprint A (destrava navegação): #1 roteamento pós-login + #3 fila KYC + #4 criar área.
Sprint B (núcleo entregador): #2 oferta + entrega ativa + home real + perfil/ganhos.
Sprint C (polish): dashboards (admin/loja), listas faltantes, avaliações.
Sprint D (separação de apps — ADR-001): `apps/{api,admin,loja,entregador}` + `packages/shared`.
Sprint E (ao vivo): rodar `HUMAN-UAT-BACKLOG` real (MySQL/B2) + resolver `pre_launch_blocker` Safe2Pay.
