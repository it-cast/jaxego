---
phase: 08-despacho-em-cascata-oferta-aceite
title: Despacho em cascata + oferta + aceite
status: draft
platform: mobile (superfície Entregador — Ionic, mobile-first) + Loja (web, telas favoritos/aceito)
gate2_visual_contract: pending-checker
generated_by: gsd-ui-researcher
generated_at: 2026-06-10
reuses: 03-shell-frontend-design-system-3-superf-cies, 05-cadastro-do-entregador-kyc, 06-rea-oper-vel-cobertura-tabela-de-frete, 07-cria-o-de-entrega-m-quina-de-estados
---

# UI-SPEC — Phase 8: Despacho em cascata + oferta + aceite

> Design contract da Phase 8 (Gate 2 — Visual Contract). **BLOQUEIA** `plan-phase` se não existir.
> Superfícies: **Entregador** (app mobile Ionic — home online/offline + **sheet de oferta** com cronômetro) e **Loja** (web — favoritos/bloqueados + card do entregador que aceitou).
> **Regra de ouro Gate 2:** todo valor visual é token. Nenhum `#hex` hardcoded. Todo token/var citado existe em `docs/identidade-visual/tokens.json` (§9) ou na camada semântica da Phase 3 (`apps/web/src/styles/_semantic.scss`).
> **Princípio desta phase:** *reusar*, não reinventar. Temas claro/dark (DEC-001), tipografia, motion, 4 componentes de estado, `jx-state-badge`, `jx-data-table`, `jx-availability-toggle` e o shell Ionic do entregador **já existem** (Phases 3/5/6/7). Aqui especificamos só o **novo**: a **home do entregador** (tela 04 — estado aguardando/oferta ativa), o **`jx-offer-sheet`** (sheet de oferta, tela 05, com **cronômetro cosmético**), o **`jx-offer-timer`** (cronômetro com motion + aria-live), as listas **favoritos/bloqueados** da Loja (tela 15) e o **`jx-accepted-courier-card`** (entregador que aceitou — nome/foto/placa/score).
> **`has_pii: false`** (ROADMAP) — mas **RN-013 é privacidade crítica**: a oferta **NUNCA** expõe o endereço completo do destino (só bairro + distância) nem a localização dos entregadores online à Loja (ADR-007). Vazamento aqui é falha de privacidade, não bug cosmético.
> **Redis TTL é a fonte de verdade do timer (ADR-104).** O cronômetro do app é **cosmético** — nunca o cliente decide se a oferta expirou; o servidor decide. A UI degrada graciosamente quando o relógio e o servidor divergem (§3.4).

---

## Fontes de verdade consultadas

- `.planning/phases/08-.../08-CONTEXT.md` — decisões **D-01..D-08** (cascata sequencial RN-009, ranking OSRM+score+carga+preço, timeout Redis TTL ADR-104, oferta só bairro+distância RN-013, aceite único com lock F-05 E3, favoritos/bloqueados separados RN-014, exceções E1-E4, adapters OSRM/push).
- `docs/identidade-visual/tokens.json` — tokens **canônicos** (FONTE da verdade visual). **`color.delivery_state`** (estado da entrega no card da Loja), **`color.score_level`** (5 níveis de score: probation/bronze/prata/ouro/diamante), **`motion.fast/normal/slow/easing_out`** (cronômetro) — usados literalmente (§9).
- `.planning/phases/03-.../UI-SPEC.md` — design system (21 vars semânticas claro/dark, tipografia, motion, 4 componentes de estado). Contrato herdado.
- `.planning/phases/05-.../UI-SPEC.md` — cadastro/KYC do entregador (foto, placa, score do entregador) — fonte dos dados exibidos no `jx-accepted-courier-card`.
- `.planning/phases/06-.../UI-SPEC.md` — **`jx-availability-toggle`** (online/offline, `role="switch"`, ≥44px, reduced-motion) + elegibilidade espacial/cobertura. Reusamos o toggle integralmente na home.
- `.planning/phases/07-.../UI-SPEC.md` — **`jx-state-badge`** (7 estados, derivado de `color.delivery_state`), **`jx-data-table`**, padrão de modal/confirmação anti-dark-pattern. Reusados.
- `apps/web/src/` — código real a reusar: `features/entregador/disponibilidade/availability-toggle.component.ts` (`jx-availability-toggle`), `shared/components/state-badge/state-badge.component.ts` (`jx-state-badge`), `shared/components/data-table/data-table.component.ts` (`jx-data-table`), `shared/state/*` (4 estados), `layouts/entregador-shell.component.ts` (tabs Ionic Início/Entregas/Ganhos/Perfil), `features/entregador/inicio.page.ts` (home atual com empty-state), `core/theme/*`, `styles/_semantic.scss` + `_tokens.scss`, `shared/util/money.ts` (`formatBrl`).
- `projeto/wireframes/05-entregador-oferta.html`, `04-entregador-home.html`, `15-loja-favoritos.html` — contratos DOM (lidos linha a linha).
- `projeto/regras-negocio/fluxos.md` §F-05 (`:90-106`) — despacho/aceite + exceções E1-E4. `regras.md` RN-009 (cascata, nunca broadcast), RN-013 (privacidade destino), RN-014 (bloqueio privado).
- `.planning/DECISIONS.md` — ADR-007 (cascata), ADR-104 (timer Redis TTL), ADR-013 (score sem peso no M1).
- `.planning/ROADMAP.md` Phase 8 — flags (has_ui, has_api, mobile:true, integration_check:true, has_pii:false) + skills obrigatórias.

### Skills aplicadas (matriz UI + flags Phase 8)

