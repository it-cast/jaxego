---
phase: 06-rea-oper-vel-bairros-config-cobertura-e-tabela-de-frete
title: Área operável — bairros, config, cobertura e tabela de frete
status: draft
platform: web+mobile (admin de área = web desktop-first; entregador = Ionic mobile-first)
gate2_visual_contract: pending-checker
generated_by: gsd-ui-researcher
generated_at: 2026-06-10
reuses: 03-shell-frontend-design-system-3-superf-cies, 04-cadastro-e-ativa-o-de-loja, 05-cadastro-do-entregador-kyc-2-n-veis-documentos-b2
---

# UI-SPEC — Phase 6: Área operável (bairros, config, cobertura e tabela de frete)

> Design contract da Phase 6 (Gate 2 — Visual Contract). **BLOQUEIA** `plan-phase` se não existir.
> Plataformas: **superfície Admin de área** (web desktop-first — config + catálogo de bairros, telas 17/18/21) e **superfície Entregador** (Ionic 8, mobile-first — cobertura + tabela de frete + online/offline, tela 10).
> **Regra de ouro Gate 2:** todo valor visual é token. Nenhum `#hex` hardcoded. Toda var/token citado existe em `docs/identidade-visual/tokens.json` (§9) ou na camada semântica da Phase 3 (`_semantic.scss`).
> **Princípio desta phase:** *reusar*, não reinventar. Temas claro/dark (DEC-001), tipografia, motion, 4 componentes de estado, `jx-field` e o padrão de painel admin **já existem** (Phase 3/4/5). Aqui especificamos só o **novo**: o formulário de config da área, o **`jx-data-table`** governado (primitivo de tabela compartilhado), a entrada de polígono por GeoJSON/coordenadas, a tela mobile de cobertura+preços do entregador (com validação de PISO) e o toggle online/offline.

---

## Fontes de verdade consultadas

- `.planning/phases/06-.../06-CONTEXT.md` — decisões D-01..D-07 (catálogo de bairros ADR-006, config F-08, cobertura RN-003, tabela de frete RN-015, online/offline, espacial MySQL 8). Polígono opcional no M1; desenho no mapa deferido (só GeoJSON/coordenadas).
- `docs/identidade-visual/tokens.json` — tokens **canônicos** (FONTE da verdade visual).
- `.planning/phases/03-.../UI-SPEC.md` — design system estabelecido (21 CSS vars semânticas claro/dark, tipografia, motion, 4 componentes de estado). Contrato herdado.
- `.planning/phases/04-.../UI-SPEC.md` — padrão de formulário BR + `jx-field` + máscara monetária + estados de erro acionáveis. Seguimos.
- `.planning/phases/05-.../UI-SPEC.md` — **padrão de painel admin de área já estabelecido** (layout sidebar desktop, fila densa, mono nos dados, badges texto+ícone+cor, audit em ação sensível). A tabela de KYC (`jx-kyc-queue-table`) era feature-local; **esta phase a generaliza** em `jx-data-table` compartilhado.
- `apps/web/src/` — código real a reusar: `shared/state/*` (4 estados), `shared/components/field/*` (`jx-field`), `core/theme/*`, `styles/_semantic.scss` + `_tokens.scss` + `typography.scss`, `layouts/*` (shell admin sidebar + shell entregador Ionic tabs), `features/admin/kyc/*` (padrão de fila/tabela admin).
- `projeto/wireframes/10-entregador-cobertura-precos.html`, `17-admin-area-dashboard.html`, `18-admin-area-entregadores.html`, `21-admin-area-config.html` — contratos DOM.
- `projeto/regras-negocio/fluxos.md` §F-08 (`:156-171`) — config da área pelo admin; E2 (ação sensível → audit_log).
- `projeto/regras-negocio/regras.md` — RN-003 (cobertura coleta E entrega + exclusões), RN-015 (entregador define preço, plataforma só impõe PISO), RN-005 (geofence default 80 m, configurável).
- `.planning/ROADMAP.md` Phase 6 — flags (has_ui, has_api, mobile; has_payments:false, has_pii:false, integration_check:false) + skills obrigatórias.

### Skills aplicadas (matriz UI + flags Phase 6)

