---
phase: 07-cria-o-de-entrega-m-quina-de-estados-modalidade-direta
title: Criação de entrega + máquina de estados (modalidade direta)
status: draft
platform: web (superfície Loja — desktop-first, responsivo até mobile)
gate2_visual_contract: pending-checker
generated_by: gsd-ui-researcher
generated_at: 2026-06-10
reuses: 03-shell-frontend-design-system-3-superf-cies, 04-cadastro-e-ativa-o-de-loja, 06-rea-oper-vel-bairros-config-cobertura-e-tabela-de-frete
---

# UI-SPEC — Phase 7: Criação de entrega + máquina de estados (modalidade direta)

> Design contract da Phase 7 (Gate 2 — Visual Contract). **BLOQUEIA** `plan-phase` se não existir.
> Superfície: **Loja** (web desktop-first, responsivo até mobile — o dono/operador cria entregas do balcão, em desktop ou celular).
> **Regra de ouro Gate 2:** todo valor visual é token. Nenhum `#hex` hardcoded. Todo token/var citado existe em `docs/identidade-visual/tokens.json` (§7) ou na camada semântica da Phase 3 (`apps/web/src/styles/_semantic.scss`).
> **Princípio desta phase:** *reusar*, não reinventar. Temas claro/dark (DEC-001), tipografia, motion, 4 componentes de estado, `jx-field`, `jx-data-table`, `jx-plan-card` e o padrão de form BR **já existem** (Phases 3/4/6). Aqui especificamos só o **novo**: o **form de nova entrega** (tela 12), o **`jx-state-badge`** (badge dos 7 estados da entrega — reutilizável em várias telas), a **linha/card de entrega** sobre `jx-data-table` (telas 14 e 11) e o **`jx-upgrade-modal`** (limite de plano, sem dark pattern).
> **`has_pii: true`** — destinatário (nome, telefone E.164) é PII. Telefone mascarado na exibição em lista; CPF nunca puro (hash — D-08). Ver §6 (LGPD + a11y).

---

## Fontes de verdade consultadas

- `.planning/phases/07-.../07-CONTEXT.md` — decisões **D-01..D-08** (form de entrega F-03, pagamento direto RN-023, 7 estados RN-019, transições append-only RN-012, estimativa mediana RN-030, exceções E1/E2/E4, limite de plano RN-028, recipients/LGPD D-08).
- `docs/identidade-visual/tokens.json` — tokens **canônicos** (FONTE da verdade visual). **`color.delivery_state`** traz as 7 cores dos estados (§3, §7) — usadas literalmente.
- `.planning/phases/03-.../UI-SPEC.md` — design system (21 vars semânticas claro/dark, tipografia, motion, 4 componentes de estado). Contrato herdado.
- `.planning/phases/04-.../UI-SPEC.md` — padrão de form BR (`jx-field`, máscara monetária/telefone, erros acionáveis, shell da Loja).
- `.planning/phases/06-.../UI-SPEC.md` — **`jx-data-table`** (primitivo de tabela governado, header sticky, `aria-sort`, estados embutidos) + catálogo de bairros (autocomplete de bairro) + estimativa pela elegibilidade espacial. Reusamos integralmente.
- `apps/web/src/` — código real a reusar: `shared/state/*` (4 estados), `shared/components/field/*` (`jx-field`), `shared/components/data-table/*` (`jx-data-table`), `shared/components/plan-card/*` (`jx-plan-card`), `features/loja/cadastro/br-format.ts` (`maskPhone`/`phoneToE164`/`maskCep`/`isCepComplete`), `shared/util/money.ts` (`maskBrl`/`parseBrl`/`formatBrl`), `core/theme/*`, `styles/_semantic.scss` + `_tokens.scss`, `layouts/loja-shell.component.ts`.
- `projeto/wireframes/12-loja-nova-entrega.html`, `11-loja-dashboard.html`, `14-loja-entregas.html` — contratos DOM (lidos linha a linha).
- `projeto/regras-negocio/fluxos.md` §F-03 (`:51-69`) — criação + exceções E1/E2/E4. `regras.md` RN-019/023/028/030.
- `.planning/ROADMAP.md` Phase 7 — flags (has_ui, has_api, has_pii:true, has_payments:false, integration_check:false) + skills obrigatórias.

### Skills aplicadas (matriz UI + flags Phase 7)

- `product/component-library-governance` — **reusar** `jx-field`, `jx-data-table`, `jx-plan-card`, 4 estados. Novos componentes governados (story + baseline §8): **`jx-state-badge`** (7 estados da entrega, texto+ícone+cor), **`jx-delivery-row`** (célula de linha de entrega), **`jx-estimate-box`** (frete estimado + taxa antes de confirmar), **`jx-upgrade-modal`** (limite de plano, anti-dark-pattern).
- `ux-advanced/design-tokens-system` — consumir só camada semântica (`var(--surface)`, `var(--brand)`) + as 7 vars de estado derivadas de `color.delivery_state` (§3.1). Nenhuma var de superfície/texto nova.
- `ui-ux-pro-max` — editorial-técnica: nº da entrega (`#2851`), telefone, valores R$, frete, taxa, data/hora em **mono**; Fraunces italic em 1 palavra-chave do H1 do dashboard; persimmon como única cor de ação. **Anti AI-slop:** sem gradiente, sem card "glow", sem badge neon, sem confete ao criar entrega.
- `br/brazilian-forms` — **máscara de telefone** `(DD) 9XXXX-XXXX` → E.164 (`maskPhone`/`phoneToE164`), **CEP** `00000-000` (`maskCep`), **valor declarado** monetário `R$ 0,00` (`maskBrl`), `inputmode` correto, NUNCA `type="number"` para dinheiro/telefone.
- `ux-advanced/form-ux-mastery` — seções por `fieldset`, validação inline no blur, um erro por campo via `aria-describedby`, CTA habilita só com form válido, estimativa visível **antes** de confirmar.
- `quality/error-ux-patterns` — `jx-error-state` `role="alert"` para fora-de-área (E1) e limite de plano (E4); `jx-warn-banner` `role="status"` não-bloqueante para 0 entregadores (E2). Erro = o que houve + o que fazer.
- `ux-advanced/saas-dashboard-patterns` — dashboard da Loja (tela 11) com KPIs em mono + tabela "em curso"; lista de entregas (tela 14) densa com filtro.
- `ux-advanced/data-tables-ux` — lista de entregas (tela 14) e "em curso" (tela 11) sobre `jx-data-table`: filtro por estado, badge de estado, ação por linha (cancelar/ver), estados loading/empty/error.
- `ux-advanced/search-filter-ux` — filtro por estado/pagamento/período/busca na tela 14 (preserva contexto, "limpar filtros" no empty).
- `ux-advanced/empty-states-polish` — `jx-empty-state` para "nenhuma entrega ainda" (com CTA "Nova entrega"), "nenhuma entrega em curso", "nenhuma entrega com esses filtros".
- `ux-advanced/onboarding-patterns` — primeira entrega: empty-state do dashboard convida à ação (CTA primário "Nova entrega").
- `br/ux-copywriting-ptbr` — sentence case, CTA verbo+objeto sem ponto ("Chamar entregador"), estados em rótulo claro pt-BR.
- `quality/accessibility-pro` — AA nos dois temas; badge de estado **nunca só por cor** (texto + ícone); foco visível; erros associados; modal com foco preso e `Esc`.
- `br/lgpd-compliance` — telefone do destinatário é PII: **mascarado na lista** (`(11) 9••••-1234`), nunca em log/URL; CPF nunca puro (hash — D-08); nome exibido só onde necessário.