- `product/component-library-governance` — **reusar** `jx-availability-toggle`, `jx-state-badge`, `jx-data-table`, 4 estados. Novos componentes governados (story + baseline §10): **`jx-offer-sheet`** (sheet de oferta), **`jx-offer-timer`** (cronômetro cosmético + aria-live), **`jx-favorite-row`** / **`jx-blocked-row`** (linhas das listas da Loja), **`jx-accepted-courier-card`** (entregador que aceitou), **`jx-score-chip`** (chip de score, deriva de `color.score_level`).
- `ux-advanced/design-tokens-system` — consumir só camada semântica (`var(--surface)`, `var(--brand)`) + 7 vars de estado (já existem) + **5 vars de score novas** derivadas de `color.score_level` (§7.1) — geração mecânica, não inventa cor. Nenhuma var de superfície/texto/brand nova.
- `ui-ux-pro-max` — editorial-técnica: cronômetro, valor da corrida (R$), distância (km), score (87,4), placa em **mono**; persimmon como única cor de ação (botão Aceitar). **Anti AI-slop:** sem gradiente, sem glow no card de oferta, sem confete ao aceitar, cronômetro com motion **com intenção** (não pulso neon decorativo).
- `ux-advanced/gesture-touch-patterns` — **sheet de oferta** entra de baixo (bottom-sheet Ionic), toque ≥44px no Aceitar; **sem** swipe-to-accept (aceite acidental = corrida perdida pra outro; o aceite é deliberado, botão grande). Recusar é toque explícito secundário. Tap-feedback scale .97 respeitando reduced-motion.
- `product/micro-animations-delight` + `ux-advanced/motion-design-patterns` — **cronômetro**: animação **com propósito** (aro/barra que esvazia, não pulso aleatório); aceleração visual nos últimos ~5s (cor → `--warning` → `--error`) reforçando urgência real; transição de entrada do sheet `motion.normal` `easing_out`; **toda** animação respeita `prefers-reduced-motion` (vira estado estático + texto). O cronômetro **nunca** é a fonte de verdade — é reforço sensorial do TTL do servidor.
- `mobile/push-notifications-architecture` — a oferta chega por **push (Web Push VAPID)**; UI cobre: notificação fora do app → tap abre o sheet; app aberto → sheet sobe direto; degrade silencioso se push indisponível (polling de oferta ativa). Sem badge/contador agressivo.
- `quality/error-ux-patterns` — F-05 E3 "essa entrega acabou de ser aceita" (`role="status"`, sem penalidade, sem culpa); oferta expirada (`role="status"`); falha de rede no aceite com retry idempotente. Erro = o que houve + o que fazer.
- `ux-advanced/empty-states-polish` — home "aguardando ofertas" (entregador online, fila vazia) com copy calma; favoritos/bloqueados vazios; loja sem entregadores na cascata (E1).
- `ux-advanced/data-tables-ux` — listas favoritos/bloqueados da Loja (tela 15) sobre `jx-data-table` (ou listagem governada): linhas com ação, estados loading/empty.
- `ux-advanced/search-filter-ux` — (leve) adicionar favorito por busca de entregador; não há filtro pesado nesta phase.
- `br/ux-copywriting-ptbr` — sentence case, CTA verbo+objeto sem ponto ("Aceitar entrega"), "Recusar", "Aguardando ofertas", "Essa entrega acabou de ser aceita por outro entregador. Sem problema — a próxima é sua.".
- `quality/accessibility-pro` — AA nos dois temas; **cronômetro não só visual** (`aria-live="polite"` no tempo, marcos sonoros/textuais, não cor-only); foco visível; touch ≥44px; sheet com `role="dialog"` + foco preso; score nunca só por cor (chip texto+nível).
- `quality/observability-production` — KPI "tempo até aceite" (gancho de UI; não é tela). Sem PII em log; `request_id`/`offer_id` não exibidos ao usuário.

---

## Telas / estados cobertos por esta fase

1. **§2 — Tela 04: Home do entregador (mobile, Ionic):** header + toggle online/offline (`jx-availability-toggle` reusado da Phase 6), estado **"aguardando ofertas"** (online, fila vazia), estado **offline**, gancho de **oferta ativa** (abre o sheet §3). Cards de ganhos/score/recentes do wireframe são read-only (dados de outras phases) — aqui só o que pertence ao despacho.
2. **§3 — Tela 05: `jx-offer-sheet` (sheet de oferta) — PEÇA CENTRAL:** cronômetro (`jx-offer-timer`, motion + aria-live), **origem** (coleta — endereço completo), **destino** (APENAS bairro + distância — RN-013), valor da corrida, botões **Aceitar** (≥44px) / **Recusar**, e os estados pós-decisão: **ganhou** (vai pra Phase 9), **perdeu a corrida** (F-05 E3), **expirou**.
3. **§4 — `jx-offer-timer` (cronômetro):** anatomia, motion, fases de urgência, a11y (aria-live + reduced-motion), e a regra "TTL do servidor é a verdade".
4. **§5 — Tela 15: Favoritos e bloqueados (Loja, web):** duas listas **separadas** (RN-014), adicionar/remover favorito + ordem de prioridade, bloquear/desbloquear (privado).
5. **§6 — `jx-accepted-courier-card`:** card do entregador que aceitou (nome, foto, placa em mono, `jx-score-chip` por `color.score_level`) — visível à Loja quando a entrega vira **ACEITA**.
6. **§7 — `jx-score-chip`** (novo, derivado de `color.score_level`); **§8 — Estados de exceção** (E1 cascata esgotada, oferta expirada, perdeu a corrida); **§8.4 — Acessibilidade**; **§9 — Tokens (Gate 2)**; **§10 — Visual regression**.

**Fora de escopo (deferido — NÃO especificar aqui):**
- **Coleta / comprovação foto+GPS / entrega / tracking** (ACEITA → COLETADA → ENTREGUE) → **Phase 9**. A entrega **para em ACEITA**. O endereço completo do destino **só** aparece após a coleta (Phase 9) — aqui é proibido por RN-013.
- **"Aceitou e sumiu"** (cancelamento por 2× ETA) → comportamento na **Phase 9**; aqui só o aceite.
- **Cobrança da corrida / fatura** → **Phase 10/11**.
- **Score com peso no ranking** → v1.1 (ADR-013; no M1 score é coletado e **exibido**, mas sem peso financeiro). O `jx-score-chip` exibe o nível; não há tela de cálculo aqui.
- **Mecânica da cascata** (arq job, Redis offer state) → backend; a UI só reage à **oferta ativa** que o servidor empurra.

---

## 1. Reuso do design system Phase 3/5/6/7 (não reinventar)

Esta phase **herda integralmente** o contrato visual. Não redefine temas, tipografia, motion nem componentes já existentes. Referências canônicas:

| Asset herdado | Arquivo real (apps/web) | Uso na Phase 8 |
|---|---|---|
| Temas claro/dark (21 vars semânticas) | `styles/_semantic.scss` | tudo consome `var(--surface)`, `var(--brand)`, etc. DEC-001 vale na home, no sheet, nas listas e no card do entregador. |
| Tokens primitivos `--jx-*` | `styles/_tokens.scss` (gerado de tokens.json) | nunca consumidos direto em componente. |
| Tipografia (escala + italic + mono) | `styles/typography.scss` | valor da corrida, distância, score, placa, cronômetro em **mono**; sem Fraunces no app do entregador (acento editorial é da Loja). |
| Anti-FOUC + toggle de tema | `index.html` + `core/theme/*` | tema ativo respeitado no app e no sheet. |
| **Shell Ionic do entregador** (tabs) | `layouts/entregador-shell.component.ts` | Início/Entregas/Ganhos/Perfil; a home (§2) entra na tab "Início". `--background`/`--color`/`--color-selected` já tokenizados. |
| **`jx-availability-toggle`** (online/offline, `role="switch"`, ≥44px, reduced-motion, revert no 409) | `features/entregador/disponibilidade/availability-toggle.component.ts` | **a peça reusada na home** (§2.2). NÃO reimplementar o toggle. |
| **`jx-state-badge`** (7 estados, derivado de `color.delivery_state`) | `shared/components/state-badge/state-badge.component.ts` | estado **ACEITA** no card do entregador que aceitou (§6) e em qualquer status de entrega na Loja. |
| `jx-data-table` (header sticky, `aria-sort`, estados) | `shared/components/data-table/data-table.component.ts` | listas de favoritos/bloqueados da Loja (§5). |
| `jx-empty-state` | `shared/state/empty-state.component.ts` | home "aguardando ofertas"/offline; favoritos/bloqueados vazios; loja sem entregadores (E1). |
| `jx-error-state` (`role="alert"`) | `shared/state/error-state.component.ts` | falha de rede no aceite; falha ao carregar oferta. |
| `jx-warn-banner` (`role="status"`) | `shared/state/warn-banner.component.ts` | "essa entrega acabou de ser aceita"; "oferta expirada"; cascata esgotada na Loja. |
| `jx-loading-skeleton` | `shared/state/loading-skeleton.component.ts` | carregando dados da oferta; processando aceite. |
| Money helper | `shared/util/money.ts` | `formatBrl` para o valor da corrida. |
| `home atual do entregador` | `features/entregador/inicio.page.ts` | base da §2 — substitui o empty-state genérico pelos estados de despacho. |

**Novos componentes compartilháveis desta phase** (governança `component-library-governance`, ganham story + baseline §10):
- **`jx-offer-sheet`** — bottom-sheet de oferta (tela 05). Orquestra cronômetro + origem + destino (bairro+distância) + valor + Aceitar/Recusar + estados pós-decisão. `role="dialog"`.
- **`jx-offer-timer`** — cronômetro **cosmético** (aro/barra que esvazia + texto mono em segundos) com fases de urgência por `color.semantic` e `aria-live`. **Não decide expiração** (servidor decide).
- **`jx-favorite-row`** — linha de favorito (posição · nome · `jx-score-chip` · stats · mover ↑↓ · remover).
- **`jx-blocked-row`** — linha de bloqueado (nome · data/motivo privado · desbloquear).
- **`jx-accepted-courier-card`** — card do entregador que aceitou (foto · nome · placa mono · `jx-score-chip` · `jx-state-badge` ACEITA).
- **`jx-score-chip`** — chip de nível de score (probation/bronze/prata/ouro/diamante), derivado de `color.score_level`. Texto (nível) + valor mono + cor — nunca cor-only.

**Vars semânticas novas:** apenas **5 vars de score** derivadas de `color.score_level` (§7.1) — adicionadas em `_semantic.scss`/`_tokens.scss` a partir do bloco `color.score_level` **já existente** em tokens.json (mesmo padrão das 7 `--state-*` da Phase 7). **Nenhuma** var de superfície/texto/brand nova. As 7 `--state-*` já existem.

---

## 2. Tela 04 — Home do entregador (F-05, mobile Ionic, gesture-touch)

Superfície **Entregador**. Rota `/entregador/inicio` (tab "Início" do shell Ionic). Mobile-first, `ion-content`, padding `--jx-space-4` (16). Estrutura do wireframe 04: header (saudação + toggle) → cards (ganhos/score/recentes, read-only de outras phases) → **estado de despacho** (a parte desta phase).

### 2.1 Header

- **Saudação:** "Bom dia, **{nome}**" — label `font.size.xs` (12) `--text-muted` + nome `font.size.md` (16) weight 600. (Do wireframe.)
- **Toggle online/offline:** à direita do header — **`jx-availability-toggle` reusado** (§2.2). NÃO recriar a pílula `.toggle-on/.toggle-off` do wireframe; o componente da Phase 6 já entrega isso com a11y completa.

### 2.2 Toggle online/offline (REUSO `jx-availability-toggle` — Phase 6)

- Componente existente: `role="switch"` + `aria-checked`, estado por **texto + ícone + posição** (nunca cor-only), `aria-live` no rótulo, **≥44px**, `revert()` no 409, reduced-motion respeitado.
- **Regra de despacho:** entregador **só recebe ofertas se online** (D-01 — elegíveis = online). Offline → nenhuma oferta entra; o estado de despacho (§2.3) mostra "Você está offline". Entregador **não-ativo** (KYC incompleto, Phase 5) → o toggle já vem `disabled` com `jx-warn-banner` "Termine sua validação…" (comportamento herdado, não re-especificar).
- **`busy`** (já em uma entrega ACEITA): nesta phase o entregador que aceitou sai do pool da cascata (D-05). UI: toggle permanece online, mas o estado de despacho mostra "Você está em uma entrega" (sem nova oferta até liberar — execução é Phase 9). Estado read-only aqui.

### 2.3 Estado de despacho (o que esta phase adiciona à home)

Bloco abaixo dos cards, que reflete a situação do entregador no fluxo de oferta. Substitui o `jx-empty-state` genérico atual (`inicio.page.ts`). Quatro estados mutuamente exclusivos:

| Estado | Gatilho | UI |
|---|---|---|
| **Offline** | toggle off | `jx-empty-state` calmo: ícone 🛵, "Você está offline", "Fique online para receber ofertas da sua área." Sem ansiedade. |
| **Aguardando ofertas** | online, sem oferta ativa | `jx-empty-state`: "Aguardando ofertas", "As corridas da sua área aparecem aqui assim que surgirem." Indicador de atividade **discreto** (ponto pulsando lento `--success`, `motion.slow`, **reduced-motion → estático**). NÃO spinner agressivo. |
| **Oferta ativa** | servidor empurrou uma oferta (push/polling) | o **`jx-offer-sheet` (§3) sobe** sobre a home (bottom-sheet). A home por baixo fica inerte (foco preso no sheet). Se o entregador estava com a tela fechada, o **push** abre o app no sheet. |
| **Em uma entrega** | `busy` (aceitou, Phase 9 assume) | card read-only "Você está em uma entrega — {bairro destino}" + link "Ver entrega" (rota Phase 9). Sem nova oferta. |