- `product/component-library-governance` — **reusar** os 4 estados (Phase 3), `jx-field` (Phase 4). Novos componentes governados (story + baseline §10): **`jx-data-table`** (primitivo de tabela com header/sort/zebra/estados, reusável pela fila KYC e além), `jx-neighborhood-row` (linha CRUD de bairro), `jx-coverage-list` (lista de cobertura mobile com toggle+preço por bairro), `jx-availability-toggle` (online/offline).
- `ux-advanced/design-tokens-system` — consumir só camada semântica (`var(--surface)`, `var(--brand)`); nunca primitivo nem hex. Nenhuma var semântica nova é necessária.
- `ui-ux-pro-max` — editorial-técnica: valores R$, raios em metros, timeouts em segundos, % de retorno, **coordenadas/GeoJSON** e nomes-código de bairro em mono; Fraunces italic em 1 palavra-chave do H1; persimmon como única cor de ação. **Anti AI-slop:** sem gradiente, sem card "glow", sem toggle neon, sem mapa decorativo. Densidade de painel admin sóbria.
- `ux-advanced/saas-dashboard-patterns` — config da área e dashboard como layout sidebar denso; agrupar regras por `fieldset`/seção; salvar com confirmação para ação sensível (audit); KPIs do dashboard (tela 17) em mono.
- `ux-advanced/data-tables-ux` — `jx-data-table`: header sticky, ordenação acessível (`aria-sort`), zebra opcional, densidade compacta, ações por linha ≥44px de área de clique, estados (loading/empty/error) da tabela, sem paginação falsa (carrega o catálogo da área — escopo pequeno; paginação só se crescer).
- `ux-advanced/responsive-breakpoint-strategy` — admin desktop-first (tabela densa, 2 col em fieldsets largos); entregador mobile-first (lista vertical, ≤420px do wireframe).
- `ux-advanced/gesture-touch-patterns` (mobile/entregador) — alvos ≥44px, toggle de cobertura por bairro tocável, toggle online/offline grande, feedback de toque (scale .97), sem gesto destrutivo escondido.
- `br/brazilian-forms` — **máscara monetária** (piso e preços R$ `0,00` com vírgula decimal pt-BR), `inputmode="decimal"` para dinheiro / `inputmode="numeric"` para metros/segundos/%, **nunca `type="number"` cru** para dinheiro (separador e zeros à direita). GeoJSON/coordenadas como `textarea`/`text` mono, não `number`.
- `ux-advanced/form-ux-mastery` — validação inline no blur, um erro por campo via `aria-describedby`, CTA habilita só com formulário válido, confirmação antes de salvar config sensível.
- `quality/error-ux-patterns` — `jx-error-state` `role="alert"` para preço abaixo do piso (mensagem **citando o piso**) e para bloqueio de remoção de bairro com entregas ativas; `jx-warn-banner` não-bloqueante para "só active pode ficar online".
- `br/ux-copywriting-ptbr` — sentence case, CTA verbo+objeto sem ponto, erro = o que houve + o que fazer.
- `quality/accessibility-pro` — AA nos dois temas, foco visível, touch ≥44px, **tabelas acessíveis** (`<th scope>`, `aria-sort`, caption), toggles com `role="switch"`/`aria-checked`, status por texto+ícone (nunca só cor).
- `ux-advanced/empty-states-polish` — `jx-empty-state` para "nenhum bairro cadastrado" (causa + CTA "Adicionar bairro") e "nenhum bairro de cobertura ainda" no entregador.

---

## Telas / estados cobertos por esta fase

1. **§2 — Tela 21 (parte A): Config da área** (admin web): nível KYC, piso de frete (km/entrega) com máscara monetária, raio de geofence (m), timeouts de despacho (s), política de retorno (%). Salvar com confirmação → audit.
2. **§3 — `jx-data-table`** (primitivo de tabela compartilhado, novo) + **Tela 21 (parte B): Catálogo de bairros** (CRUD: listar/adicionar/remover, polígono opcional via GeoJSON/coordenadas).
3. **§4 — Tela 10: Cobertura + preços do entregador** (Ionic mobile): seleção de bairros (com exclusões), tabela de frete (modo bairro / modo km) com validação de PISO, % de retorno.
4. **§5 — `jx-availability-toggle`: online/offline** (entregador) — só `active` pode ficar online.
5. **§6 — Estados** (vazio / erro-piso / erro-remoção / loading) reusando componentes Phase 3.
6. **§7 — Acessibilidade**; **§8 — Tokens (Gate 2)**; **§10 — Visual regression**.

**Fora de escopo (deferido — NÃO especificar aqui):**
- **Despacho / ofertas / cascata** (consome cobertura + disponibilidade) → **Phase 8**. O `busy` derivado da carga e o consumo do estado online são Phase 8 — aqui só o toggle online/offline e o estado pronto.
- **Criação de entregas** (usa bairro do catálogo) → **Phase 7**.
- **Mapa interativo de tracking** (MapLibre) → **Phase 9**. Aqui **nenhum mapa** — polígono entra por GeoJSON/coordenadas em texto.
- **Desenho de polígono no mapa pelo admin** → nice-to-have pós-M1 (CONTEXT §deferred). M1 aceita só GeoJSON/coordenadas.
- **Dashboard da área (tela 17) e listagem de entregadores (tela 18)** já têm o **contrato de tabela/KPIs** estabelecido na Phase 5 (`jx-kyc-queue-table`) e no shell admin da Phase 3; esta phase **só os refatora sobre `jx-data-table`** (§3.5) e **não redesenha** o detalhe de entregador (Phase 5) nem o despacho (Phase 8).

---

## 1. Reuso do design system Phase 3/4/5 (não reinventar)

Esta phase **herda integralmente** o contrato visual. Não redefine temas, tipografia, motion nem os componentes já existentes. Referências canônicas:

| Asset herdado | Arquivo real (apps/web) | Uso na Phase 6 |
|---|---|---|
| Temas claro/dark (21 vars semânticas) | `styles/_semantic.scss` | tudo consome `var(--surface)`, `var(--brand)`, etc. DEC-001 vale em config, tabela e tela mobile. |
| Tokens primitivos `--jx-*` | `styles/_tokens.scss` (gerado de tokens.json) | nunca consumidos direto em componente. |
| Tipografia (escala + italic + mono) | `styles/typography.scss` | H1 com Fraunces italic; valores R$, metros, segundos, %, coordenadas/GeoJSON e nome-código de bairro em mono. |
| Anti-FOUC + toggle de tema | `index.html` + `core/theme/*` | já no shell admin e no shell entregador; todas as telas respeitam tema ativo. |
| Shell admin (sidebar desktop) | `layouts/*` (admin) | config/bairros entram como rota `/admin/{area}/config` sob a sidebar (item "Configurações" do wireframe 17). |
| Shell entregador (Ionic tabs) | `layouts/*` (entregador) | cobertura/preços abre na aba/rota do entregador; toggle online no início/perfil. |
| `jx-empty-state` | `shared/state/empty-state.component.ts` | catálogo de bairros vazio (admin); sem bairros de cobertura (entregador). |
| `jx-error-state` (`role="alert"`) | `shared/state/error-state.component.ts` | **preço abaixo do piso** (cita o piso); **remoção bloqueada** (bairro com entregas ativas); falha de salvar config. |
| `jx-warn-banner` (`role="status"`) | `shared/state/warn-banner.component.ts` | "você só recebe ofertas com coleta E entrega na cobertura" (aviso de contexto); "fique active para ficar online". |
| `jx-loading-skeleton` | `shared/state/loading-skeleton.component.ts` | carga da config, do catálogo, da tabela de frete; salvando. |
| `jx-field` | `shared/components/field/field.component.ts` | todos os inputs de config e de preço (label + erro + máscara + `aria-describedby` + estado). |
| Padrão de painel admin / fila densa | `features/admin/kyc/*` | base de layout para config + catálogo; a fila KYC migra para `jx-data-table` (§3.5). |