---

## Telas / estados cobertos por esta fase

1. **§2 — Tela 12: Form de nova entrega** (coleta pré-preenchida · entrega CEP→bairro do catálogo Phase 6 · destinatário · itens · comprovação · pagamento direto) + **`jx-estimate-box`** (frete mediana + taxa antes de confirmar — RN-030) + exceções **E1** (fora de área), **E2** (0 entregadores), **E4** (limite de plano → modal).
2. **§3 — `jx-state-badge`** (novo, reutilizável): os **7 estados** da entrega (RN-019) com as cores de `color.delivery_state`, texto + ícone (a11y).
3. **§4 — Tela 14: Lista de entregas da Loja** sobre `jx-data-table` (filtro por estado, badge, ação **cancelar antes do aceite sem custo**) + **Tela 11: Dashboard da Loja** (KPIs + "em curso agora" + CTA "Nova entrega").
4. **§5 — `jx-upgrade-modal`** (E4 limite de plano — sem dark pattern, comparativo via `jx-plan-card`, "agora não" visível).
5. **§6 — Acessibilidade + LGPD**; **§7 — Tokens (Gate 2)**; **§8 — Visual regression**.

**Fora de escopo (deferido — NÃO especificar aqui):**
- **Despacho / oferta / aceite / cascata** (CRIADA → ACEITA) → **Phase 8**. Aqui a entrega **nasce CRIADA e fica aguardando**; a máquina inteira é *definida*, mas só CRIADA e CANCELADA (pela Loja, antes do aceite) são *atingíveis* nesta phase.
- **Comprovação foto+GPS, COLETADA→ENTREGUE→FINALIZADA, tracking** → **Phase 9**. Aqui só se **escolhe** o método de comprovação (foto default); nada é executado.
- **Checkout pago cartão/PIX (Safe2Pay)** → **Phase 10**. Cartão/PIX aparecem **selecionáveis-desabilitados** com badge "em breve"; só **direto** habilitado (D-02).
- **OTP de comprovação** → pós-M1 (TD-003). Selecionável-desabilitado com badge "em breve" (D-01).
- **Fatura mensal de taxas + bloqueio por fatura vencida (RN-025)** → **Phase 11**. Aqui só o **gancho** (banner de fatura no dashboard, `hidden` por padrão — wireframe 11).
- **Detalhe de uma entrega / tracking page** → o link `ver` aponta para a rota, mas o **detalhe completo** (timeline da máquina, mapa) é Phase 8/9. Aqui só o estado read-only via badge.

---

## 1. Reuso do design system Phase 3/4/6 (não reinventar)

Esta phase **herda integralmente** o contrato visual. Não redefine temas, tipografia, motion nem os componentes já existentes. Referências canônicas:

| Asset herdado | Arquivo real (apps/web) | Uso na Phase 7 |
|---|---|---|
| Temas claro/dark (21 vars semânticas) | `styles/_semantic.scss` | tudo consome `var(--surface)`, `var(--brand)`, etc. DEC-001 vale no form, na lista, no dashboard e no modal. |
| Tokens primitivos `--jx-*` | `styles/_tokens.scss` (gerado de tokens.json) | nunca consumidos direto em componente. |
| Tipografia (escala + italic + mono) | `styles/typography.scss` | H1 dashboard com Fraunces italic; nº entrega, telefone, R$, frete, taxa, data/hora em mono. |
| Anti-FOUC + toggle de tema | `index.html` + `core/theme/*` | já no shell da Loja; todas as telas respeitam o tema ativo. |
| Shell da Loja (header + nav) | `layouts/loja-shell.component.ts` | nova-entrega, lista e dashboard entram sob o shell (nav "Painel / Entregas / …" do wireframe 11). |
| `jx-field` (label + erro + máscara + a11y) | `shared/components/field/field.component.ts` | todos os inputs do form de entrega (endereço, destinatário, telefone, itens, valor). `[mono]` para telefone/valor. |
| `jx-data-table` (header sticky, `aria-sort`, estados) | `shared/components/data-table/data-table.component.ts` | lista de entregas (tela 14) e "em curso" (tela 11). Colunas projetadas via `<ng-template #row>`. |
| `jx-plan-card` (anti-dark-pattern) | `shared/components/plan-card/plan-card.component.ts` | comparativo de planos dentro do `jx-upgrade-modal` (§5). |
| `jx-empty-state` | `shared/state/empty-state.component.ts` | "nenhuma entrega ainda" (CTA), "nenhuma em curso", "nenhuma com esses filtros". |
| `jx-error-state` (`role="alert"`) | `shared/state/error-state.component.ts` | E1 fora de área; falha ao criar; falha ao carregar lista. |
| `jx-warn-banner` (`role="status"`) | `shared/state/warn-banner.component.ts` | E2 "0 entregadores agora"; gancho de fatura vencida (Phase 11). |
| `jx-loading-skeleton` | `shared/state/loading-skeleton.component.ts` | carregando estimativa, criando entrega, carregando lista/dashboard. |
| Máscaras BR | `features/loja/cadastro/br-format.ts` | `maskPhone`/`phoneToE164` (telefone destinatário E.164), `maskCep`/`isCepComplete` (CEP de entrega). |
| Money helpers | `shared/util/money.ts` | `maskBrl`/`parseBrl`/`formatBrl` (valor declarado opcional; exibição de frete/taxa). |