- **gesture-touch:** o sheet de oferta é a única superfície gestual desta phase; a home em si é scroll vertical padrão Ionic. Pull-to-refresh opcional na home para reconsultar oferta ativa (degrade do polling), `motion.normal`.

---

## 3. Tela 05 — `jx-offer-sheet` (sheet de oferta) — PEÇA CENTRAL (F-05, RN-013, D-04)

Superfície **Entregador**. Bottom-sheet modal (`role="dialog"`, `aria-modal="true"`, `aria-labelledby`) que sobe de baixo sobre a home. Largura total (mobile), `max-width` 420px centralizado, topo arredondado `radius.xl` (16, do wireframe `border-radius:20px` → adotamos token `xl`), fundo `--surface`, sombra `--shadow-lg`, padding `--jx-space-5` (20→24). Entra com `transform: translateY` `motion.normal` `easing_out` (**reduced-motion → sem deslize, aparece estático**). Foco inicial no título; foco **preso**; **Esc não fecha** (a oferta exige decisão explícita — recusar é o caminho de saída, não dismiss acidental).

### 3.1 Cabeçalho do sheet

- **Overline:** "NOVA OFERTA" — `font.size.2xs` (11) weight 700 uppercase letter-spacing .1em `--brand`. (Do wireframe.)
- **Cronômetro:** à direita do overline — **`jx-offer-timer` (§4)**. `aria-live="polite"`.
- **Título (loja):** nome da loja — `font.size.xl` (22) weight 600, -.02em, `--text`. (Ex.: "Pizzaria do José".)
- **Afinidade (opcional):** se o entregador já entregou pra essa loja, micro-linha `font.size.xs` `--text-muted`: "⭐ Você já entregou {N} vezes pra essa loja". Reforça contexto, não é obrigatório.

### 3.2 Origem (coleta) e destino (RN-013 — privacidade crítica)

Dois "stops" empilhados (do wireframe `.stop a` / `.stop b`):

| Stop | Conteúdo PERMITIDO | Cor / pino | Privacidade |
|---|---|---|---|
| **A — Coleta** | **Endereço COMPLETO** da coleta (rua, número · bairro). Ex.: "Rua das Flores, 123 · Centro" | pino `--text` (neutro escuro), fundo `--surface-elevated`, overline "COLETA" `--text-muted` | endereço da loja, não é PII de destinatário; pode ser completo (D-04). |
| **B — Entrega** | **APENAS bairro + distância** — Ex.: "Vila Nova · ~2,8 km" + microcopy "(endereço completo após a coleta)" | pino `--brand`, fundo `--brand-wash`, borda `--brand-wash-border`, overline "ENTREGA" `--brand-hover` | **RN-013 — NUNCA** rua/número/CEP/nome/telefone do destinatário. O payload da oferta **não contém** esses campos (teste de contrato no ROADMAP). |

- **Regra inviolável (RN-013):** o componente recebe do backend só `{ bairro, distancia_km }` para o destino. Se algum dado completo vazar no payload, é **bug de privacidade bloqueante** — a UI nunca renderiza rua/número/destinatário do destino nesta phase. O endereço completo é revelado só após COLETADA (Phase 9).
- **Distância:** em **mono**, `~{X,X} km` (vírgula decimal pt-BR). `~` sinaliza estimativa (OSRM em rota; se `eta_degraded`, ainda mostra valor — degrade silencioso, sem alarmar o entregador).

### 3.3 Valor da corrida + metadados

Faixa `.meta` (do wireframe), borda topo/baixo `--border`, padding `--jx-space-3`:

- **Valor da corrida:** "Você ganha **R$ 8,50**" — valor em **mono** `font.size.2xl` (28→26) weight 800 `--brand` (`formatBrl`). É o número que decide o aceite; é o elemento mais proeminente depois do cronômetro.
- **Distância:** "2,8 km" mono `font.size.sm` `--text-muted`.
- **ETA:** "~15 min" mono `font.size.sm` `--text-muted`. Se `eta_degraded`, sem badge ruidoso (degrade silencioso).
- **Modalidade de pagamento:** badge "PAGAMENTO DIRETO 💵" — `font.size.2xs` weight 700, fundo `--warning-bg`, texto `--warning` (ou `--brand-wash`/`--brand-hover`). Sinaliza que o entregador recebe direto (RN-023). Sem valor de cobrança aqui (cobrança = Phase 10).

### 3.4 Aceitar / Recusar (gesture-touch, D-05)

- **Aceitar entrega (CTA primário):** botão **full-width**, `--brand`/`--brand-contrast`, radius `lg` (10), weight 700, `font.size.md` (16), **altura ≥44px** (na verdade ~52px — alvo generoso, decisão sob pressão de tempo). Tap-feedback scale .97 `motion.fast` (**reduced-motion → sem scale**). **Sem swipe-to-accept** (gesture-touch: aceite acidental custaria a corrida; o aceite é toque deliberado).
- **Recusar (secundário):** botão full-width outline `--border-strong`/`--text-muted`, transparente, abaixo do Aceitar, ≥44px. Recusar → próximo da cascata (servidor); UI fecha o sheet sem culpa, volta a "aguardando ofertas".
- **Estado processando aceite:** ao tocar Aceitar → botão entra em `aria-busy`, label "Aceitando…", `jx-loading-skeleton` leve; cronômetro pausa visualmente. O **lock transacional** (D-05) decide no servidor. Idempotente: toque duplo não cria duas ações.

### 3.5 Estados pós-decisão (F-05 E3 — aceite único)

O sheet resolve em um de três estados terminais, anunciados via live region:

| Resultado | Gatilho | UI (dentro do sheet, substitui os botões) |
|---|---|---|
| **Ganhou** | lock concedido → entrega ACEITA | feedback discreto `role="status"` `--success`: "Entrega aceita! Vá até a coleta." + CTA "Ver entrega" (rota Phase 9). **Sem confete** (anti-slop). Sheet fecha em ~1,5s ou ao tocar. |
| **Perdeu a corrida (E3)** | dois aceites simultâneos, este é o 2º | `jx-warn-banner` `role="status"` (NÃO `alert`, NÃO erro): **"Essa entrega acabou de ser aceita por outro entregador. Sem problema — a próxima é sua."** (texto do wireframe). **Sem penalidade, sem culpa.** Botão "Ok" / fecha sozinho. Volta a "aguardando ofertas". |
| **Expirou** | TTL do servidor estourou antes do aceite | `jx-warn-banner` `role="status"`: "Essa oferta expirou. Já estamos buscando a próxima pra você." Fecha, volta a "aguardando". |