**Novos componentes compartilháveis desta phase** (governança `component-library-governance`, ganham story + baseline §10):
- **`jx-data-table`** — primitivo de tabela: `<table>` semântica com header sticky, ordenação acessível, zebra opcional, densidade compacta, slots de célula, ações por linha, e os 3 estados (loading/empty/error) embutidos via componentes da Phase 3. **Reaproveitado** pela fila KYC (Phase 5 refatora) e pelo catálogo de bairros.
- `jx-neighborhood-row` — linha de bairro no catálogo (nome + flag "informal" + status de polígono + ações editar/remover).
- `jx-coverage-list` — lista mobile de cobertura: por bairro, toggle "atendo" + input de preço (modo bairro) + estado de exclusão.
- `jx-availability-toggle` — toggle online/offline do entregador (`role="switch"`).

Tudo abaixo usa **apenas** vars semânticas já existentes. **Nenhuma var semântica nova é necessária.**

---

## 2. Tela 21 (parte A) — Config da área (admin web — F-08 passo 3, D-03)

Superfície **Admin** (web desktop-first, layout sidebar da Phase 3). Item de menu "Configurações" (do wireframe 17). Densa, sóbria, mono nos valores.

### 2.1 Layout e cabeçalho

- **Container:** `<main>` sob a sidebar, `max-width` ~680px (acompanha wireframe 21), margem `--jx-space-5` (24) topo, padding lateral `--jx-space-5`.
- **Voltar:** "← Painel" (`--info`, `font.size.sm`) no topo.
- **H1 (do wireframe):** "Configurações da *área* · {Nome}" — *área* em Fraunces italic `--brand` weight 500 (1 palavra só), `font.size.xl` (22), -.02em. O nome da área (ex. "Pádua") em peso normal.
- **Form único** com `fieldset`s agrupados (saas-dashboard: agrupamento semântico), submetido em bloco.

### 2.2 Agrupamento por `fieldset` (4 seções do wireframe)

Cada `fieldset`: fundo `--surface-elevated`, borda `--border`, radius `lg` (10), padding `--jx-space-4` (16), margem `--jx-space-3` entre seções. `<legend>` em overline: `font.size.xs` (12) weight 600 uppercase letter-spacing .08em `--text-muted` (padrão MASTER/Phase 3).

| Seção (legend) | Campos (via `jx-field`) | Tipo / `inputmode` | Máscara / faixa | Mono? |
|---|---|---|---|---|
| **Validação de entregadores** | Nível exigido | `select` (Simples / Completa) | enum; default da área | — |
| | Exigir certidão de antecedentes | `checkbox` (`role` nativo) | bool | — |
| **Preços e geofence** | Piso de frete por entrega (R$) | `text` `inputmode="decimal"` | **máscara monetária pt-BR** `R$ 0,00`; ≥ 0; passo lógico 0,50 | sim (valor) |
| | Piso de frete por km (R$/km) | `text` `inputmode="decimal"` | máscara monetária `R$ 0,00`; ≥ 0 | sim |
| | Raio de comprovação GPS (metros) | `text` `inputmode="numeric"` | inteiro; faixa 30–300 (RN-005, default 80) | sim |
| | Política de retorno default (%) | `text` `inputmode="numeric"` | 0–100 | sim |
| **Despacho** | Tempo de cada oferta (s) | `text` `inputmode="numeric"` | 10–60 (default 20, ADR-104) | sim |
| | Janela total de favoritos (s) | `text` `inputmode="numeric"` | 20–180 (default 60, ADR-007) | sim |
| **Catálogo de bairros** | (CRUD — §3.3/§3.4) | — | — | — |

- **Microcopy de apoio (`<small>` do wireframe):** sob "Nível exigido": "Simples: CPF + selfie + contatos. Completa: + CNH EAR + CRLV + MEI." — `font.size.xs` `--text-muted`, weight 400.
- **Dois pisos (decisão D-03/D-05):** a área define piso **por entrega** e **por km** (ambos guard-rails). A tabela de frete do entregador (§4) valida contra o piso do modo correspondente.
- **Valores em mono:** todo número de regra (R$, m, s, %) exibido/editado em `font.family.mono`, alinhado à direita no input (padrão wireframe), `font.size.base` (14).

### 2.3 Validação e erros (form-ux-mastery + error-ux-patterns + brazilian-forms)

- Validação **no blur**, um erro por campo abaixo do input, `font.size.xs` `--error`, associado por `aria-describedby`; campo inválido `aria-invalid="true"`, borda `--error`.
- **Máscara monetária (brazilian-forms):** dinheiro NUNCA usa `type="number"` cru — usa `text`/`inputmode="decimal"` com máscara `R$ 0,00` (vírgula decimal, ponto de milhar), normaliza para centavos inteiros ao submeter. Evita perda de zeros à direita e separador errado.
- Faixas fora do limite → erro acionável: ex. "O raio precisa estar entre 30 e 300 metros." · "O tempo de oferta vai de 10 a 60 segundos." · "A política de retorno vai de 0 a 100%."