**Novos componentes compartilháveis desta phase** (governança `component-library-governance`, ganham story + baseline §8):
- **`jx-state-badge`** — badge dos 7 estados da entrega (RN-019). **Reutilizável** em lista (14), dashboard (11) e, depois, no detalhe (Phase 8/9). Texto + ícone + cor de `color.delivery_state`. ÚNICA fonte do vocabulário visual de estado.
- **`jx-delivery-row`** — célula de linha de entrega (nº mono · data mono · destino · estado via `jx-state-badge` · frete mono · pagamento · ação). Consome `jx-data-table`.
- **`jx-estimate-box`** — caixa de frete estimado (mediana RN-030) + taxa do plano, mostrada **antes** de confirmar; variantes: faixa de valor (N entregadores), 0 entregadores (E2), carregando.
- **`jx-upgrade-modal`** — modal de limite de plano (E4): comparativo via `jx-plan-card`, CTA upgrade + "agora não" de igual peso (anti-dark-pattern), foco preso, `Esc` fecha.

**Vars semânticas novas:** apenas **7 vars de estado de entrega** derivadas de `color.delivery_state` (§3.1) — a serem adicionadas em `_semantic.scss`/`_tokens.scss` a partir do bloco `color.delivery_state` já existente em tokens.json. **Nenhuma** var de superfície/texto/brand nova.

---

## 2. Tela 12 — Form de nova entrega (F-03, D-01/D-02/D-05)

Superfície **Loja**. Rota `/loja/entregas/nova` (do wireframe 11: botão "+ Nova entrega"). `<main>` centrado `max-width` ~620px (do wireframe 12), margem `--jx-space-5` (24) topo, padding lateral `--jx-space-5`. Form único, seções por `fieldset`, submetido em bloco. Responsivo: em mobile o form ocupa largura total com padding `--jx-space-4`.

### 2.1 Cabeçalho

- **H1 (do wireframe):** "Nova entrega" — `font.size.xl` (22)/`2xl` (28 desktop), weight 600, -.02em. Sem italic aqui (reservado ao dashboard).
- **Voltar:** "← Painel" (`--info`, `font.size.sm`) no topo.

### 2.2 Seções (`fieldset` — wireframe 12, F-03 passos 2-4)

Cada `fieldset`: fundo `--surface-elevated`, borda `--border`, radius `lg` (10), padding `--jx-space-4` (16), margem `--jx-space-3` entre seções. `<legend>` overline: `font.size.xs` (12) weight 600 uppercase letter-spacing .08em `--text-muted`. Todos os inputs via `jx-field`.

| Seção (legend) | Campo | Componente / tipo | Máscara / regra | Mono? |
|---|---|---|---|---|
| **Coleta** | Endereço de coleta | `jx-field` text | **pré-preenchido com a loja** (D-01), editável; default = endereço cadastrado da Loja (Phase 4) | — |
| **Entrega** | Endereço de entrega (rua, número) | `jx-field` text, `required` | livre; placeholder "Rua, número" | — |
| | CEP | `jx-field` text, `inputmode="numeric"` | **`maskCep`** `00000-000`; autocomplete dispara busca de bairro (§2.3) | sim |
| | Bairro | `select` (`jx-field` ou native), `required` | opções = **catálogo de bairros da área** (Phase 6); fora do catálogo → E1 (§2.4) | — |
| **Destinatário** | Nome do destinatário | `jx-field` text, `required` | livre; PII (LGPD) | — |
| | Telefone do destinatário | `jx-field` `type="tel"`, `inputmode="numeric"`, `required` | **`maskPhone`** `(DD) 9XXXX-XXXX` → **`phoneToE164`** ao submeter; PII | sim |
| **Itens** | O que vai ser entregue | `textarea` (via `jx-field`/native), `required` | placeholder "1 pizza grande, 1 refrigerante 2L" | — |
| | Quantidade | `jx-field` `inputmode="numeric"` | inteiro ≥1; default 1 | sim |
| | Valor declarado (R$) | `jx-field` `inputmode="decimal"` **opcional** | **`maskBrl`** `R$ 0,00`; vazio = não declarado | sim |
| | Nº do pedido (comprovação) | `jx-field` text, opcional | livre; placeholder "2851"; mono | sim |
| | Observações p/ o entregador | `jx-field` text, opcional | placeholder "Cuidado, não virar a caixa" | — |
| **Comprovação** | Método | `radiogroup` (3 opções, §2.5) | foto **default**; foto+referência; OTP **desabilitado** "em breve" | — |
| **Pagamento da corrida** | Forma | `radiogroup` (3 opções, §2.6) | **direto** habilitado (default); PIX/cartão **desabilitados** "em breve" | — |

- **Microcopy:** sob "Endereço de coleta": "Pré-preenchido com o endereço da sua loja. Edite se a coleta for em outro lugar." `font.size.xs` `--text-muted`.
- **Valores em mono:** CEP, telefone, quantidade, valor declarado, nº do pedido em `font.family.mono`, `font.size.base` (14).

### 2.3 CEP → bairro do catálogo (autocomplete, reuso Phase 6)