- **Falha de rede no aceite:** `jx-error-state` `role="alert"` "Não deu pra confirmar agora. Tentar de novo." + retry **idempotente** (mesmo `offer_id`; se outro já levou, cai no estado "perdeu a corrida" — nunca aceita em duplicidade).
- **Regra ADR-104:** o cliente **nunca** declara "expirou" sozinho — só exibe "expirou" quando o **servidor** confirma (o cronômetro zerar é dica visual; a confirmação vem do backend). Se o relógio local zera mas o servidor ainda aceita, o aceite **vale** (servidor é a verdade). Cf. §4.4.

---

## 4. `jx-offer-timer` — cronômetro (motion-design + micro-animations + a11y) — NOVO

O elemento que dá tensão à oferta. **Cosmético por contrato (ADR-104).** Motion com intenção, não AI-slop.

### 4.1 Anatomia

- **Texto:** "⏱ {N}s" em **mono** (`font.family.mono`) `font.size.sm` (13→15) weight 700. O número de segundos é a informação acessível primária. (Do wireframe `.timer`.)
- **Indicador visual:** aro circular **ou** barra fina que **esvazia** proporcional ao tempo restante (de 100% → 0%). Cor segue as fases (§4.2). O esvaziamento é a metáfora ("tempo escoando"), não um pulso decorativo.
- **Posição:** topo-direita do sheet, alinhado ao overline "NOVA OFERTA".

### 4.2 Fases de urgência (color.semantic — motion com propósito)

| Fase | Faixa (do TTL configurável 10-60s, default 20s) | Cor do aro/texto | Motion |
|---|---|---|---|
| **Calmo** | > ~50% restante | `--text-muted` / `--info` | esvaziamento linear suave |
| **Atenção** | ~50%–25% | `--warning` | esvaziamento contínuo |
| **Urgente** | < ~25% (≈ últimos 5s no default) | `--error` | esvaziamento + leve aceleração visual (NÃO piscar epilético; transição de cor `motion.fast`) |

- **Anti AI-slop:** sem glow neon, sem pulsar aleatório, sem som estridente. A aceleração de cor nos últimos segundos reforça urgência **real** (o TTL de fato acabando), não decoração.
- A duração total vem da **config da área** (D-03), não hardcoded. O componente recebe `ttl_total` e `ttl_restante` do servidor.

### 4.3 Acessibilidade do cronômetro (accessibility-pro — crítico)

- **Não só visual:** o tempo é anunciado por **`aria-live="polite"`** (do wireframe). Não anunciar a cada segundo (verborrágico) — anunciar em **marcos**: ao abrir ("18 segundos para decidir"), em 10s, em 5s, e ao expirar. Texto sempre presente (não cor-only).
- **`prefers-reduced-motion`:** sem animação de esvaziamento/aceleração — vira **contagem textual estática** que atualiza o número (mono) + mudança de cor por fase (cor é reforço, não única pista; o número é a verdade). Cf. `motion-design-patterns`.
- **Cor + texto + forma:** a urgência é sinalizada por **cor (semantic)** E **número decrescente** E **aro esvaziando** — nunca só cor (daltonismo).
- **Foco:** o cronômetro não é interativo (não recebe foco); é `aria-live`. O foco fica nos botões Aceitar/Recusar.

### 4.4 Regra de verdade (ADR-104) — cronômetro é cosmético

- O **Redis TTL no servidor é a fonte de verdade**. O `jx-offer-timer` é um espelho **otimista** do tempo restante que o servidor informou; **nunca** decide expiração sozinho.
- **Divergência (clock skew / latência):** se o cronômetro local zera mas o servidor ainda aceita → o aceite **vale** (servidor decide). Se o servidor expira antes do cronômetro local → ao tocar Aceitar, o sheet cai no estado "expirou" (§3.5). A UI nunca trava o entregador num estado que contradiz o servidor.
- **Re-sync:** ao receber resposta do servidor (heartbeat/polling), o cronômetro **corrige** seu valor para o `ttl_restante` autoritativo (sem "pulo" brusco — interpola em `motion.fast`).

---

## 5. Tela 15 — Favoritos e bloqueados (Loja, web, RN-014, D-06)

Superfície **Loja** (web, sob `loja-shell`). Rota `/loja/favoritos`. `<main>` `max-width` ~720px (do wireframe). **Duas listas SEPARADAS** (RN-014) — favoritos e bloqueados são entidades distintas (`merchant_courier_favorites` / `merchant_courier_blocks`).

- **Intro (hint):** `font.size.sm` (13) `--text-muted`: "Favoritos recebem suas ofertas primeiro (um por vez, {timeout}s cada). Bloqueados nunca recebem suas ofertas — a lista é privada e não afeta o score de ninguém." (RN-014: bloqueio é privado e não penaliza o entregador.) O `{timeout}` vem da config da área (Phase 6), não hardcoded.

### 5.1 Lista de favoritos (`jx-favorite-row`, ordem de prioridade)

Card `--surface-elevated`, borda `--border`, radius `lg`. Título "⭐ Favoritos (ordem de prioridade)" `font.size.md` (16) weight 600.

- **Linha (`jx-favorite-row`):** posição (`1 ·`, mono) · nome (weight 600) · **`jx-score-chip`** (§7, ex. "★87 ouro" via `color.score_level`) · stats em **mono** `--text-muted` ("142 entregas pra você · 96% no prazo"). Ações à direita: **mover ↑** / **mover ↓** (reordenar prioridade da cascata — D-01) / **Remover** (`--error` outline). Todas as ações ≥44px.
- **Ordem importa (D-01):** a posição define a ordem na cascata de favoritos. Mover ↑/↓ persiste a prioridade; primeiro/último com a respectiva seta `disabled` (`aria-disabled`).
- **Adicionar favorito (search-filter-ux leve):** ação "Adicionar favorito" → busca de entregador que já entregou pra loja (nome). Não há marketplace aberto de entregadores (privacidade ADR-007); favorita-se quem já atendeu (do wireframe: "Marque a estrela em qualquer entrega concluída").
- **Empty:** `jx-empty-state` "Você ainda não tem favoritos. Marque a estrela em qualquer entrega concluída."
- **Remover:** confirmação leve (não modal pesado): "Remover {nome} dos favoritos? Ele ainda pode receber ofertas pelo ranking automático." + "Remover" (`--error`) / "Voltar". Remover de favoritos **≠** bloquear (deixa claro).