### 2.4 Salvar com confirmação — ação sensível (F-08 E2, audit)

- **CTA (do wireframe):** "Salvar configurações (auditado)" — full-width ou alinhado à esquerda no rodapé do form; `--brand`/`--brand-contrast`, radius `md`/`lg`, weight 600, ≥44px. O rótulo deixa explícito que a ação é auditada.
- **Confirmação antes de gravar (mudança sensível — piso/geofence/nível mexem na operação):** ao submeter, abre confirmação (sheet/diálogo) listando **o que muda** (before → after dos campos alterados, em mono) e exigindo confirmação. Padrão saas-dashboard para ações sensíveis. Copy: "Você está alterando regras da área. Isso fica registrado no histórico (audit). Confirmar?" + "Confirmar alteração" (`--brand`) / "Cancelar" (texto `--text-muted`).
- **Pós-salvar:** estado `salvando` = CTA desabilitado + `jx-loading-skeleton` no rodapé + `aria-busy`; sucesso = feedback discreto inline "Configurações salvas" (`--success`, `font.size.sm`, `role="status"`) — sem toast festivo; falha = `jx-error-state` `role="alert"` acionável.
- **Audit (F-08 E2 / RN-012):** o backend grava before/after em `audit_log`; a UI só comunica que foi auditado (não renderiza o log aqui — visão de audit é outra tela). `request_id` do erro logado, não exibido.

---

## 3. `jx-data-table` (novo primitivo) + Tela 21 (parte B) — Catálogo de bairros (data-tables-ux, D-01/D-02)

### 3.1 `jx-data-table` — primitivo de tabela compartilhado

Generaliza o que a Phase 5 fez inline na fila de KYC. Tabela densa, acessível, token-driven.

- **Anatomia:** `<table>` semântica dentro de container `--surface-elevated`, borda `--border`, radius `lg` (10), `overflow:hidden` (cantos arredondados como no wireframe 18). `<caption>` (visível ou `sr-only`) descreve a tabela.
- **Header:** `<thead>` sticky no topo do scroll-container, fundo `--surface-sunken`, `<th scope="col">` `font.size.xs` (12) uppercase letter-spacing .06em weight 600 `--text-muted` (overline). Coluna ordenável: botão no `<th>` com indicador + `aria-sort` (`ascending`/`descending`/`none`).
- **Linhas:** `<td>` padding `--jx-space-2`/`--jx-space-3`, `font.size.sm` (13) `--text`, divisor `border-bottom --border` (`neutral.200`/`F2EBE0` claro). Zebra **opcional** via `--surface-elevated` alternado. Hover de linha `--brand-wash`. Dados (IDs, valores, contagens) em `font.family.mono`.
- **Ações por linha:** alinhadas à direita; links/botões `font.size.xs`, área de clique ≥44px (padding compensa a fonte menor). Ação destrutiva (remover) usa `--error` no texto/borda outline, fundo transparente (padrão wireframe 21).
- **Estados embutidos (data-tables-ux — slots):** `loading` = `jx-loading-skeleton` (N linhas-fantasma); `empty` = `jx-empty-state` no lugar do `<tbody>`; `error` = `jx-error-state` `role="alert"` + retry. O componente expõe um modo por entrada (`state: 'loading'|'empty'|'error'|'ready'`).
- **A11y:** `<th scope="col">`/`scope="row"`; ordenação por `aria-sort` + botão real no header (teclado); linha navegável por teclado; sem depender de cor para status (texto+ícone). Densidade compacta mas alvos de ação ≥44px.
- **Responsivo:** desktop = tabela completa; em telas estreitas (se reusada no mobile) colapsa para lista de cards (cada linha vira card empilhado) — não usado no admin desktop, previsto no componente.

### 3.2 Catálogo de bairros — visão (CRUD, escopo de área / AreaScoped)

No wireframe 21 o catálogo é a 4ª `fieldset`. Aqui ele usa `jx-data-table` (lista) + `jx-neighborhood-row` por item + bloco "Adicionar bairro". Escopado por área (RBAC + AreaScoped — D-02).

- **Colunas da tabela de bairros:** Nome (· flag "informal" quando aplicável) · Polígono (status: "Definido" / "Sem polígono — por nome", §3.3) · Ações ("Editar polígono" · "Remover").
- **`jx-neighborhood-row` (linha):** nome `font.size.sm` (13) `--text`; se informal, selo `font.size.2xs` (11) `--text-muted` "informal" (do wireframe: "bairro informal — incluído pelo gestor"). Status de polígono = badge texto+ícone (§3.3). Ação "Remover" = botão outline `--error` (texto + borda `--error`, fundo transparente).
- **Bairro sem polígono é válido (D-01):** funciona por nome; a coluna Polígono mostra "Sem polígono — por nome" sem tratá-lo como erro (é o default `neighborhood`). Polígono é opcional no M1.

### 3.3 Entrada de polígono — GeoJSON / coordenadas (Discretion D-01; desenho no mapa deferido)

**Nenhum mapa nesta phase** (mapa interativo = Phase 9). Polígono entra por texto, em mono.