- Ao completar o CEP (`isCepComplete`), dispara busca que sugere/seleciona o **bairro do catálogo da área** (Phase 6). O `select` de bairro lista **só bairros do catálogo** (RN-003 / elegibilidade espacial). O `request_id` da busca não é exibido.
- Bairro **fora do catálogo** (CEP não mapeado / bairro não atendido) → estado **E1 fora de área** (§2.4), não erro de digitação.
- Estado de busca: enquanto resolve, `select` em `aria-busy`, skeleton leve. Sem mapa nesta phase (mapa = Phase 9).

### 2.4 E1 — Endereço fora da área (F-03 E1, D-06)

- **Gatilho:** bairro/CEP fora do catálogo de cobertura da área.
- **UI:** `jx-error-state` `role="alert"` logo abaixo do campo Bairro: **"Endereço fora da nossa área de cobertura. Confira o bairro."** (texto do wireframe). Campo Bairro `aria-invalid="true"`, borda `--error`. **Não** bloqueia o resto do form, mas o CTA "Chamar entregador" fica desabilitado enquanto o destino estiver fora de área.
- **Captura de interesse (D-06):** abaixo do alerta, ação secundária discreta "Avisar quando atendermos esse bairro" (link `--info`, opcional) → registra interesse (gancho leve; não é fluxo desta phase fechar). Copy sem promessa de data.

### 2.5 Método de comprovação (D-01)

`radiogroup` (`role="radiogroup"`, `aria-labelledby` na legend). 3 opções, grid (3 col desktop, empilhado mobile):

| Opção | Estado | Rótulo / microcopy |
|---|---|---|
| Foto | **selecionável, default selecionado** | "Foto na entrega" · "padrão" |
| Foto + nº de referência | selecionável | "Foto + nº do pedido" |
| Foto + código OTP | **desabilitado** (`disabled`, `aria-disabled="true"`) + badge "em breve" | "Foto + código" · badge `font.size.2xs` `--text-muted` fundo `--surface-sunken` |

- Cartão selecionado: borda `--brand` (2px), fundo `--brand-wash` (igual padrão `.pay label.sel` do wireframe, mas via tokens). Não-selecionado: borda `--border-strong`.
- OTP desabilitado **visível mas inerte** (D-01): cursor `not-allowed`, opacidade reduzida via `--text-subtle`, badge "em breve". Foco do teclado pula opções desabilitadas.

### 2.6 Forma de pagamento da corrida (D-02, RN-023)

`radiogroup`, grid 3 col (do wireframe `.pay`):

| Opção | Estado | Rótulo / microcopy |
|---|---|---|
| Direto ao entregador | **habilitado, default selecionado** | "Direto ao entregador" · "dinheiro ou seu PIX" |
| PIX (pela plataforma) | **desabilitado** + badge "em breve" | "PIX" · "pela plataforma" |
| Cartão (pela plataforma) | **desabilitado** + badge "em breve" | "Cartão" · "pela plataforma" |

- **Direto (D-02):** a entrega **nasce sem cobrança online**; a taxa de plataforma acumula na fatura mensal (fatura = Phase 11). Microcopy sob a seção: "No direto, você acerta a corrida com o entregador. A taxa da plataforma entra na sua fatura do mês." `font.size.xs` `--text-muted`.
- PIX/cartão desabilitados com badge "em breve" (Phase 10) — mesmo padrão visual do OTP (§2.5). **Nenhuma** tela de checkout/Safe2Pay nesta phase.

### 2.7 `jx-estimate-box` — frete estimado + taxa (RN-030, D-05) — antes de confirmar

Caixa de destaque acima do CTA (do wireframe `.estimate`): fundo `--brand-wash`, borda `--brand-wash-border`, radius `lg` (10), padding `--jx-space-4`, `display:flex` justify-between, `role="status"` (`aria-live="polite"`).

- **Conteúdo (estado normal):** à esquerda rótulo "Frete estimado" + `<small>` "({N} entregadores online)"; à direita **valor em mono** weight 700: faixa "R$ 8,00–9,50" + "+ taxa R$ 1,50". A **mediana** (RN-030) das tabelas dos entregadores elegíveis define a faixa; a taxa vem do plano da Loja (Phase 4). **Nenhum valor hardcoded** — tudo da API.
- **Recalcula** quando origem/destino/bairro mudam (debounce `motion.normal`); enquanto recalcula, skeleton dentro da caixa (`aria-busy`).
- **Variante E2 (0 entregadores — §2.8):** a caixa mostra "Sem entregadores online agora para esse trecho" em vez da faixa; ver §2.8.
- **Disclaimer (D-05):** microcopy `font.size.2xs` `--text-muted`: "Estimativa pela mediana de quem está online. O valor final é a tabela de quem aceitar." (o teto +10% e re-confirmação são regra de Phase 8 — aqui só a estimativa).

### 2.8 E2 — 0 entregadores online (F-03 E2, D-06)

- **Gatilho:** nenhum entregador online cobre origem **E** destino.
- **UI:** `jx-warn-banner` `role="status"` (**não-bloqueante** — D-06) acima do CTA: "0 entregadores online agora para esse trecho — sua entrega pode demorar." A `jx-estimate-box` mostra "Sem estimativa agora". **A Loja decide:** o CTA "Chamar entregador" **continua habilitado** (a entrega nasce CRIADA e aguarda — Phase 8). Borda esquerda 3px `--warning`, fundo `--warning-bg` (dark: `--surface-elevated` + `--warning` vivo).
- Diferença de E1: E1 é `role="alert"` e **bloqueia** (fora de cobertura, não dá pra entregar); E2 é `role="status"` e **permite** (dentro da cobertura, só sem ninguém online agora).

### 2.9 Validação, CTA e criação (form-ux-mastery, D-03)