### 5.2 Lista de bloqueados (`jx-blocked-row`)

Card separado. Título "🚫 Bloqueados" `font.size.md` weight 600.

- **Linha (`jx-blocked-row`):** nome (weight 600) · linha de detalhe `font.size.sm` `--text-muted` "bloqueado em {dd/MM} — motivo (privado): {motivo}". Ação **Desbloquear** (outline neutro, ≥44px).
- **Privacidade (RN-014):** o motivo é **privado da loja** (nunca exibido ao entregador, nunca afeta o score). Bloqueado **nunca** entra na cascata daquela loja (nem favoritos nem ranking).
- **Bloquear:** ação disponível a partir de uma entrega concluída / do perfil do entregador (gancho leve aqui). Confirmação: "Bloquear {nome}? Ele não receberá mais ofertas da sua loja. Isso é privado e não afeta o score dele." + "Bloquear" (`--error`) / "Voltar".
- **Empty:** `jx-empty-state` "Nenhum entregador bloqueado."

- **Sobre `jx-data-table`:** as duas listas usam o primitivo governado (`jx-data-table` ou listagem governada equivalente) para herdar estados loading/empty/error, `aria` e teclado. Loading = skeleton de linhas; error = `jx-error-state` + retry.

---

## 6. `jx-accepted-courier-card` — entregador que aceitou (D-05) — visível à Loja

Quando a entrega vira **ACEITA** (lock concedido), a Loja vê **quem** aceitou. Card exibido no detalhe/dashboard da entrega (a tela de detalhe completa é Phase 8/9; aqui especificamos o **card**, reutilizável).

- **Anatomia:** card `--surface-elevated`, borda `--border`, radius `lg`, padding `--jx-space-4`. Linha: **foto** (avatar circular `radius.full`, do cadastro Phase 5; fallback iniciais sobre `--surface-sunken` se sem foto) · **nome** (weight 600, `font.size.md`) · **placa** em **mono** `font.size.sm` `--text-muted` (ex.: "ABC-1D23") · **`jx-score-chip`** (§7) · **`jx-state-badge`** estado **ACEITA** (variant `dashboard` = "Indo coletar", ou `list` = "Aceita").
- **Privacidade reversa (ADR-007):** a Loja vê **identidade do entregador que aceitou** (nome/foto/placa/score — necessário para confiança e contato pós-aceite). A Loja **NUNCA** vê a localização em tempo real do entregador nesta phase (tracking é Phase 9, e mesmo lá com regra). A localização dos entregadores **online** (antes do aceite) nunca é exposta.
- **Dados:** vêm do perfil do entregador (Phase 5). Foto/placa são dados do entregador, não PII de destinatário; exibição à loja é parte do contrato de confiança.
- **Estado pré-aceite:** enquanto CRIADA (procurando), no lugar do card aparece o estado "Procurando entregador…" (reusa `jx-state-badge` CRIADA + texto), sem identidade (ninguém aceitou ainda).

---

## 7. `jx-score-chip` — chip de nível de score (color.score_level) — NOVO

Chip que mostra o nível de score do entregador. Reutilizado em favoritos (§5.1) e no card do aceito (§6). **Score sem peso no ranking no M1 (ADR-013)** — aqui é só **exibição**.

### 7.1 Os 5 níveis e suas cores (`color.score_level`)

Cada nível mapeia 1:1 para `color.score_level.*` de tokens.json. Cria-se uma var semântica por nível (`--score-{nivel}`) derivada do primitivo `--jx-score-{nivel}` (gerado de `color.score_level`) — **mesmo padrão mecânico** das 7 `--state-*` da Phase 7. **Nunca só por cor** → chip tem **texto (nível) + valor mono + cor**.

| Nível | Token cor (`color.score_level.*`) | Hex | Var semântica | Rótulo pt-BR |
|---|---|---|---|---|
| `probation` | `color.score_level.probation` | #9D8E7A | `--score-probation` | "em avaliação" |
| `bronze` | `color.score_level.bronze` | #A66D2F | `--score-bronze` | "bronze" |
| `prata` | `color.score_level.prata` | #7E7B73 | `--score-prata` | "prata" |
| `ouro` | `color.score_level.ouro` | #D4A017 | `--score-ouro` | "ouro" |
| `diamante` | `color.score_level.diamante` | #1B998B | `--score-diamante` | "diamante" |

### 7.2 Anatomia (texto + valor + cor — a11y)