- **Adicionar/editar polígono:** dentro da linha (ou sheet de edição) abre um `<textarea>` `font.family.mono` `font.size.xs` (12) para colar **GeoJSON** (`Polygon`/`MultiPolygon`, SRID 4326) **ou** lista de coordenadas `lng,lat` por linha. Label: "Polígono (GeoJSON ou coordenadas) — opcional".
- **Validação (sem mapa):** valida sintaxe GeoJSON / pares de coordenadas no blur; faixa plausível (lng −180..180, lat −90..90); polígono fechado (1º ponto = último, ou auto-fecha). Erro acionável: "GeoJSON inválido. Cole um Polygon com pares lng,lat." / "Coordenada fora de faixa. Use lng entre −180 e 180." Estado válido → badge "Polígono definido" (`--success`, check).
- **Status de polígono (badge texto+ícone+cor):**

| Status | Badge texto | Token cor | Fundo | Ícone |
|---|---|---|---|---|
| Definido | "Polígono definido" | `--success` | `--success-bg` | check |
| Por nome (sem polígono) | "Por nome" | `--text-muted` | `--surface-sunken` | hash/marcador |
| Inválido (na edição) | "Revisar coordenadas" | `--error` | `--error-bg` | alerta |

- No **dark**, fundos `_bg` claros não funcionam → herda padrão Phase 3: fundo `--surface-elevated` + texto/borda na cor semântica viva.

### 3.4 Adicionar / remover bairro (CRUD)

- **Adicionar (do wireframe):** rótulo "Adicionar bairro" + linha com `jx-field` texto (`name=new_neighborhood`, placeholder "Nome do bairro", `flex:1`) + botão "Adicionar" (`--text`/escuro `neutral.800` fill — botão secundário sóbrio do wireframe, NÃO persimmon, para diferenciar de ação primária). Após adicionar, abre opcionalmente o `<textarea>` de polígono (§3.3).
- **Remover — bloqueio com entregas ativas (do wireframe / regra):** remover bairro com entregas ativas é **proibido**. Tentar remover → `jx-error-state` `role="alert"`: **"Não é possível remover \"{Centro}\": há entregas ativas nesse bairro. Arquive primeiro."** (texto do wireframe). Bairro sem entregas → remove com confirmação leve.
- **Microcopy (`<small>` do wireframe):** "Remover bairro com entregas ativas não é permitido — arquive primeiro." `font.size.xs` `--text-muted`.

### 3.5 Refatoração da fila KYC + tabelas admin sobre `jx-data-table` (governança)

- A fila de KYC (Phase 5 `jx-kyc-queue-table`), a listagem de entregadores (tela 18) e o bloco de filas do dashboard (tela 17) passam a **consumir `jx-data-table`** (DRY de governança). **Não redesenha** colunas nem semântica já especificadas na Phase 5 — só troca a implementação inline pelo primitivo. Status badges (active/pending/suspended do wireframe 18) seguem o vocabulário texto+ícone+cor já estabelecido. **Nenhum novo contrato visual** para essas tabelas além de "usam o primitivo".

---

## 4. Tela 10 — Cobertura + preços do entregador (Ionic mobile-first — RN-003 / RN-015, D-04/D-05)

Superfície **Entregador** = Ionic 8 dentro do shell `ion-tabs` (Phase 3). Rota dedicada (ex. `/entregador/bairros-precos`). `ion-content` `--surface`, conteúdo centrado `max-width` 420px (do wireframe), padding `--jx-space-4` (16), **safe-area insets** respeitados.

### 4.1 Cabeçalho e aviso de contexto (RN-003)

- **H1 (do wireframe):** "Bairros e *preços*" — *preços* em Fraunces italic `--brand` weight 500 (1 palavra), `font.size.xl` (22), -.02em.
- **Aviso de cobertura (RN-003) — `jx-warn-banner` (`role="status"`, não-dispensável, informativo):** "Você só recebe ofertas quando a coleta **E** a entrega estão nos seus bairros. Piso da cidade: **R$ 6,00**." O valor do piso vem da config da área (§2) — **mono**, nunca hardcoded. Tokens `--warning`/`--warning-bg` (dark: `--surface-elevated` + `--warning` vivo, borda esquerda 3px).

### 4.2 `jx-coverage-list` — seleção de cobertura + preço por bairro (modo bairro)

Lista vertical dos bairros do catálogo da área. Cada bairro é uma linha (do wireframe: `label` com checkbox + input de preço).

- **Anatomia da linha:** `--surface-elevated` card agrupando a seção; cada linha com divisor `--border` (`neutral.200`). À esquerda: **checkbox "atendo"** (`role` nativo, ≥20px, área de toque ≥44px) + nome do bairro `font.size.base` (14) `--text`. À direita: **input de preço por entrega** `jx-field` compacto, `inputmode="decimal"`, máscara `R$ 0,00`, **mono**, alinhado à direita, largura ~90px (do wireframe).
- **Bairro não atendido (checkbox off):** input de preço **desabilitado** (`disabled`, placeholder "—"), `--text-subtle` — exatamente como o wireframe (Cidade Nova / Divinéia off). Ativar o checkbox habilita o input.
- **Exclusões (RN-003 / D-04):** um bairro pode ser marcado como **exclusão explícita** (veta coleta E entrega mesmo dentro de área coberta). UI: além de "atendo/não atendo", um estado "Excluir" (toggle secundário ou ação na linha) que marca a linha com selo "Excluído" (`--text-muted` + ícone bloqueio, texto+ícone). Exclusão **prevalece** sobre cobertura. Microcopy: "Bairros excluídos não recebem ofertas nem na coleta nem na entrega."
- **Toque (gesture-touch):** linha inteira tocável para alternar "atendo"; input de preço foca direto. Feedback scale .97 `motion.fast`. Sem swipe destrutivo.

### 4.3 Modo bairro × modo km (RN-015, Discretion CONTEXT)