- **Validação inline no blur**, um erro por campo abaixo do input (`font.size.xs` `--error`, `aria-describedby`), `aria-invalid` + borda `--error` no campo. Telefone valida E.164 completo; CEP valida 8 dígitos; itens/destino obrigatórios.
- **CTA (do wireframe):** "Chamar entregador" — full-width, `--brand`/`--brand-contrast`, radius `lg`, weight 700, ≥44px (`font.size.md` 16). **Habilita** só com form válido **e** destino dentro de área (E1 desabilita; E2 não). Verbo+objeto, sem ponto.
- **E4 (limite de plano):** se a Loja está no limite (Free 2/mês — RN-028), o submit abre `jx-upgrade-modal` (§5) **em vez de** criar. O contador vem de `merchant_subscriptions` (Phase 4). Ver §5.
- **Criação (D-03):** sucesso → entrega nasce no estado **CRIADA**; redireciona para a lista/detalhe com feedback discreto `role="status"` "Entrega criada — procurando entregador" (`--success`, `font.size.sm`). **Sem confete** (anti-slop). Estado `criando` = CTA desabilitado + skeleton + `aria-busy`.
- **Falha ao criar:** `jx-error-state` `role="alert"` acionável "Não foi possível criar a entrega. Tente de novo." + "Tentar de novo". `request_id` logado, não exibido.

---

## 3. `jx-state-badge` — badge dos 7 estados (RN-019, D-03) — NOVO, reutilizável

A peça mais reutilizada da phase. ÚNICA fonte do vocabulário visual de estado da entrega. Usado em lista (14), dashboard (11) e, depois, detalhe (Phase 8/9).

### 3.1 Os 7 estados e suas cores (`color.delivery_state`)

Cada estado mapeia 1:1 para `color.delivery_state.*` de tokens.json. Cria-se uma var semântica por estado (`--state-{nome}`) derivada do primitivo `--jx-delivery-{nome}` (gerado de `color.delivery_state`). **Status nunca só por cor** → cada badge tem **texto + ícone** (a11y). Rótulo pt-BR voltado à Loja (do wireframe 14/11).

| Estado (RN-019 / código) | Token cor (`color.delivery_state.*`) | Hex | Var semântica | Rótulo pt-BR (Loja) | Ícone (texto/glifo, `aria-hidden`) |
|---|---|---|---|---|---|
| `CRIADA` | `color.delivery_state.criada` | #6B5F50 | `--state-criada` | "Procurando" | ◷ (relógio/busca) |
| `ACEITA` | `color.delivery_state.aceita` | #0A66C2 | `--state-aceita` | "Aceita" | ✓ |
| `COLETADA` | `color.delivery_state.coletada` | #E89B0E | `--state-coletada` | "A caminho" | → |
| `ENTREGUE` | `color.delivery_state.entregue` | #1B998B | `--state-entregue` | "Entregue" | ⤓ (entregue) |
| `RECUSADA_NO_DESTINO` | `color.delivery_state.recusada_no_destino` | #E84E1B | `--state-recusada` | "Recusada no destino" | ⊘ |
| `CANCELADA` | `color.delivery_state.cancelada` | #9D8E7A | `--state-cancelada` | "Cancelada" | × |
| `FINALIZADA` | `color.delivery_state.finalizada` | #0F6E62 | `--state-finalizada` | "Finalizada" | ✓✓ |

- **Nota de escopo:** nesta phase só **CRIADA** ("Procurando") e **CANCELADA** são *atingíveis* (a entrega nasce CRIADA; a Loja pode cancelar antes do aceite). Os outros 5 são **definidos no componente** (RN-019 define a máquina inteira aqui) e usados quando as Phases 8/9 os produzirem. O badge já cobre os 7 para não redesenhar depois.
- O dashboard (wireframe 11) usa rótulos de jornada mais coloquiais para "em curso": ACEITA = "Indo coletar", COLETADA = "A caminho", CRIADA = "Procurando". `jx-state-badge` aceita um `[variant]` (`list` | `dashboard`) que troca só o rótulo, mantendo cor+ícone. Vocabulário canônico do banco permanece o da coluna "código".

### 3.2 Anatomia (texto + ícone + cor — a11y)

- **Pílula:** `radius.full` (9999), padding `--jx-space-1`/`--jx-space-2` (vertical 3-4px / horizontal 8px do wireframe `.st`), `font.size.2xs` (11) weight 700, uppercase opcional (lista usa caixa alta como o wireframe; dashboard usa rótulo de jornada em caixa normal).
- **Cor (claro):** texto = `--state-{nome}`; fundo = wash leve do mesmo matiz. Para reusar superfícies existentes sem inventar 7 fundos: fundo = `--surface-sunken` (neutro) com texto/borda na `--state-{nome}` viva — **padrão dark-mode-theming** que funciona nos DOIS temas e garante AA. (O wireframe usa pastéis `_bg`; adotamos o padrão "superfície neutra + cor viva" da Phase 3 para não criar 7 tokens `_bg` novos e manter AA no dark.)
- **Ícone:** glifo/`<svg>` `aria-hidden="true"` à esquerda do texto; o texto é a fonte acessível do estado. `role` ausente (é conteúdo), mas o texto do estado é sempre lido.
- **Dark:** mesma regra — fundo `--surface-elevated`/`--surface-sunken`, texto na `--state-{nome}` (todas as 7 cores já têm contraste AA sobre superfície escura; o checker valida).

### 3.3 Regra de uso

- **Nunca** renderizar estado só por cor ou só por código cru de banco. Sempre via `jx-state-badge` (texto+ícone+cor). Proíbe-se `<span style="color:#...">` ou classe ad-hoc — só o componente governado.

---

## 4. Tela 14 (lista) + Tela 11 (dashboard) — sobre `jx-data-table` (data-tables-ux)

### 4.1 Tela 14 — Lista de entregas da Loja

Rota `/loja/entregas`. `<main>` `max-width` ~980px (do wireframe 14). Usa `jx-data-table` + `jx-delivery-row` + barra de filtros.