- **Chip:** pílula `radius.full`, padding `--jx-space-1`/`--jx-space-2`, `font.size.2xs`/`xs`. Conteúdo: glifo "★" (`aria-hidden`) + **valor em mono** (ex. "87,4" ou "87") + **rótulo do nível** (texto, ex. "ouro"). Cor do texto/glifo = `--score-{nivel}`.
- **Fundo:** `--surface-sunken` (neutro) com texto/glifo na `--score-{nivel}` viva — mesmo padrão "superfície neutra + cor viva" das `--state-*` (funciona AA nos dois temas; evita 5 tokens `_bg` novos). **`prata` (#7E7B73)** e **`probation` (#9D8E7A)** são neutros baixos — o checker valida AA sobre `--surface-sunken`; no dark, lift para neutral mais claro se necessário (mesmo tratamento de `--state-criada`/`--state-cancelada`).
- **Nunca cor-only:** o nível é sempre **escrito** ("ouro"), nunca só a cor da pílula. O valor numérico é mono.
- **Dark:** texto na `--score-{nivel}`; checker valida contraste sobre `--surface-elevated`/`--surface-sunken`.

---

## 8. Estados de exceção (F-05 E1-E4) + Acessibilidade

### 8.1 E1 — Cascata esgotada sem aceite (Loja, F-05 E1, D-07)

Quando favoritos + ranking esgotam sem ninguém aceitar:

- **UI (Loja):** `jx-warn-banner` `role="status"` no detalhe/dashboard da entrega: "Ninguém aceitou ainda. O que você quer fazer?" + **3 opções de igual peso** (anti-dark-pattern, sem forçar a mais cara):
  1. **Aumentar o frete e reofertar** → ação que sobe o valor e reinicia a cascata (re-oferta). Copy: "Aumentar frete e chamar de novo".
  2. **Aguardar e tentar de novo** → re-cascata em ~2min (D-07). Copy: "Aguardar e tentar em 2 min".
  3. **Cancelar sem custo** → "Como ninguém aceitou, não há cobrança." (RN-004). Botão `--error` outline.
- Estado calmo, não alarmista: a entrega não falhou, só precisa de decisão. `jx-empty-state`/`warn-banner`, não `error-state`.

### 8.2 Oferta expirada (Entregador) — §3.5

Coberto no `jx-offer-sheet` §3.5: `jx-warn-banner` `role="status"` "Essa oferta expirou. Já estamos buscando a próxima pra você." Sem penalidade. Volta a "aguardando ofertas".

### 8.3 Perdeu a corrida (Entregador, E3) — §3.5

Coberto no `jx-offer-sheet` §3.5: "Essa entrega acabou de ser aceita por outro entregador. Sem problema — a próxima é sua." `role="status"`, sem culpa, sem penalidade (F-05 E3). **Este é o estado mais sensível da phase** — o tom NUNCA pune o entregador que perdeu a corrida de rede.

### 8.4 E4 — Loja cancela durante a cascata (D-07)

- Loja cancela uma entrega CRIADA durante a cascata → ofertas pendentes canceladas, **sem custo** (só cobra após aceite, RN-004). UI: confirmação leve (reusa o padrão de cancelar CRIADA da Phase 7) "Cancelar a entrega? Ninguém aceitou ainda, então não há cobrança." Entregadores com oferta pendente: o sheet some/cai em "oferta expirada" (servidor cancela a oferta).

### 8.5 Acessibilidade (accessibility-pro — AA dois temas, DEC-001)

- **Contraste AA nos DOIS temas:** herda mapas da Phase 3. **5 cores de score** (`color.score_level`) e **estado ACEITA** validados claro+dark sobre a superfície do chip/badge (`--surface-sunken`/`--surface-elevated`) pelo checker (axe + contraste). Sheet, cronômetro, botões e card também.
- **Cronômetro não-só-visual (§4.3):** `aria-live="polite"` por marcos (abrir/10s/5s/expirar), número mono sempre presente, cor + número + aro (nunca cor-only). `prefers-reduced-motion` → contagem estática.
- **Sheet acessível:** `role="dialog"` `aria-modal="true"` `aria-labelledby` (nome da loja); foco inicial no título; foco **preso**; saída só por Aceitar/Recusar (não Esc acidental). Resultado pós-decisão anunciado por `role="status"`.
- **Toggle (herdado):** `role="switch"` + `aria-checked`, texto+ícone+posição (já a11y completo na Phase 6).
- **Score/estado nunca só por cor:** `jx-score-chip` (texto do nível) e `jx-state-badge` (texto+ícone) sempre carregam o significado em texto.
- **Touch ≥44px:** Aceitar (~52px), Recusar, mover ↑↓, Remover, Desbloquear, opções da cascata esgotada, toggle online.
- **Foco visível:** `--focus-ring` (`shadow.focus`) em todo interativo. Nunca `outline:none` sem substituto.
- **Motion:** entrada do sheet, tap-feedback, cronômetro em `motion.fast/normal/slow` `easing_out`; **`prefers-reduced-motion`** → sem deslize/scale/esvaziamento animado (vira estático + texto).
- **`lang="pt-BR"`**, landmarks Ionic (`ion-content`, `ion-tabs`); listas da Loja sob `<main>`/`<table>`. `axe-core` na home, no sheet, nas listas e no card: zero violações críticas (verificação ROADMAP).

---

## 9. Tabela de tokens citados (Gate 2 — todos existem em `tokens.json`)

Cada token referenciado, com caminho em `docs/identidade-visual/tokens.json`. **Confirmado: 100% existem (zero inventados)** — incluindo os **5 `color.score_level`**, o estado **`color.delivery_state.aceita`** e os **4 `motion.*`** do cronômetro. As vars semânticas de superfície/texto/brand/semantic já estão em `_semantic.scss` (Phase 3); as 7 `--state-*` já existem (Phase 7).

| Token (caminho em tokens.json) | Valor | Existe? |
|---|---|---|
| **`color.score_level.probation`** | #9D8E7A | ✅ |
| **`color.score_level.bronze`** | #A66D2F | ✅ |
| **`color.score_level.prata`** | #7E7B73 | ✅ |
| **`color.score_level.ouro`** | #D4A017 | ✅ |
| **`color.score_level.diamante`** | #1B998B | ✅ |
| **`color.delivery_state.aceita`** (→ `--state-aceita`, card do aceito) | #0A66C2 | ✅ |
| **`color.delivery_state.criada`** (estado pré-aceite "procurando") | #6B5F50 | ✅ |
| **`motion.fast`** (cronômetro: transição de cor, re-sync, tap-feedback) | 140ms | ✅ |
| **`motion.normal`** (entrada do sheet, recálculo) | 220ms | ✅ |
| **`motion.slow`** (ponto pulsando "aguardando ofertas") | 380ms | ✅ |
| **`motion.easing_out`** (todas as transições) | cubic-bezier(0.16,1,0.3,1) | ✅ |
| `color.brand.50` (→ `--brand-wash`, stop B / chip) | #FFF1E8 | ✅ |
| `color.brand.100` (→ `--brand-wash-border`) | #FFDEC1 | ✅ |
| `color.brand.400` (brand dark) | #FB813D | ✅ |
| `color.brand.500` (→ `--brand`, CTA Aceitar / valor / pino B) | #E84E1B | ✅ |
| `color.brand.600` (→ `--brand-hover`) | #C73E0F | ✅ |
| `color.neutral.50` (→ `--surface` / `--brand-contrast`) | #FAF6EE | ✅ |
| `color.neutral.100` (→ `--surface-elevated`, cards) | #F2EBE0 | ✅ |
| `color.neutral.200` (→ `--surface-sunken` / `--border`, fundo do chip/badge) | #E5DBCC | ✅ |
| `color.neutral.300` (→ `--border-strong` / `--state-criada` dark) | #C8BAA5 | ✅ |
| `color.neutral.400` (→ `--text-subtle` / lift de score neutro no dark) | #9D8E7A | ✅ |
| `color.neutral.500` (→ `--text-muted`) | #6B5F50 | ✅ |
| `color.neutral.700`/`.800`/`.900` (text / superfície dark / fundo) | #2D261F / #181410 / #0A0805 | ✅ |
| `color.semantic.success` (→ `--success`, "aguardando"/"aceita!") | #1B998B | ✅ |
| `color.semantic.warning` (→ `--warning`, cronômetro fase atenção / badge direto) | #E89B0E | ✅ |
| `color.semantic.warning_bg` (→ `--warning-bg`) | #FFF1D2 | ✅ |
| `color.semantic.error` (→ `--error`, cronômetro fase urgente / remover / cancelar) | #C71D1D | ✅ |
| `color.semantic.error_bg` (→ `--error-bg`) | #F9DCDC | ✅ |
| `color.semantic.info` (→ `--info`, cronômetro fase calma) | #0A66C2 | ✅ |
| `spacing.1`/`.2`/`.3`/`.4`/`.5` (4/8/12/16/24px) | — | ✅ |
| `radius.lg` / `xl` / `full` (10/16/9999px — card / sheet topo / pílulas) | — | ✅ |
| `font.family.display` (Inter Tight — títulos/corpo) | Inter Tight… | ✅ |
| `font.family.mono` (cronômetro, valor R$, distância, score, placa) | JetBrains Mono… | ✅ |
| `font.size.2xs`/`xs`/`sm`/`base`/`md`/`xl`/`2xl` (11/12/13/14/16/22/28) | — | ✅ |
| `font.weight.regular`/`medium`/`semibold`/`bold`/`extrabold` (400/500/600/700/800) | — | ✅ |
| `shadow.lg` (→ `--shadow-lg`, sheet / cards) | rgba(24,20,16,…) | ✅ |
| `shadow.focus` (→ `--focus-ring`) | rgba(232,78,27,.28) | ✅ |

**Tokens referenciados que NÃO existem em tokens.json: NENHUM (0).** Os **5 `color.score_level`**, o **`color.delivery_state.aceita`** e os **4 `motion.*`** existem e são usados literalmente. Nenhuma var de superfície/texto/brand nova; as únicas vars novas são as **5 `--score-*`** derivadas de `color.score_level` (geração mecânica, mesmo padrão das `--state-*`). Gate 2 satisfeito.

> **Nota para o executor:** `color.score_level` ainda **não** está mapeado em `apps/web/src/styles/_semantic.scss` (só `color.delivery_state` está). O plan/execute desta phase **deve** adicionar os 5 primitivos `--jx-score-*` em `_tokens.scss` e as 5 vars `--score-*` (claro + `@mixin jx-dark-theme`) em `_semantic.scss`, derivando mecanicamente de `color.score_level` — exatamente como as `--state-*` foram derivadas de `color.delivery_state` na Phase 7. Nenhuma cor inventada.

---

## 10. Visual regression (baseline desta phase)

Novos componentes/telas que recebem story + baseline (`product/visual-regression-testing`):

- [ ] `jx-offer-sheet` — stories: oferta-ativa, processando-aceite, **ganhou**, **perdeu-corrida (E3)**, **expirou**, falha-rede · claro+dark · mobile
- [ ] `jx-offer-timer` — stories: fase calma (>50%), atenção (~40%), **urgente (<25%)**, expirado, **reduced-motion (estático)** · claro+dark
- [ ] `jx-score-chip` — stories: **todos os 5 níveis** (probation/bronze/prata/ouro/diamante) · claro+dark
- [ ] `jx-accepted-courier-card` — stories: com-foto, sem-foto (iniciais), estado ACEITA · claro+dark
- [ ] `jx-favorite-row` — stories: primeiro (↑ disabled), meio, último (↓ disabled), confirmar-remover · claro+dark
- [ ] `jx-blocked-row` — stories: com-motivo, confirmar-desbloquear · claro+dark
- [ ] `entregador-home` (tela 04) — stories: offline, **aguardando-ofertas**, em-uma-entrega, toggle-disabled (KYC) · claro+dark · mobile
- [ ] `loja-favoritos` (tela 15) — stories: com-favoritos+bloqueados, favoritos-vazio, bloqueados-vazio, loading · claro+dark
- [ ] `cascata-esgotada` (E1, Loja) — stories: 3-opções (aumentar frete / aguardar / cancelar) · claro+dark

Nome screenshot: `{component}-{state}-{theme}-{viewport}.png`.

---

## 11. Open questions para o humano

- [ ] **Forma do cronômetro (aro vs barra):** modelei aro circular **ou** barra que esvazia (§4.1), ambos válidos. **Recomendação:** aro circular ao redor do número (compacto no topo do sheet, metáfora "relógio"). Confirmar preferência.
- [ ] **Marcos de anúncio do `aria-live`:** modelei abrir/10s/5s/expirar (§4.3) para não ser verborrágico. Confirmar se o entregador com leitor de tela quer mais granularidade (ex. a cada 5s).
- [ ] **Esc no sheet:** modelei **Esc NÃO fecha** (oferta exige decisão; recusar é o caminho). Confirmar — alternativa seria Esc = recusar explícito.
- [ ] **Rótulo do score-chip:** modelei "★{valor} {nível}" (ex. "★87 ouro"). Confirmar se a Loja prefere só nível ("ouro") ou só valor ("87,4") em alguns contextos.
- [ ] **Reordenar favoritos (↑↓ vs drag):** modelei botões ↑↓ (acessível por teclado, ≥44px) em vez de drag-and-drop (gesture frágil + a11y difícil). **Recomendação:** manter ↑↓. Confirmar.

---

## Approval

- [ ] Humano revisou e aprovou (ou delegou ao ui-checker)
- [ ] ui-checker validou 6 dimensões: tokens, tipografia, copy, estados, interações, acessibilidade
- [ ] Gate 2 (Visual Contract) verde — tokens citados existem em tokens.json (§9), incluindo os 5 `color.score_level`, `color.delivery_state.aceita` e os 4 `motion.*`
- [ ] Wireframe-contract de `04-entregador-home.html`, `05-entregador-oferta.html`, `15-loja-favoritos.html` coberto; coleta/comprovação (Phase 9) e cobrança (Phase 10) ficam fora
- [ ] RN-013 verificada: nenhuma tela renderiza endereço completo/destinatário do destino (só bairro+distância)
- [ ] Aprovado em: {date}

**Próximo passo:** `/gsd:plan-phase 8` — o planner recebe este UI-SPEC como contrato de design.