O entregador define a tabela por **bairro** OU por **km**. Seletor no topo da seção de preços.

- **Seletor de modo:** segmented control (Ionic `ion-segment` ou toggle de 2 opções) "Por bairro" / "Por km", `role="radiogroup"`. Só um modo ativo; trocar de modo preserva os dados do outro (não apaga).
- **Modo bairro:** `jx-coverage-list` (§4.2) — preço por entrega por bairro.
- **Modo km:** faixas por km — lista editável de faixas `{ até_km, preço }` (ex. "até 3 km · R$ 7,00"), botão "Adicionar faixa". Valores em mono, `inputmode="decimal"` para preço / `inputmode="numeric"` para km. Cada faixa valida contra o piso por km (§2.2).
- **Cobertura é independente do modo de preço:** a seleção de bairros que atende (§4.2 checkboxes) define elegibilidade (RN-003); o modo só muda como o preço é calculado. Em modo km, a seleção de bairros continua visível (sem o input de preço por bairro).

### 4.4 Retorno (% sobre a corrida)

- **Bloco "Retorno" (do wireframe):** card `--surface-elevated`; `jx-field` numérico (`inputmode="numeric"`, 0–100) "% sobre a corrida para voltar com o item", mono. Default herdado da política de retorno da área (§2.2) mas editável pelo entregador dentro do permitido. Copy: "Retorno (quando o destinatário recusa)".

### 4.5 Validação de PISO — rejeição citando o piso (RN-015 — núcleo desta tela)

Regra dura: a plataforma **nunca fixa** o preço; só impõe piso e rejeita abaixo dele com mensagem que **cita o valor do piso**.

- **Validação inline (no blur do preço):** se preço < piso (do modo correspondente), o `jx-field` daquele bairro/faixa entra em erro: borda `--error`, `aria-invalid="true"`, e mensagem por `aria-describedby`.
- **Erro global ao salvar (do wireframe):** se algum preço está abaixo do piso, bloqueia salvar e mostra `jx-error-state` `role="alert"` acima do CTA: **"O preço de {Vila Nova} está abaixo do piso da cidade (R$ 6,00). Ajuste para salvar."** — o valor do piso **sempre citado** (mono), vindo da config da área. Foco move ao alerta; o(s) campo(s) infrator(es) ficam `aria-invalid`.
- **Sem dark pattern:** a plataforma sugere (pode pré-preencher uma sugestão), mas o entregador edita livremente acima do piso. Nada força um preço específico.
- **CTA (do wireframe):** "Salvar bairros e preços" — full-width, `--brand`/`--brand-contrast`, ≥44px, radius `md`/`lg`, weight 600. Estado `salvando` = desabilitado + skeleton + `aria-busy`.

### 4.6 Motion (gesture-touch + reduced-motion)

- Toque em checkbox/segment/CTA: scale .97 `motion.fast` (140ms). Troca de modo bairro↔km: fade `motion.normal` (220ms) `easing_out`. **`prefers-reduced-motion`** → sem scale/transição.

---

## 5. `jx-availability-toggle` — online/offline (entregador — D-06)

Toggle de disponibilidade. `busy` é **derivado** (Phase 8) — aqui só online/offline.

- **Onde:** topo do início/perfil do entregador (shell Ionic). Componente proeminente (decisão clara de estado).
- **Anatomia:** `role="switch"` com `aria-checked`. Pílula `radius.full`, ≥44px de altura. Estado **online** = fundo `--success`-derivado (trilho `--success`, texto `--brand-contrast`/claro) + rótulo "Online" + ponto/ícone; estado **offline** = trilho `--surface-sunken` + rótulo "Offline" `--text-muted`. **Status comunicado por texto + posição + ícone**, nunca só cor.
- **Só `active` pode ficar online (D-06):** se o entregador não está `active` (KYC pendente/reprovado — Phase 5), o toggle fica **desabilitado** e um `jx-warn-banner` (`role="status"`) explica: "Termine sua validação para ficar online e receber ofertas." + CTA "Ver validação" (`--info`). Não-bloqueante, mas o toggle não liga.
- **Feedback:** ao alternar, transição `motion.normal`; estado anunciado `aria-live="polite"` ("Você está online" / "Você está offline"). Sem festividade.
- **Estado pronto para despacho (Phase 8):** a UI só reflete/edita online/offline; o consumo (entrar na cascata de ofertas) é Phase 8. `busy` derivado da carga **não** é editável aqui (read-only/ausente nesta phase).

---

## 6. Estados (loading / vazio / erro) — reuso Phase 3

Toda tela cobre os estados reusando os componentes canônicos. Copy pt-BR (causa + ação).

| Estado | Onde | Componente | Copy |
|---|---|---|---|
| **Vazio — catálogo sem bairros** | admin, tela 21 catálogo | `jx-empty-state` (com CTA) | Título "Nenhum bairro cadastrado ainda." Causa/ação: "Adicione o primeiro bairro da {Pádua} para a operação começar." + CTA "Adicionar bairro" (`--brand`). |
| **Vazio — entregador sem cobertura** | entregador, tela 10 | `jx-empty-state` | "Você ainda não atende nenhum bairro. Marque os bairros que quer atender abaixo." (sem CTA falso — a ação são os checkboxes na própria tela). |
| **Erro — preço abaixo do piso** | entregador, tela 10 | `jx-error-state` `role="alert"` | "O preço de {bairro} está abaixo do piso da cidade (R$ 6,00). Ajuste para salvar." (piso citado, mono). |
| **Erro — remoção bloqueada** | admin, catálogo | `jx-error-state` `role="alert"` | "Não é possível remover \"{Centro}\": há entregas ativas nesse bairro. Arquive primeiro." |
| **Erro — salvar config falhou** | admin, config | `jx-error-state` `role="alert"` | "Não conseguimos salvar as configurações. Tente de novo em instantes." + "Tentar de novo". |
| **Erro — GeoJSON inválido** | admin, polígono | `jx-field` erro inline | "GeoJSON inválido. Cole um Polygon com pares lng,lat." |
| **Loading — carga / salvando** | todas | `jx-loading-skeleton` | skeleton do layout real (linhas de tabela, campos de config, lista de cobertura). |
| **Toggle indisponível (não-active)** | entregador, online | `jx-warn-banner` `role="status"` | "Termine sua validação para ficar online e receber ofertas." + "Ver validação". |