- **Filtros (search-filter-ux — do wireframe):** linha `form.filters` acima da tabela: `select` **estado** (Todos / Procurando / Aceita / A caminho / Entregue / Finalizada / Recusada no destino / Cancelada — rótulos = §3.1), `select` **pagamento** (Todo / Direto / PIX / Cartão), `date` **de**/`date` **até**, `search` "Buscar por nº, destinatário…", botão "Filtrar" (`--text`/neutro escuro `neutral.800` fill — secundário sóbrio, não persimmon). Filtros preservam contexto na URL (query params). PIX/Cartão no filtro existem (entregas futuras), mas nesta phase só "Direto" produz dados.
- **Colunas (`jx-data-table` + `jx-delivery-row`):** Nº (link, mono) · Data (mono `dd/MM HH:mm`) · Destino (bairro) · Entregador (nome ou "—" se ainda CRIADA) · Frete (mono R$ ou "—") · Pagamento (direto/PIX/cartão) · **Status** (`jx-state-badge` variant `list`) · **Ação**.
- **Ação por linha — cancelar antes do aceite (RN-019 / D-03):** entrega no estado **CRIADA** mostra ação "Cancelar" (botão outline `--error`, texto+borda, fundo transparente, área ≥44px). Cancelar **antes do aceite é sem custo** → confirmação leve: "Cancelar a entrega #{nº}? Como ninguém aceitou ainda, não há cobrança." + "Cancelar entrega" (`--error`) / "Voltar" (texto `--text-muted`). Estados ≠ CRIADA **não** mostram "Cancelar" (cancelamento pós-aceite tem regra/custo → Phase 8+; aqui ausente). Link "ver" (→ detalhe) sempre presente.
- **Telefone do destinatário (LGPD):** se exibido em alguma coluna/tooltip, **mascarado** `(11) 9••••-1234` — nunca completo na lista (§6). Por padrão a lista não mostra telefone (só destino/destinatário-nome quando necessário).
- **Estados (jx-data-table embutidos):** `loading` = skeleton de linhas; `empty` (sem entregas / filtro sem resultado) = `jx-empty-state`; `error` = `jx-error-state` + retry. Empty com filtro: "Nenhuma entrega com esses filtros." + "Limpar filtros" (do wireframe). Empty sem nenhuma entrega: "Nenhuma entrega ainda." + CTA "Nova entrega" (`--brand`).
- **Paginação:** `nav.pages` simples (do wireframe) — só aparece com >1 página; acessível (`aria-current="page"`).

### 4.2 Tela 11 — Dashboard da Loja

Rota `/loja` (default da Loja). `<main>` `max-width` ~980px. Layout do wireframe 11.

- **Gancho de fatura (Phase 11):** `jx-warn-banner` `role="status"` no topo, **`hidden` por padrão** nesta phase (RN-025 é Phase 11). Copy preparada: "Sua fatura de {mês} venceu há {N} dias. Pagar agora — novas entregas serão bloqueadas em {M} dias." Não dispara nesta phase; só o slot existe.
- **H1 com italic (do wireframe):** "Hoje na sua loja. Tudo *certinho.*" — *certinho* em Fraunces italic `--brand` weight 500 (1 palavra), `font.size.2xl` (28). Ao lado, CTA primário "+ Nova entrega" (`--brand`, ≥44px) → rota `/loja/entregas/nova`.
- **KPIs (`.stats` — 4 cards, do wireframe):** grid 4 col (responsivo → 2 col mobile). Cada card `--surface-elevated`, borda `--border`, radius `lg` (10). Valor em **mono** `font.size.2xl` (28) (`<b>`); rótulo overline `font.size.2xs` (11) uppercase `--text-muted`. KPIs: "entregas hoje", "tempo médio" (mono "14 min"), "fretes hoje" (mono R$), "entregas do plano" (mono "12/40" — contador RN-028). Valores da API; nada hardcoded.
- **"Em curso agora" (card + `jx-data-table`):** título `font.size.md` (16). Tabela com colunas Entrega (nº mono) · Destino · Entregador · **Status** (`jx-state-badge` variant `dashboard`) · Pagamento · ação "ver". Nesta phase só linhas em estado **CRIADA** ("Procurando") aparecem aqui (ACEITA/COLETADA chegam na Phase 8); o badge já suporta os rótulos de jornada. Empty: `jx-empty-state` "Nenhuma entrega em curso. Crie uma no botão acima." (CTA aponta ao botão "+ Nova entrega").
- **Primeira entrega (onboarding-patterns):** Loja sem nenhuma entrega → KPIs zerados + empty-state convidando à primeira ("Sua primeira entrega começa aqui." + CTA "Nova entrega").

---

## 5. `jx-upgrade-modal` — E4 limite de plano (RN-028, D-07) — sem dark pattern

- **Gatilho (D-07):** Loja no limite do plano (Free 2/mês; contador zera dia 1º — `merchant_subscriptions`, Phase 4). A 3ª entrega → submit do form (§2.9) abre o modal **em vez de** criar. Fatura vencida >7 dias bloquearia criação (RN-025) — **gancho** previsto, mas fatura é Phase 11; nesta phase só o limite de contagem dispara.
- **Anatomia:** diálogo modal (`role="dialog"`, `aria-modal="true"`, `aria-labelledby`), sobre overlay `rgba` warm (derivado de `--surface-sunken`/sombra), painel `--surface-elevated`, borda `--border`, radius `xl` (16), sombra `--shadow-lg`, `max-width` ~560px, padding `--jx-space-6` (32). Foco **preso** dentro do modal; abre com foco no título; `Esc` fecha (= "agora não"); foco volta ao CTA que o abriu.
- **Conteúdo:**
  - **Título:** "Você usou suas 2 entregas do mês" (`font.size.lg`/`xl`, weight 600). Sentence case, factual, sem culpar.
  - **Subtexto:** "No plano Free são 2 entregas por mês. O contador zera no dia 1º. Para enviar agora, escolha um plano com mais entregas." `font.size.sm` `--text-muted`.
  - **Comparativo:** 2-3 `jx-plan-card` lado a lado (Free atual marcado "Seu plano" + planos pagos), **data-driven** de `GET /v1/plans` (DRV-009). Valores (preço, entregas, taxa) em mono via `jx-plan-card`.
- **Anti-dark-pattern (D-07 / `jx-plan-card` já garante):**
  - **"Agora não" sempre visível** e de **igual peso visual** ao CTA de upgrade — botão de texto `--text` legível (não cinza apagado escondido), `font.size.base`, ≥44px, no rodapé ao lado do CTA primário.
  - **Sem** contagem regressiva falsa, **sem** "última chance", **sem** pré-seleção forçada do plano mais caro, **sem** escurecer/ocultar o "agora não". Fechar pelo X, `Esc` ou "Agora não" são equivalentes e não penalizam.
  - Copy honesta: diz exatamente o limite e quando reseta (dia 1º). Não infla urgência.
- **Ação:** escolher plano pago → fluxo de upgrade (rota `/loja/plano` — Phase 4). "Agora não"/Esc/X → fecha, volta ao form com a entrega **não criada** (nada perdido; o form mantém o que foi preenchido).

---

## 6. Acessibilidade (accessibility-pro — AA nos dois temas, DEC-001) + LGPD

### 6.1 Acessibilidade

- **Contraste AA nos DOIS temas:** herda mapas validados da Phase 3. As **7 cores de estado** (`color.delivery_state`) validadas claro+dark sobre a superfície do badge (`--surface-sunken`/`--surface-elevated`) pelo checker (axe + contraste). `jx-estimate-box`, KPIs mono, modal e CTAs também.
- **Status nunca só por cor:** `jx-state-badge` sempre **texto + ícone** além da cor (§3.2). Filtro de estado e legenda usam o mesmo rótulo textual.
- **Form acessível:** todo input com `<label for>` (via `jx-field`); cada erro associado por **`aria-describedby`**; `aria-invalid="true"` no campo inválido / fora de área (E1). `radiogroup` de comprovação e pagamento com `role="radiogroup"` + `aria-labelledby` na legend; opções desabilitadas (OTP, PIX, cartão) com `aria-disabled="true"` e fora da ordem de foco.
- **Estimativa e exceções via live region:** `jx-estimate-box` `role="status"` `aria-live="polite"` (anuncia recálculo); E1 `jx-error-state` `role="alert"`; E2 `jx-warn-banner` `role="status"`; criação ok/falha anunciada.
- **Tabela acessível (jx-data-table já garante):** `<th scope="col">`, `aria-sort`, `<caption>`, navegação por teclado; ação "Cancelar/ver" como botão/link real ≥44px.
- **Modal (jx-upgrade-modal):** `role="dialog"` `aria-modal="true"`, foco preso, foco inicial no título, `Esc` fecha, foco retorna ao gatilho; "Agora não" alcançável por teclado e de igual peso.
- **Foco visível:** `--focus-ring` (`shadow.focus`) em todo interativo (campos, radios, CTA, ações de linha, filtros, botões do modal). Nunca `outline:none` sem substituto.
- **Touch ≥44×44px:** CTA "Chamar entregador", "+ Nova entrega", opções de radio, "Cancelar/ver" da linha, botões do modal, "Filtrar".
- **Motion:** recálculo da estimativa/abertura do modal em `motion.normal` `easing_out`; toque scale .97 `motion.fast`; **`prefers-reduced-motion`** → sem scale/transição.
- **`lang="pt-BR"`**, landmarks `<main>`/`<nav>` (shell Loja)/`<form>`/`<table>`. `axe-core` no form, na lista e no dashboard: zero violações críticas (verificação ROADMAP).

### 6.2 LGPD (br/lgpd-compliance — has_pii:true, D-08)

- **Telefone do destinatário = PII:** exibido **mascarado** na lista/dashboard (`(11) 9••••-1234`); completo só onde estritamente necessário (ex. ação de contato no detalhe — Phase 8+). **Nunca** em URL, query, log ou screenshot de teste.
- **CPF nunca puro (D-08):** se houver CPF do destinatário (antifraude), só **hash** trafega/exibe; a UI nunca pede nem mostra CPF puro nesta phase.
- **Nome do destinatário:** exibido só onde necessário (linha de entrega, detalhe); não em KPIs agregados.
- **Minimização:** o form coleta só o essencial (nome, telefone, endereço, itens); valor declarado e nº do pedido são opcionais e claramente marcados.

---

## 7. Tabela de tokens citados (Gate 2 — todos existem em `tokens.json`)

Cada token referenciado, com caminho em `docs/identidade-visual/tokens.json`. **Confirmado: 100% existem (zero inventados)** — incluindo os **7 `color.delivery_state`**. As vars semânticas de superfície/texto/brand (`--surface`, `--surface-elevated`, `--surface-sunken`, `--text`, `--text-muted`, `--text-subtle`, `--border`, `--border-strong`, `--brand`, `--brand-contrast`, `--brand-wash`, `--brand-wash-border`, `--success`, `--warning`, `--warning-bg`, `--error`, `--error-bg`, `--info`, `--focus-ring`) já estão em `_semantic.scss` (Phase 3).