- **Vazio ≠ erro:** catálogo sem bairros é estado legítimo (`role="status"`), não alerta. Preço abaixo do piso e remoção bloqueada são `role="alert"` (interrompem a ação).

---

## 7. Acessibilidade (accessibility-pro — AA nos dois temas, DEC-001)

- **Contraste AA nos DOIS temas:** herda mapas validados da Phase 3 (`--text`/`--surface`, `--brand-contrast`/`--brand`, semânticos sobre superfície escura no dark). Tabela, badges de polígono, toggle online e os valores mono validados claro+dark pelo checker (axe + contraste).
- **Tabelas acessíveis (data-tables-ux):** `<table>` semântica com `<caption>`; `<th scope="col">` no header e `scope="row"` na 1ª célula quando faz sentido; coluna ordenável com **botão real** + `aria-sort` (`ascending`/`descending`/`none`); navegação por teclado; status de linha por **texto + ícone**, nunca só cor.
- **Toggles:** `jx-availability-toggle` e o segmented bairro/km com `role="switch"`/`role="radiogroup"` + `aria-checked`/`aria-current`; estado anunciado em `aria-live="polite"`; operável por teclado (Space/Enter/setas).
- **Foco visível:** `--focus-ring` (`shadow.focus`) em todo interativo — campos de config, máscara monetária, textarea de polígono, checkboxes de cobertura, segmented, toggle online, ações de linha. Nunca `outline:none` sem substituto.
- **Touch ≥44×44px (mobile/entregador):** checkbox "atendo" (área de toque), input de preço, segmented bairro/km, toggle online, CTA "Salvar bairros e preços". Admin: ações de linha "Editar/Remover", "Adicionar", CTA "Salvar configurações" com área de clique ≥44px.
- **Labels e erros:** todo input com `<label for>`; cada erro associado por **`aria-describedby`**; `aria-invalid="true"` no campo abaixo do piso / fora de faixa / GeoJSON inválido. Máscara monetária não quebra leitor de tela (valor lido como número).
- **Live regions:** `jx-error-state` `role="alert"` (piso, remoção, salvar); `jx-warn-banner`/`jx-empty-state`/sucesso de salvar `role="status"`; skeleton `aria-hidden` + container `aria-busy`; troca de estado online/offline e troca de modo de preço anunciadas `aria-live="polite"`.
- **Status nunca só por cor:** badges de polígono, selo de exclusão e estado online/offline sempre com **texto + ícone** além da cor.
- **Teclado:** ordem de tabulação lógica (config: por seção; tela 10: aviso → modo → lista → retorno → salvar); Enter submete; segmented por setas; `prefers-reduced-motion` desliga scale/transições.
- **`lang="pt-BR"`**, landmarks `<main>`/`<nav>` (sidebar admin / tabbar entregador)/`<section>`/`<table>`. `axe-core` na config, no catálogo e na tela de cobertura: zero violações críticas (verificação ROADMAP).

---

## 8. Direção estética (ui-ux-pro-max — anti AI-slop)

- **Mono em todo dado técnico:** R$ (piso, preços, faixas km), metros (geofence), segundos (timeouts), % (retorno), **coordenadas/GeoJSON**, nome-código de bairro/IDs. `font.family.mono`, alinhado à direita em inputs numéricos.
- **Fraunces italic** só em 1 palavra-chave por H1 (config: *área*; tela 10: *preços*), cor `--brand`, weight 500. Nunca em tabela, label, valor, erro.
- **Persimmon como única cor de ação:** CTAs primários `--brand`; ações secundárias = outline `--brand` ou neutro escuro sóbrio (botão "Adicionar" do wireframe). Destrutivo = `--error` outline.
- **Anti-slop explícito:** sem gradiente, sem card "glow", sem toggle neon, sem mapa decorativo, sem confete ao salvar. Painel admin denso e sóbrio; tela do entregador limpa e direta. Elevação por `--surface-elevated`, não por sombra exagerada.

---

## 9. Tabela de tokens citados (Gate 2 — todos existem em `tokens.json`)

Cada token referenciado, com caminho em `docs/identidade-visual/tokens.json`. **Confirmado: 100% existem (zero inventados).** Toda var semântica usada (`--surface`, `--surface-elevated`, `--surface-sunken`, `--text`, `--text-muted`, `--text-subtle`, `--border`, `--border-strong`, `--brand`, `--brand-contrast`, `--brand-wash`, `--success`, `--success-bg`, `--warning`, `--warning-bg`, `--error`, `--error-bg`, `--info`, `--info-bg`, `--focus-ring`) já está em `apps/web/src/styles/_semantic.scss` (Phase 3), derivada das primitivas abaixo.