| Token (caminho em tokens.json) | Valor | Existe? |
|---|---|---|
| **`color.delivery_state.criada`** | #6B5F50 | ✅ |
| **`color.delivery_state.aceita`** | #0A66C2 | ✅ |
| **`color.delivery_state.coletada`** | #E89B0E | ✅ |
| **`color.delivery_state.entregue`** | #1B998B | ✅ |
| **`color.delivery_state.recusada_no_destino`** | #E84E1B | ✅ |
| **`color.delivery_state.cancelada`** | #9D8E7A | ✅ |
| **`color.delivery_state.finalizada`** | #0F6E62 | ✅ |
| `color.brand.50` (→ `--brand-wash`) | #FFF1E8 | ✅ |
| `color.brand.100` (→ `--brand-wash-border`) | #FFDEC1 | ✅ |
| `color.brand.400` (brand dark) | #FB813D | ✅ |
| `color.brand.500` (→ `--brand`) | #E84E1B | ✅ |
| `color.brand.600` (→ `--brand-hover`) | #C73E0F | ✅ |
| `color.neutral.50` (→ `--surface` / `--brand-contrast`) | #FAF6EE | ✅ |
| `color.neutral.100` (→ `--surface-elevated`) | #F2EBE0 | ✅ |
| `color.neutral.200` (→ `--surface-sunken` / `--border`) | #E5DBCC | ✅ |
| `color.neutral.300` (→ `--border-strong`) | #C8BAA5 | ✅ |
| `color.neutral.400` (→ `--text-subtle`) | #9D8E7A | ✅ |
| `color.neutral.500` (→ `--text-muted`) | #6B5F50 | ✅ |
| `color.neutral.700` / `.800` / `.900` (text / fill secundário / surface dark) | #2D261F / #181410 / #0A0805 | ✅ |
| `color.semantic.success` (→ `--success`) | #1B998B | ✅ |
| `color.semantic.warning` (→ `--warning`) | #E89B0E | ✅ |
| `color.semantic.warning_bg` (→ `--warning-bg`) | #FFF1D2 | ✅ |
| `color.semantic.error` (→ `--error`) | #C71D1D | ✅ |
| `color.semantic.error_bg` (→ `--error-bg`) | #F9DCDC | ✅ |
| `color.semantic.info` (→ `--info`) | #0A66C2 | ✅ |
| `spacing.1`/`.2`/`.3`/`.4`/`.5`/`.6` (4/8/12/16/24/32px) | — | ✅ |
| `radius.lg` / `xl` / `full` (10/16/9999px) | — | ✅ |
| `font.family.display` | Inter Tight… | ✅ |
| `font.family.serif_accent` (Fraunces italic) | Fraunces… | ✅ |
| `font.family.mono` (nº, telefone, R$, data) | JetBrains Mono… | ✅ |
| `font.size.2xs`/`xs`/`sm`/`base`/`md`/`lg`/`xl`/`2xl` (11/12/13/14/16/18/22/28) | — | ✅ |
| `font.weight.regular` / `medium` / `semibold` / `bold` (400/500/600/700) | — | ✅ |
| `shadow.lg` (→ `--shadow-lg`, modal) | rgba(24,20,16,…) | ✅ |
| `shadow.focus` (→ `--focus-ring`) | rgba(232,78,27,.28) | ✅ |
| `motion.fast` / `normal` / `easing_out` (140/220ms / cubic-bezier) | — | ✅ |

**Tokens referenciados que NÃO existem em tokens.json: NENHUM (0).** Os **7 `color.delivery_state`** existem e são usados literalmente no `jx-state-badge`. Nenhuma var de superfície/texto/brand nova; as únicas vars novas são as 7 `--state-*` **derivadas** de `color.delivery_state` (geração mecânica, não inventa cor). Gate 2 satisfeito.

---

## 8. Visual regression (baseline desta phase)

Novos componentes/telas que recebem story + baseline (`product/visual-regression-testing`):

- [ ] `jx-state-badge` — stories: **todos os 7 estados** (criada/aceita/coletada/entregue/recusada/cancelada/finalizada) · variant list · variant dashboard · claro+dark
- [ ] `jx-estimate-box` — stories: faixa (N entregadores), 0 entregadores (E2), carregando · claro+dark
- [ ] `jx-delivery-row` — stories: CRIADA (com ação cancelar), sem entregador (—), entregue, cancelada · claro+dark
- [ ] `jx-upgrade-modal` — stories: aberto (comparativo), foco no "agora não", mobile · claro+dark
- [ ] `nova-entrega` (tela 12) — stories: form-vazio, preenchido-válido, E1 fora-de-área (alert), E2 0-entregadores (warn), validando, criando · claro+dark · desktop+mobile
- [ ] `loja-entregas` (tela 14) — stories: com-entregas, filtro-sem-resultado (empty), sem-nenhuma (empty+CTA), loading, erro · claro+dark
- [ ] `loja-dashboard` (tela 11) — stories: com-KPIs+em-curso, primeira-entrega (empty/onboarding), gancho-fatura (slot hidden) · claro+dark

Nome screenshot: `{component}-{state}-{theme}-{viewport}.png`.

---

## 9. Open questions para o humano

- [ ] **Rótulos de estado list × dashboard:** o wireframe 14 usa caixa-alta (ENTREGUE, CANCELADA) e o 11 usa rótulos de jornada (PROCURANDO, A CAMINHO, INDO COLETAR). Modelei `jx-state-badge [variant]` (list/dashboard) trocando só o rótulo, mantendo cor+ícone+código canônico. **Recomendação:** manter os dois vocabulários via variant. Confirmar se a Loja prefere um só vocabulário em ambas as telas.
- [ ] **Telefone na lista (LGPD):** por padrão **não** exibo telefone na lista (só nome/destino); mascarado só se realmente necessário. **Recomendação:** manter telefone fora da lista; revelar mascarado só no detalhe/ação de contato (Phase 8+). Confirmar.
- [ ] **"Cancelar" só em CRIADA:** modelei a ação de cancelar **só** no estado CRIADA (antes do aceite, sem custo — D-03/RN-019). Cancelamento pós-aceite (com regra/custo) fica para Phase 8. Confirmar que nesta phase a Loja só cancela CRIADA.
- [ ] **Captura de interesse (E1):** modelei como link opcional "Avisar quando atendermos esse bairro" sem promessa de data. **Recomendação:** gancho leve, persistir interesse; não bloquear. Confirmar se entra no M1 ou fica deferido.

---

## Approval

- [ ] Humano revisou e aprovou (ou delegou ao ui-checker)
- [ ] ui-checker validou 6 dimensões: tokens, tipografia, copy, estados, interações, acessibilidade
- [ ] Gate 2 (Visual Contract) verde — tokens citados existem em tokens.json (§7), incluindo os 7 `color.delivery_state`
- [ ] Wireframe-contract de `12-loja-nova-entrega.html`, `11-loja-dashboard.html`, `14-loja-entregas.html` coberto (verificação ROADMAP); despacho (Phase 8), comprovação (Phase 9) e checkout pago (Phase 10) ficam fora.
- [ ] Aprovado em: {date}

**Próximo passo:** `/gsd:plan-phase 7` — o planner recebe este UI-SPEC como contrato de design.