| Token (caminho em tokens.json) | Valor | Existe? |
|---|---|---|
| `color.brand.50` | #FFF1E8 | ✅ |
| `color.brand.100` | #FFDEC1 | ✅ |
| `color.brand.300` | #FFA56B | ✅ |
| `color.brand.400` | #FB813D | ✅ |
| `color.brand.500` | #E84E1B | ✅ |
| `color.brand.600` | #C73E0F | ✅ |
| `color.brand.800` | #6F2308 | ✅ |
| `color.brand.900` | #421405 | ✅ |
| `color.neutral.50` | #FAF6EE | ✅ |
| `color.neutral.100` | #F2EBE0 | ✅ |
| `color.neutral.200` | #E5DBCC | ✅ |
| `color.neutral.300` | #C8BAA5 | ✅ |
| `color.neutral.400` | #9D8E7A | ✅ |
| `color.neutral.500` | #6B5F50 | ✅ |
| `color.neutral.600` | #4A4136 | ✅ |
| `color.neutral.700` | #2D261F | ✅ |
| `color.neutral.800` | #181410 | ✅ |
| `color.neutral.900` | #0A0805 | ✅ |
| `color.semantic.success` | #1B998B | ✅ |
| `color.semantic.success_bg` | #D6F1ED | ✅ |
| `color.semantic.warning` | #E89B0E | ✅ |
| `color.semantic.warning_bg` | #FFF1D2 | ✅ |
| `color.semantic.error` | #C71D1D | ✅ |
| `color.semantic.error_bg` | #F9DCDC | ✅ |
| `color.semantic.info` | #0A66C2 | ✅ |
| `color.semantic.info_bg` | #DDEBFA | ✅ |
| `spacing.2` / `.3` / `.4` / `.5` (8/12/16/24px) | — | ✅ |
| `radius.md` / `lg` / `full` (6/10/9999px) | — | ✅ |
| `font.family.display` | Inter Tight… | ✅ |
| `font.family.serif_accent` | Fraunces… | ✅ |
| `font.family.mono` | JetBrains Mono… | ✅ |
| `font.size.2xs` / `xs` / `sm` / `base` / `xl` (11/12/13/14/22) | — | ✅ |
| `font.weight.regular` / `medium` / `semibold` (400/500/600) | — | ✅ |
| `shadow.focus` (→ `--focus-ring`) | rgba(232,78,27,.28) | ✅ |
| `motion.fast` / `normal` / `easing_out` (140/220ms / cubic-bezier) | — | ✅ |

**Tokens referenciados que NÃO existem em tokens.json: NENHUM (0).** Nenhuma var semântica nova foi necessária — a Phase 6 reusa integralmente as 21 vars da Phase 3. Gate 2 satisfeito.

---

## 10. Visual regression (baseline desta phase)

Novos componentes/telas que recebem story + baseline (`product/visual-regression-testing`):

- [ ] `jx-data-table` — stories: ready, com-zebra, ordenado, loading, vazio, erro · claro+dark
- [ ] `jx-neighborhood-row` — stories: com-polígono, sem-polígono (por nome), informal, edição-textarea, geojson-inválido · claro+dark
- [ ] `jx-coverage-list` — stories: bairro-atendido, não-atendido (preço disabled), excluído · claro+dark · mobile
- [ ] `jx-availability-toggle` — stories: online, offline, desabilitado (não-active) · claro+dark · mobile
- [ ] `config-area` (tela 21 parte A) — stories: form-completo, validando, confirmação-sensível (before/after), erro-faixa · claro+dark
- [ ] `catalogo-bairros` (tela 21 parte B) — stories: com-bairros, vazio (empty-state), remoção-bloqueada · claro+dark
- [ ] `entregador-cobertura-precos` (tela 10) — stories: modo-bairro, modo-km, preço-abaixo-do-piso (erro), retorno, sem-cobertura (vazio) · claro+dark · mobile

Nome screenshot: `{component}-{state}-{theme}-{viewport}.png`.

---

## 11. Open questions para o humano

- [ ] **Exclusão de bairro (RN-003):** o wireframe 10 só mostra checkbox "atendo/não atendo". Modelei a **exclusão explícita** (veta os dois pontos mesmo dentro de área coberta) como estado adicional na linha. **Recomendação:** no M1, "não atendo" já basta como veto; a exclusão explícita só importa quando houver herança de polígono que cubra o bairro automaticamente. Confirmar se M1 precisa do estado "Excluído" separado ou se "não atendo" cobre.
- [ ] **Dois pisos (por entrega + por km):** D-03 lista piso "por km e por entrega". Modelei dois campos na config e validação por modo. **Recomendação:** manter ambos (cada um valida o modo correspondente da tabela do entregador). Confirmar se M1 quer só um dos dois.
- [ ] **Polígono — formato aceito:** GeoJSON `Polygon` **e** lista de coordenadas `lng,lat`? **Recomendação:** aceitar os dois (GeoJSON colado de ferramentas + coordenadas manuais), validar sintaxe sem mapa. Desenho no mapa é Phase 9+ (deferido). Confirmar.

---

## Approval

- [ ] Humano revisou e aprovou (ou delegou ao ui-checker)
- [ ] ui-checker validou 6 dimensões: tokens, tipografia, copy, estados, interações, acessibilidade
- [ ] Gate 2 (Visual Contract) verde — tokens citados existem em tokens.json (§9)
- [ ] Wireframe-contract de `10`, `17`, `18`, `21` coberto (verificação ROADMAP) — `17`/`18` reusam o contrato Phase 3/5 + migram para `jx-data-table` (§3.5); despacho (Phase 8) e detalhe de entregador (Phase 5) ficam fora.
- [ ] Aprovado em: {date}

**Próximo passo:** `/gsd:plan-phase 6` — o planner recebe este UI-SPEC como contrato de design.
