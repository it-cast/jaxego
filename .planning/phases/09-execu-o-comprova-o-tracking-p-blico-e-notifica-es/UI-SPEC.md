---
phase: 09-execu-o-comprova-o-tracking-p-blico-e-notifica-es
title: Execução, comprovação, tracking público e notificações
status: draft
platform: mobile (Entregador — Ionic, mobile-first) + Loja (web responsivo) + Tracking público (web, SEM login, mobile-first)
gate2_visual_contract: pending-checker
generated_by: gsd-ui-researcher
generated_at: 2026-06-10
reuses: 03-shell-frontend-design-system-3-superf-cies, 05-cadastro-do-entregador-kyc, 07-cria-o-de-entrega-m-quina-de-estados, 08-despacho-em-cascata-oferta-aceite
---

# UI-SPEC — Phase 9: Execução, comprovação, tracking público e notificações

> Design contract. Gerado por `gsd-ui-researcher` em 2026-06-10. Aprovado por `gsd-ui-checker` em {date}.
> **BLOQUEIA** `plan-phase` se não existir (Gate 2 — Visual Contract).
> Plataforma: **3 superfícies** — Entregador (Ionic mobile-first), Loja (web responsivo), Tracking público (web SEM login).
> **Regra de ouro Gate 2:** todo valor visual é token semântico (`--surface`, `--brand`, `--state-*`…) derivado de `docs/identidade-visual/tokens.json`. Nenhum `#hex` hardcoded. Toda referência a token neste doc existe em tokens.json (ver §11). **A maior phase de UI do M1** — fecha o ciclo operacional F-06.

---

## Fontes de verdade consultadas

- `docs/identidade-visual/tokens.json` — tokens **canônicos**. FONTE da verdade visual. Atenção a `color.delivery_state.*` (7 estados, base da timeline e dos badges).
- `.planning/phases/09-.../09-CONTEXT.md` — D-01..D-10, DEC-002 (mapa tempo real M1 / ADR-101 promovida), DEC-001 (dark mode M1).
- `.planning/phases/03-.../UI-SPEC.md` — sistema de temas (21 CSS vars semânticas), tipografia, motion, componentes de estado canônicos. **HERDADO integralmente.**
- `.planning/phases/08-.../UI-SPEC.md` + `apps/web/src/features/entregador/oferta/offer-sheet.component.ts` — padrão de sheet, sem swipe-em-ação-crítica, RN-013 (destino só bairro antes da coleta).
- Componentes existentes (`apps/web/src/shared/`): `jx-state-badge`, `jx-doc-upload` (base da câmera de comprovação — Phase 5), `jx-empty-state`, `jx-error-state`, `jx-loading-skeleton`, `jx-warn-banner`, `jx-accepted-courier-card`, `jx-score-chip`. **REUSE.**
- `apps/web/src/layouts/entregador-shell.component.ts` — shell Ionic (tabs Início/Entregas/Ganhos/Perfil).
- `projeto/wireframes/06-entregador-entrega-ativa.html`, `07-entregador-comprovacao.html`, `13-loja-detalhe-entrega.html`, `26-tracking-publico.html` — contratos DOM.
- `projeto/regras-negocio/fluxos.md` §F-06 (`:109-128`) — passos 1-8 + exceções E1-E6.
- `projeto/regras-negocio/regras.md` — RN-004 (cancelamento), RN-005/RN-017 (foto+GPS geofence), RN-013 (endereço destino), RN-018 (notificações/SMS), RN-022 (janela telefones), RN-026 (confirmação pagamento direto).
- `.planning/ROADMAP.md` Phase 9 — flags (has_ui, has_api, mobile, integration_check, has_pii, has_external_users), DEC-002, skills.

### Skills aplicadas (matriz UI + flags da Phase 9)

| Skill | Decisão de design que ela ancora |
|---|---|
| `ux-advanced/design-tokens-system` | Tudo via CSS vars semânticas herdadas da Phase 3; mapa e timeline também (§1, §11). |
| `ux-advanced/dark-mode-theming` | Dois temas, **inclusive o mapa** (filtro/tiles dark) e a timeline (§7.4, §6). |
| `ui-ux-pro-max` | Estética editorial-técnica: timeline tipográfica forte, mono em IDs/ETA/valores, persimmon como acento. Anti-AI-slop: nada de "card flutuante genérico com gradiente" no tracking. |
| `quality/accessibility-pro` | AA dois temas, foco visível, touch ≥44px, aria-live em mudança de estado, **mapa com alternativa textual** (§9). |
| `ux-advanced/empty-states-polish` | Tracking sem dados, comprovações vazias, link inválido — causa + ação. |
| `br/ux-copywriting-ptbr` | Toda copy sentence case, CTA verbo+objeto, erro = o que houve + o que fazer (§10). |
| `quality/error-ux-patterns` | GPS fora do raio, número não confere, upload offline — acionáveis, não bloqueiam para sempre. |
| `ux-advanced/gesture-touch-patterns` | **Sem swipe em ação crítica** (cheguei/confirmar = botão deliberado ≥52px); tap-to-enlarge na foto; pan do mapa não conflita com scroll (§2, §3). |
| `ux-advanced/file-upload-ux` | Captura de foto reusa `jx-doc-upload`; preview, compressão, retry, progresso (§3). |
| `mobile/offline-first` | Upload offline-tolerante (pending_upload); polling resiliente; banner de fila pendente (§4). |
| `mobile/push-notifications-architecture` | Padrão visual de push/in-app nos 3 momentos + opt-in (§8). |
| `ux-advanced/trust-safety-ux` | Tracking público: só PII permitida do entregador, footer de procedência, sem rastreio invasivo (§6, §9). |
| `quality/performance-web-vitals` | Mapa **lazy-load** abaixo da timeline; LCP é a timeline (texto), não o mapa; tiles não bloqueiam render (§6.5). |
| `quality/observability-production` | `request_id` em erro; mudança de estado logada (sem PII). |

---

## Telas / estados cobertos por esta fase

| # | Tela / artefato | Superfície | Wireframe | Seção |
|---|---|---|---|---|
| 1 | **Entrega ativa** (rota, cheguei, ligar/mensagem, estado) | Entregador (Ionic) | `06` | §2 |
| 2 | **Comprovação** (câmera+GPS/geofence, nº referência, pagamento direto, ausente/recusa) | Entregador (Ionic) | `07` | §3 |
| 3 | **Fila de upload offline** (pending_upload) | Entregador | — (novo) | §4 |
| 4 | **Detalhe da entrega** (timeline, estado, card entregador, comprovações, cancelar) | Loja (web) | `13` | §5 |
| 5 | **Tracking público** (timeline 7 estados, ETA, mapa ao vivo) — SEM login | Web público | `26` | §6 |
| 6 | **Mapa ao vivo** (peça nova central — MapLibre/OSM, dark, perf, a11y) | Loja + público | — (novo) | §6.4-6.5, §7.4 |
| 7 | **Notificações** (push/in-app, 3 momentos + opt-in) | Entregador + Loja + destinatário | — (novo) | §8 |

**Estados obrigatórios por tela** (REQ-055): loading / sucesso / vazio / erro / **offline-mobile**. Reusam os componentes de estado da Phase 3.

**Fora de escopo (deferido):** cobrança online cartão/PIX/escrow (Phase 10); fatura mensal, mediação completa de disputa, saques (Phase 11); score com peso (Phase 13); OTP de comprovação (TD-003); antifraude de foto por IA (TD-008). **NÃO especificar aqui.**

---

## 0. Reuso do design system (Phases 3-8) — herança e o que é NOVO

### 0.1 Herdado SEM redefinir (vem da Phase 3, não repetir)

- **Sistema de temas:** 21 CSS vars semânticas (`--surface`, `--surface-elevated`, `--surface-sunken`, `--text`, `--text-muted`, `--text-subtle`, `--border`, `--brand`, `--brand-contrast`, `--brand-wash`, `--success`, `--warning`, `--error`, `--info` + `_bg`), sombras warm, `--focus-ring`. Claro + dark via `data-theme`. Anti-FOUC já resolvido.
- **Tipografia:** Inter Tight (UI), Fraunces italic (1 palavra-chave/título, `--brand`), JetBrains Mono (IDs, ETA, valores, timestamps, placas). Escala `font.size.*`, line-height corpo 1.5 / heading 1.2.
- **Spacing / radius / motion:** escalas de tokens; press scale .97 `fast`; `prefers-reduced-motion` respeitado.
- **Shell entregador:** `jx-entregador-shell` (Ionic tabs). Entrega ativa e comprovação vivem na aba **Entregas** (full-screen sobre o conteúdo da aba, sem tabbar visível durante a operação ativa — foco na tarefa).

### 0.2 Componentes REUSADOS (não respecificar — só compor)

| Componente | Origem | Uso na Phase 9 |
|---|---|---|
| `jx-state-badge` | Phase 7 | Estado da entrega no topo de 06, em 13 e no banner do tracking. Já mapeia os 7 estados → `--state-*` (texto+ícone+cor, nunca cor só). **Vocabulário já definido**, ver tabela abaixo. |
| `jx-doc-upload` | Phase 5 | **Base da câmera de comprovação.** Mesma máquina (idle→selecting→compressing→uploading→success→error), preview, retry, progresso aria-live, `capture="environment"`. **Estendido** com camada de GPS/geofence (§3.2) — wrapper `jx-proof-capture`, não fork. |
| `jx-empty-state` | Phase 3 | Tracking sem dados, comprovações vazias. |
| `jx-error-state` | Phase 3 | Link de rastreio inválido/expirado; falha de carregamento; GPS bloqueante. |
| `jx-loading-skeleton` | Phase 3 | Timeline e mapa carregando (skeleton do layout real, não spinner). |
| `jx-warn-banner` | Phase 3 | Conexão instável, fila de upload pendente, posição desatualizada no mapa. |
| `jx-accepted-courier-card` | Phase 8 | Card do entregador em 13 (loja). Já omite localização ao vivo por design (TH-3). |
| `jx-score-chip` | Phase 5/8 | Score do entregador em 13 e no card público (valor limitado). |

**Vocabulário do `jx-state-badge` (já implementado — usar como está):**
`CRIADA` "Procurando" · `ACEITA` "Aceita"/"Indo coletar" · `COLETADA` "A caminho" · `ENTREGUE` "Entregue" · `RECUSADA_NO_DESTINO` "Recusada no destino" · `CANCELADA` "Cancelada" · `FINALIZADA` "Finalizada". Cores de `color.delivery_state.*`.

### 0.3 Componentes NOVOS desta phase

| Componente | Selector | O que é | Skill-âncora |
|---|---|---|---|
| Captura de comprovação | `jx-proof-capture` | Wrapper de `jx-doc-upload` + feedback GPS/geofence + estado de retentativas (3→low_confidence). | file-upload-ux, gesture-touch, offline-first |
| Pílula de GPS/geofence | `jx-geofence-pill` | Status inline "dentro/fora do raio" (text+ícone, nunca cor só). | error-ux-patterns, a11y |
| Confirmação de pagamento direto | `jx-direct-payment-confirm` | Fieldset "Recebi R$ X / Não recebi". | trust-safety-ux, error-ux |
| Banner de fila offline | `jx-pending-upload-banner` | Fila de fotos aguardando reconexão. | offline-first |
| Timeline de tracking | `jx-tracking-timeline` | Os 7 estados em linha do tempo vertical (reusada em 13 e 26). | empty-states, a11y |
| Banner de estado/ETA | `jx-tracking-banner` | "A caminho — chega em ~6 min" no topo do tracking. | a11y (aria-live) |
| Mapa ao vivo | `jx-live-map` | MapLibre GL JS + tiles OSM, posição aproximada do entregador, **lazy + dark + alternativa textual**. | performance-web-vitals, dark-mode, trust-safety, a11y |
| Toast / push pattern | `jx-notice` | Padrão visual de notificação in-app (espelha o push). | push-notifications-architecture |

---

## 1. Princípios visuais desta phase (editorial-técnica aplicada)

- **A timeline é a UI principal, não o mapa.** A timeline (texto + tempos em mono) é a fonte da verdade e o LCP do tracking; o mapa é enriquecimento progressivo (§6.5). Isto é intencional (perf + a11y + trust).
- **Mono carrega o dado:** ETA (`~6 min`), distância (`0,8 km`), `delivery_id` (`dlv_01HXAQ3K9P`), placa, horários (`14:36:12`), valor (`R$ 8,50`) — sempre `font.family.mono`. Texto narrativo em Inter Tight.
- **Persimmon é acento, não preenchimento:** estado atual da timeline, foco, e o ponto "agora" no mapa usam `--brand`/`--state-coletada`. Ações primárias de operação crítica (cheguei, confirmar) usam superfície escura `--text` (carvão) com texto `--brand-contrast` — alto contraste, sóbrio, igual ao wireframe 06.
- **Sem AI-slop:** nada de gradiente decorativo no mapa, sem glassmorphism no banner de ETA, sem "moto animada saltitante". Movimento só onde comunica progresso real.

---

## 2. Entrega ativa (tela 06 — Entregador, Ionic mobile-first)

A tela full-screen da aba Entregas durante uma entrega `ACEITA`/`COLETADA`. Reusa shell Ionic; tabbar oculta durante a operação ativa (foco na tarefa).

### 2.1 Anatomia (top→bottom)

| Bloco | Conteúdo | Tokens |
|---|---|---|
| **Mapa de rota** (topo, ~280-300px) | `jx-live-map` em modo "rota própria" (você → coleta, ou você → destino após COLETADA). Overlay: `jx-state-badge` (canto sup. esq.) + `delivery_id` em mono (canto inf. dir.). | fundo `--surface-sunken`; pill `--surface-elevated`; badge via `--state-*` |
| **Overline de progresso** | "INDO COLETAR · ~4 min · 0,8 km" (uppercase, mono nos números) | `font.size.2xs/xs`, letter-spacing .08em, `--text-muted`; números mono |
| **Título + endereço** | `<h1>` nome da loja/destino; endereço abaixo | h1 `font.size.xl` (20-22), -.02em, `--text`; endereço `font.size.base` `--text-muted` |
| **Ações de contato** | Grid 2col: "Ligar" (`tel:`) · "Mensagem" (chat) | botões outline `--border-strong`, texto `--text-muted`, weight 600, ≥44px |
| **CTA primário** | "Cheguei na coleta" → "Confirmar coleta"; depois "Cheguei no destino" → "Comprovar entrega" | full-width, padding `--jx-space-4`, **fundo `--text` (carvão)**, texto `--brand-contrast`, radius `lg`, ≥52px, press scale .97 `fast` |
| **Link de problema** | "Não consigo concluir esta entrega" (E5) | botão texto sublinhado `--error`, ≥44px |
| **Mini-stepper** | Lista ordenada dos passos (aceita→coletar→entregar→comprovar); destino "endereço aparece após a coleta" (RN-013) | `font.size.xs`; done `--success`, current `--brand` weight 600 |

### 2.2 Estados e regras

| Estado | Comportamento | A11y |
|---|---|---|
| **ACEITA (indo coletar)** | rota até a coleta; CTA "Cheguei na coleta". Destino exibido só como **bairro** (RN-013). | — |
| **Cheguei na coleta** | confirma chegada (loja vê status); abre fluxo de foto da coleta (§3). | — |
| **COLETADA → a caminho** | `jx-state-badge` muda para "A caminho"; **endereço completo do destino revelado AGORA** (RN-013/D-01); rota recalcula até o destino; mapa começa a alimentar `delivery_locations` (polling §6.4). | `aria-live="polite"` anuncia "Endereço do destino liberado" |
| **Longe do ponto (geofence)** | `jx-error-state`/banner: "Você parece longe do ponto de coleta. Aproxime-se para confirmar a chegada." CTA "Cheguei" desabilitado até dentro do raio. | `role="alert"` |
| **Loading** | `jx-loading-skeleton` no lugar do mapa + bloco de texto; mapa entra depois (lazy). | `aria-busy` |
| **Offline** | `jx-warn-banner` "Conexão instável. A rota pode estar desatualizada." Operação continua; foto vai para a fila (§4). | `role="status"` |

### 2.3 Janela de telefones (RN-022 / D-01)

- Botões "Ligar"/"Mensagem" presentes **somente** quando a entrega está em `ACEITA`→`FINALIZADA`. Fora dessa janela (CRIADA, CANCELADA, e após FINALIZADA) o backend não retorna o telefone e o botão **não renderiza** (não fica desabilitado vazio).
- `tel:` abre o discador nativo; nunca exibir o número completo em texto copiável fora da necessidade — exibir mascarado quando exibido (`(22) 9****-1234`, mono).

### 2.4 Gesture (gesture-touch-patterns)

- **Sem swipe-to-arrive / swipe-to-confirm.** "Cheguei" e "Confirmar" são botões deliberados ≥52px — um gesto acidental não pode disparar uma transição de estado server-side.
- Pan/zoom do mapa não conflita com o scroll da página: mapa com `touch-action` próprio; a página rola pelo conteúdo abaixo do mapa. Mapa não captura o scroll vertical da página inteira.
- Tap na foto de preview = ampliar (herdado de `jx-doc-upload`).

---

## 3. Comprovação (tela 07 — Entregador) — `jx-proof-capture`

Aciona em COLETADA→ENTREGUE (e na coleta ACEITA→COLETADA). Wrapper que **reusa `jx-doc-upload`** e adiciona GPS/geofence, número de referência, pagamento direto e desvios.

### 3.1 Anatomia

| Bloco | Conteúdo |
|---|---|
| **Overline + título** | "NO DESTINO · Vila Nova" + `<h1>` "Comprovar entrega"; "Destinatária: Maria Silva" (`--text-muted`) |
| **`jx-geofence-pill`** | status GPS (ver §3.2) — acima da câmera |
| **Câmera** | `jx-doc-upload` (`captureMode="environment"`, label "Foto da entrega"); hint "Enquadre a fachada, número ou porta" |
| **Número de referência** | input mono centralizado, `inputmode="numeric"`, `maxlength=6` — só quando método = nº referência |
| **`jx-direct-payment-confirm`** | fieldset pagamento direto (só quando modalidade = direto) — §3.4 |
| **CTA** | "Confirmar entrega" (`--brand`, full-width, ≥52px), `disabled` até foto OK + (GPS OK **ou** low_confidence) + nº válido quando exigido |
| **Desvios** | "Destinatário ausente" / "Destinatário recusou o item" — texto `--error`, ≥44px |

### 3.2 Feedback de GPS / geofence — `jx-geofence-pill` (RN-005/RN-017, D-03)

A foto é validada **server-side** (extrai EXIF GPS, valida geofence; cliente dá feedback otimista mas a transição só conclui no servidor). A pílula tem 3 estados (sempre texto + ícone, **nunca cor só**):

| Estado | Aparência | Copy | A11y | Efeito no CTA |
|---|---|---|---|---|
| **Verificando** | fundo `--surface-sunken`, ícone "…" | "Verificando sua localização…" | `aria-live="polite"` | CTA aguarda |
| **Dentro do raio (OK)** | fundo `--success-bg` (claro) / `--surface-elevated`+texto `--success` (dark), borda esq. 3px `--success`, ícone ✓ | "GPS confirmado · você está no endereço" | `role="status"` | CTA habilita (com foto) |
| **Fora do raio / sem GPS** | fundo `--error-bg` (claro) / `--surface-elevated`+texto `--error` (dark), borda esq. 3px `--error`, ícone ! | "Você está fora do raio do endereço. Aproxime-se ou ative a localização." | `role="alert"` | CTA bloqueado |

**3 falhas → `low_confidence` (D-03/E1):** após a 3ª foto rejeitada, a pílula vira `jx-warn-banner`: "Não conseguimos confirmar a localização. Sua entrega segue para revisão da equipe — você pode concluir mesmo assim." → CTA **destrava** (a operação não pode travar para sempre); a entrega entra com flag `low_confidence` para revisão do admin de área. Borda/ícone warning, `role="status"`.

> **Nota crítica de pipeline (CONTEXT §specifics):** KYC (Phase 5) faz *strip* de EXIF por privacidade; **comprovação PRESERVA e valida o GPS do EXIF** (antifraude geofence). Pipelines opostos — não confundir. Isto é backend, mas a UI depende dele: o cliente NÃO decide o geofence, só reflete o veredito.

### 3.3 Número de referência (D-02 / E4)

- Input mono centralizado, `letter-spacing .2em`, `inputmode="numeric"`, `maxlength=6`, placeholder "0000". Label: "Número do pedido (pergunte ao destinatário)".
- Validação contra `reference_number`. Erro (não confere): `jx-error-state` inline "Número não confere (tentativa 2 de 3). Confirme com o destinatário ou ligue para a loja." (`role="alert"`, contador visível).
- **3 tentativas erradas:** orienta ligar à loja; a loja libera manualmente pelo painel (§5.3). CTA de confirmar fica bloqueado por nº; surge atalho "Ligar para a loja".

### 3.4 Confirmação de pagamento direto — `jx-direct-payment-confirm` (RN-026 / D-05)

Fieldset (`<legend>` com tag warning "PAGAMENTO DIRETO 💵", fundo `--warning-bg`/texto `--warning`). Radio group obrigatório quando modalidade = direto:

| Opção | Valor | Efeito |
|---|---|---|
| "Recebi R$ 8,50 em dinheiro" | `cash` | ENTREGUE normal; grava `direct_payment_confirmations` |
| "Recebi R$ 8,50 por PIX" | `pix` | idem |
| "Não recebi o pagamento" | `not_received` | **entrega conclui (ENTREGUE)** mas abre `payment_dispute` (registro); mediação é Phase 11/13 |

- Valor (`R$ 8,50`) sempre em mono, vindo do backend (nunca hardcoded).
- Selecionar "Não recebi" mostra um `jx-warn-banner` de confirmação consciente: "A entrega será concluída e um registro será aberto para a equipe avaliar." — sem bloquear; trust-safety (o entregador não é punido por reportar honestamente).
- A11y: `<fieldset>`/`<legend>`, radios com `<label>` clicável ≥44px, grupo com nome acessível.

### 3.5 Desvios (E2 ausente / E3 recusa — D-07)

| Desvio | Fluxo UI | Estado final |
|---|---|---|
| **Ausente (E2)** | botão "Destinatário ausente" → tela de espera: notifica destinatário + exibe telefone para ligar (janela RN-022) + **contagem de 10 min** (timer visível, mono). Após 10 min sem resposta → botão "Retornar ao estabelecimento" habilita. | `RECUSADA_NO_DESTINO` (reason `absent`); loja paga corrida + retorno (RN-004) |
| **Recusa (E3)** | botão "Destinatário recusou o item" → exige **foto da recusa** (mesmo `jx-proof-capture`) + campo motivo (textarea curta) | `RECUSADA_NO_DESTINO` (reason `refused`) |

- O timer de 10 min usa o padrão do `jx-offer-timer` (Phase 8) reusado/adaptado — contagem regressiva mono, sem som agressivo; `aria-live="polite"` em marcos (5 min, 1 min).
- Ambos os desvios revelam custo ao entregador de forma neutra: "A loja é avisada. Você não é penalizado por isto."

---

## 4. Upload offline-tolerante (offline-first / D-04) — `jx-pending-upload-banner`

O interior tem conexão ruim: a foto fica no device e sobe ao reconectar (`pending_upload`); **a transição de estado só conclui com upload OK**.

### 4.1 Comportamento

- Ao confirmar com a rede caída: a foto é salva localmente; a UI mostra estado **"na fila"** em vez de erro. CTA mostra "Salvo — enviando quando a conexão voltar."
- `jx-pending-upload-banner` (fixo, abaixo do header ou como ion-toast persistente): "1 foto aguardando conexão para enviar." com contador mono; reusa visual de `jx-warn-banner` (`--warning-bg`, ícone, borda esq. 3px). `role="status"`.
- Ao reconectar: progresso retomado (reusa a barra `role="progressbar"` do `jx-doc-upload`); ao concluir → estado transiciona de fato e o banner some com `aria-live` "Foto enviada. Entrega confirmada."
- **A entrega NÃO aparece como ENTREGUE até o upload e a validação server-side concluírem** — a UI deixa isso explícito ("Pendente de envio", não "Entregue").
- Polling de localização (§6.4) também é resiliente: pausa offline, retoma online; não acumula posições obsoletas (filtro de movimento 50m).

### 4.2 A11y

- Status sempre text+ícone; nada depende só de cor. Banner persistente é `role="status"` (não interrompe). Falha definitiva (ex.: device sem espaço) → `jx-error-state` `role="alert"` com retry.

---

## 5. Loja — detalhe da entrega (tela 13, web responsivo)

Layout 2 colunas (≥760px): conteúdo principal + aside. Colapsa para 1 coluna no mobile. Reusa cards do design system.

### 5.1 Anatomia

| Região | Conteúdo | Componentes |
|---|---|---|
| **Header** | `<a>` voltar; `<h1>` "Entrega #2851" (mono) + `jx-state-badge` (variant `dashboard`) + badge "DIRETO 💵"; botão cancelar (política RN-004) | `jx-state-badge` |
| **Mapa ao vivo** (coluna principal) | `jx-live-map` (modo loja) — posição aproximada do entregador, **só na janela ACEITA→FINALIZADA**; lazy abaixo do fold inicial | `jx-live-map` |
| **Linha do tempo** | `jx-tracking-timeline` com os eventos reais + horários mono ("Coletada · foto ok · GPS ok 14:36:12") | `jx-tracking-timeline` |
| **Comprovações** | thumbnails das fotos (coleta/entrega) com alt descritivo; warn se nº de referência falhou 3× + botão "Liberar entrega manualmente" (E4) | `jx-warn-banner` |
| **Aside — Entregador** | `jx-accepted-courier-card` (nome, placa mono, `jx-score-chip`) + ligar/mensagem (janela RN-022) | `jx-accepted-courier-card`, `jx-score-chip` |
| **Aside — Valores** | corrida (direto ao entregador) + taxa Jaxegô (na fatura) — mono | — |
| **Aside — Destinatário** | nome + telefone mascarado mono + **link de rastreio público** (`/r/{token}`) | — |

### 5.2 Cancelamento (RN-004 / D-08)

- Botão de cancelar **declara a política e o custo no próprio rótulo**: "Cancelar (cobra 100% + retorno)" após coleta; "Cancelar (cobra 50%)" após aceite antes da coleta; "Cancelar (sem custo)" antes do aceite.
- Estilo: outline `--error` (não fundo cheio — ação destrutiva precisa de fricção, não de proeminência). Abre confirmação modal (reusa `jx-upgrade-modal` pattern como base de modal) com o custo em destaque mono e exige confirmação explícita.
- No M1 (direto) o custo é **registrado** na entrega; a cobrança efetiva é fatura (Phase 11) — o modal diz isso: "O valor será lançado na sua próxima fatura."

### 5.3 Liberação manual (E4)

- Quando nº de referência falhou 3×: `jx-warn-banner` no card de comprovações com botão "Liberar entrega manualmente" (fica registrado/auditável). Confirmação com aviso de que a ação fica logada.

### 5.4 Estados

- **Loading:** `jx-loading-skeleton` (timeline + mapa). **Vazio/404:** `jx-empty-state` "Entrega não encontrada." + voltar à lista. **Erro:** `jx-error-state` com retry.

---

## 6. Tracking público (tela 26, SEM login) — peça nova central

Acesso por `public_token` opaco (Phase 7), sem auth. **Trust-safety + LGPD são o coração desta tela.** Mobile-first (chega por SMS/link), `max-width ~480px`.

### 6.1 Anatomia (top→bottom)

| Bloco | Conteúdo | Componente |
|---|---|---|
| **Header de marca** | "Jaxegô. Chegou *rapidinho.*" (`rapidinho.` Fraunces italic `--brand`) — assinatura, sem login | — |
| **Mapa ao vivo** | `jx-live-map` (modo público): posição **aproximada** do entregador, "atualiza a cada minuto"; **lazy** (§6.5) | `jx-live-map` |
| **Banner de estado + ETA** | `jx-tracking-banner`: "🛵 Sua entrega está a caminho — chega em ~6 min" (ETA mono) | `jx-tracking-banner` |
| **Timeline** | `jx-tracking-timeline`: estados em linguagem do destinatário ("Saiu para entrega", "Chegando em Vila Nova") com horários mono | `jx-tracking-timeline` |
| **Card do entregador** | avatar (iniciais fallback), nome, score limitado (★ 4.8), veículo+placa — **só PII permitida** (RN-022) | `jx-score-chip` (valor limitado) |
| **Footer de procedência** | "Você recebeu este link por SMS porque {Loja} enviou uma entrega via Jaxegô · jaxego.com.br" | — |

### 6.2 Regras de PII e estado (RN-013 / RN-022 / trust-safety)

- **Endereço completo do destino só aparece no tracking APÓS `COLETADA`** (RN-013). Antes: "Chegando em {bairro}".
- Card do entregador expõe **apenas o permitido**: primeiro nome, score, modelo+placa do veículo. **Nunca** telefone do entregador, documento, localização exata residencial, histórico.
- **Nunca PII além do permitido no DOM nem no payload** da rota pública (não basta esconder no CSS — o endpoint público não retorna o dado).
- Posição do entregador é **aproximada** (snap a via / arredondamento), nunca lat/long precisa em texto.

### 6.3 Timeline pública — `jx-tracking-timeline`

- Os 7 estados como linha do tempo vertical (reusa o padrão do wireframe 13/26). Cada item: ponto colorido por `color.delivery_state.*` + label + horário mono.
- Estados: `done` (cor cheia `--success`/estado), `current` (ponto `--brand`/`--state-coletada`, label weight 600), futuros (ponto `--border-strong`, label `--text-subtle`).
- **É a alternativa textual do mapa** (§9) e o **LCP** da tela (§6.5).
- `aria-live="polite"` no item current: quando o estado muda (ex.: vira ENTREGUE), anuncia "Sua entrega foi entregue."

### 6.4 Mapa ao vivo — fonte de dados (DEC-002 / ADR-101)

- App do entregador faz **polling HTTP de localização 60-120s** (filtro de movimento 50m; **Page Visibility API pausa** quando o app vai para background → economia + privacidade), grava em `delivery_locations` (retenção 24h pós-entrega).
- O mapa público **lê** a última posição aproximada via endpoint público (sem auth, via token); refresh client-side a cada ~60s.
- WebSocket foi **rejeitado** (custo — DEC-002): é polling, não realtime socket. A UI comunica "atualiza a cada minuto", não finge tempo-real-instantâneo.
- Posição só existe na janela `ACEITA`→`FINALIZADA`; fora dela o mapa some e fica só a timeline.

### 6.5 Mapa — performance (performance-web-vitals) — `jx-live-map`

**O mapa NÃO pode degradar o LCP.** Contrato de performance:

- **LCP = a timeline + banner de ETA** (texto, render imediato no SSR/primeira pintura). O mapa é **lazy**: `IntersectionObserver`/import dinâmico do MapLibre GL JS só após a primeira pintura do conteúdo crítico.
- Placeholder do mapa = `jx-loading-skeleton` (bloco `--surface-sunken` com label "Carregando mapa…"); **a página é totalmente utilizável sem o mapa** (timeline + ETA já respondem a pergunta "onde está minha entrega?").
- MapLibre GL JS + tiles OSM carregados **sob demanda**; sem bloquear o thread principal de render inicial; bundle do mapa fora do chunk crítico (lazy route/component).
- Tiles com cache; marcador único (posição do entregador) — sem camadas pesadas, sem heatmap, sem clustering.
- `prefers-reduced-motion`: sem animação de "voo"/pan automático; a posição atualiza por reposicionamento estático do marcador, sem tween.
- Budget herdado (`config.json performance_budget`): LCP ≤ 2500ms — garantido porque o LCP não depende do mapa.

### 6.6 Estados do tracking

| Estado | Aparência |
|---|---|
| **Loading** | `jx-loading-skeleton` (timeline) + skeleton do mapa |
| **Ativo** | timeline + banner ETA + mapa (após COLETADA) |
| **Pré-coleta** | timeline até "Aceita/Indo coletar"; mapa pode mostrar entregador indo à coleta; destino só bairro |
| **Entregue/Finalizada** | banner "Entregue às 14:52"; mapa congela na última posição ou some; timeline completa |
| **Link inválido/expirado** | `jx-error-state` "Link de rastreio expirado ou entrega não encontrada. Confira com a loja." (`role="alert"`) — token opaco, sem revelar se existe (anti-enumeração) |

---

## 7. Sistema de cores aplicado (60/30/10 + delivery_state)

### 7.1 60/30/10 (herdado da Phase 3)

- **60% dominante:** `--surface` (cream warm `neutral.50` claro / `neutral.900` dark) — fundo de todas as telas.
- **30% secundário:** `--surface-elevated` (cards, sheets, banner de ETA, card do entregador, mapa container) + `--border`.
- **10% acento (`--brand` persimmon) — RESERVADO para:**
  1. Palavra-chave Fraunces italic do header de marca.
  2. Estado **atual** na timeline (ponto + label "agora") e no mini-stepper.
  3. Marcador "agora" / posição do entregador no mapa.
  4. CTA de comprovação "Confirmar entrega" (`jx-proof-capture`).
  5. Foco (`--focus-ring`).
  - **NÃO usar persimmon** como fundo de card, banner neutro, ou preenchimento decorativo.

### 7.2 Cor semântica secundária (destrutiva)

- `--error` reservado a: ações destrutivas (cancelar entrega, "não consigo concluir", desvios ausente/recusa), GPS fora do raio, link inválido. Cancelar = outline `--error` (fricção), nunca fundo cheio dominante.

### 7.3 `color.delivery_state.*` na timeline e badges (NOVO uso nesta phase)

Mapeamento dos 7 estados → `--state-*` (CSS vars derivadas em Phase 7 a partir de `color.delivery_state`):

| Estado | Token | Uso |
|---|---|---|
| CRIADA | `color.delivery_state.criada` (#6B5F50) | "Procurando" |
| ACEITA | `color.delivery_state.aceita` (#0A66C2) | "Indo coletar" |
| COLETADA | `color.delivery_state.coletada` (#E89B0E) | "A caminho" — ponto atual frequente |
| ENTREGUE | `color.delivery_state.entregue` (#1B998B) | "Entregue" |
| RECUSADA_NO_DESTINO | `color.delivery_state.recusada_no_destino` (#E84E1B) | "Recusada no destino" |
| CANCELADA | `color.delivery_state.cancelada` (#9D8E7A) | "Cancelada" |
| FINALIZADA | `color.delivery_state.finalizada` (#0F6E62) | "Finalizada" |

- Contraste validado nos dois temas: pontos da timeline são preenchidos (forma) + label em `--text` (não dependem só da cor do ponto para legibilidade — a11y).

### 7.4 Mapa em dark mode (DEC-001 — tratamento explícito)

**O mapa precisa de tratamento dark dedicado** (tiles claros de OSM "queimam" o olho no tema escuro):

- **Estratégia:** estilo de mapa por tema. No `data-theme="dark"`, o `jx-live-map` aplica um **style/tile dark** (MapLibre style escuro — ex.: tiles raster OSM com filtro CSS `brightness/invert` controlado, OU um style vetorial dark se a fonte de tiles oferecer). Decisão de implementação (Discretion): preferir style dark nativo se a fonte tiver; senão, overlay `--surface` com `mix-blend`/filtro calibrado para não inverter o marcador.
- **Marcador da posição** mantém `--brand` (persimmon) nos dois temas — alto contraste sobre claro e escuro.
- Container do mapa: borda `--border`, radius `lg`, fundo de fallback `--surface-sunken` (combina nos dois temas durante o load).
- Atribuição OSM legível nos dois temas (`--text-subtle` sobre `--surface-elevated`), nunca apagada (requisito de licença OSM).
- `prefers-color-scheme`/toggle: o mapa reage à troca de `data-theme` sem reload (re-aplica style).

---

## 8. Notificações — padrão visual (push + in-app) — `jx-notice` (D-10, RN-018)

3 momentos proativos ao destinatário/loja; canal push/e-mail; **SMS só no "a caminho"** (quota — RN-018). Multicanal com fallback (push→email; SMS primário→fallback→email).

### 8.1 Os 3 momentos

| Momento | Disparo | Canal | Copy (exemplo) |
|---|---|---|---|
| **Aceite** | entregador aceitou | push + e-mail | "{Loja} já tem um entregador para o seu pedido." |
| **A caminho / aproximação** | COLETADA + geofence de aproximação | push + e-mail + **SMS** (com link de tracking) | "Sua entrega está a caminho — acompanhe: {link}" |
| **Entregue** | ENTREGUE | push + e-mail | "Sua entrega foi concluída. Avalie quando quiser." |

### 8.2 Padrão visual in-app (`jx-notice`) — espelha o push

- **Toast/in-app:** card `--surface-elevated`, borda esq. 3px na cor semântica do momento (info para aceite/a caminho, `--success` para entregue), ícone + título curto + corpo + ação opcional ("Acompanhar"). Radius `lg`, shadow `--shadow-md`.
- **Push (sistema):** título ≤ 50 chars, corpo ≤ 120 chars, mesma voz; deep-link para o tracking/detalhe.
- Auto-dismiss 6s (não-crítico) com `prefers-reduced-motion` desabilitando o slide; `role="status"` (não interrompe leitor de tela em momento crítico).
- **Opt-in de push (push-notifications-architecture):** prompt de permissão **contextual** (após primeira entrega relevante, não no primeiro load); se negado, fallback silencioso para e-mail/SMS; nunca re-pedir agressivo. Estado "notificações desligadas" mostrável em perfil com CTA para reativar.
- `push_subscriptions`: registro do device do entregador/loja; UI de gerência mínima em perfil ("Receber avisos neste aparelho" toggle, `aria-pressed`).

### 8.3 A11y das notificações

- Toast `role="status"` (`aria-live="polite"`); ações com ≥44px; nunca só cor para distinguir tipo (ícone + texto). Toast não rouba foco.

---

## 9. Acessibilidade (AA dois temas — accessibility-pro, DEC-001)

- **Contraste AA nos dois temas:** ≥4.5:1 texto, ≥3:1 UI/grande. Validar `--state-*` sobre `--surface-elevated` em claro e dark (pontos da timeline reforçados por label em `--text`, nunca cor-só).
- **Mapa acessível (trust-safety + a11y):** o mapa tem **alternativa textual equivalente = timeline + banner de ETA** (pergunta "onde está minha entrega?" respondida sem o mapa). Mapa tem `role="img"`/`aria-label` resumindo ("Mapa: entregador a ~6 min, em Vila Nova"); controles do MapLibre operáveis por teclado OU explicitamente `aria-hidden` com a alternativa textual cobrindo a informação. Mapa **nunca** é a única forma de obter o estado.
- **Câmera acessível (file-upload-ux herdado):** `jx-doc-upload` já opera por botões (não só pelo input nativo); labels descritivos; status sempre text+ícone+aria-live; progresso `role="progressbar"`.
- **Foco:** `--focus-ring` em todo interativo; foco move para alertas (GPS fora, nº não confere, link inválido). Ordem de tabulação lógica em 13 (2 colunas) e no formulário de comprovação.
- **Touch ≥44px** (CTAs ≥52px em ações de operação crítica); radios de pagamento com label clicável ≥44px.
- **aria-live em mudança de estado** (requisito explícito): transição COLETADA (endereço liberado), ENTREGUE, posição atualizada, foto enviada, GPS confirmado — todos anunciados via `aria-live="polite"` ou `role="alert"`/`status` conforme urgência.
- **`prefers-reduced-motion`:** sem pan automático do mapa, sem pulse de skeleton, sem slide de toast — reposicionamento estático.
- **`lang="pt-BR"`**, landmarks (`<main>`, `<nav>`, `role="dialog"` em modais de cancelamento), `axe-core` no tracking público e na comprovação (zero violações críticas).

---

## 10. Copywriting (br/ux-copywriting-ptbr — contrato)

| Elemento | Copy | Regra |
|---|---|---|
| **CTA primário coleta** | "Cheguei na coleta" → "Confirmar coleta" | verbo, sem ponto |
| **CTA primário entrega** | "Comprovar entrega" / "Confirmar entrega" | verbo+objeto |
| **Empty (comprovações)** | "Ainda não há comprovações nesta entrega." | causa, sem "Lista vazia" |
| **Empty (tracking pré-coleta)** | "Sua entrega está sendo preparada. Avisamos quando sair." | tranquiliza + próximo passo |
| **Erro GPS fora** | "Você está fora do raio do endereço. Aproxime-se ou ative a localização." | o que houve + o que fazer |
| **Erro nº referência** | "Número não confere (tentativa 2 de 3). Confirme com o destinatário ou ligue para a loja." | acionável + contador |
| **Low confidence** | "Não conseguimos confirmar a localização. Sua entrega segue para revisão da equipe — você pode concluir mesmo assim." | não trava; tom neutro |
| **Offline (fila)** | "Salvo — enviando quando a conexão voltar." / "1 foto aguardando conexão." | reassuro, não erro |
| **Link inválido (público)** | "Link de rastreio expirado ou entrega não encontrada. Confira com a loja." | anti-enumeração |
| **Pagamento "não recebi"** | "A entrega será concluída e um registro será aberto para a equipe avaliar." | consciente, sem punir |
| **Cancelar (destrutivo)** | rótulo: "Cancelar (cobra 100% + retorno)"; modal: "O valor será lançado na sua próxima fatura." | custo explícito antes da ação |
| **Notif. a caminho** | "Sua entrega está a caminho — acompanhe: {link}" | curta (SMS quota) |
| **Notif. entregue** | "Sua entrega foi concluída. Avalie quando quiser." | sem urgência falsa |

- **Fraunces italic:** SÓ em "rapidinho." no header de marca do tracking. Nunca em botão, erro, dado, estado.

---

## 11. Tabela de tokens citados (Gate 2 — todos existem em `tokens.json`)

Cada token referenciado neste UI-SPEC com caminho em `docs/identidade-visual/tokens.json`. **Confirmado: 100% existem (zero inventados).** As CSS vars semânticas (`--surface`, `--state-*`, etc.) foram definidas na Phase 3/7 e derivam destes.

| Token (caminho em tokens.json) | Valor | Existe? |
|---|---|---|
| `color.brand.50/100/300/400/500/600/800/900` | #FFF1E8…#421405 | ✅ |
| `color.neutral.50/100/200/300/400/500/600/700/800/900` | #FAF6EE…#0A0805 | ✅ |
| `color.semantic.success` / `success_bg` | #1B998B / #D6F1ED | ✅ |
| `color.semantic.warning` / `warning_bg` | #E89B0E / #FFF1D2 | ✅ |
| `color.semantic.error` / `error_bg` | #C71D1D / #F9DCDC | ✅ |
| `color.semantic.info` / `info_bg` | #0A66C2 / #DDEBFA | ✅ |
| `color.delivery_state.criada` | #6B5F50 | ✅ |
| `color.delivery_state.aceita` | #0A66C2 | ✅ |
| `color.delivery_state.coletada` | #E89B0E | ✅ |
| `color.delivery_state.entregue` | #1B998B | ✅ |
| `color.delivery_state.recusada_no_destino` | #E84E1B | ✅ |
| `color.delivery_state.cancelada` | #9D8E7A | ✅ |
| `color.delivery_state.finalizada` | #0F6E62 | ✅ |
| `color.score_level.*` (chip do entregador) | probation…diamante | ✅ |
| `spacing.1 … spacing.9` | 4 … 96px | ✅ |
| `radius.sm/md/lg/xl/full` | 4/6/10/16/9999px | ✅ |
| `font.family.display / serif_accent / body / mono` | Inter Tight / Fraunces / Inter Tight / JetBrains Mono | ✅ |
| `font.size.2xs…3xl` (usados: 2xs/xs/sm/base/md/lg/xl/2xl/3xl) | 11…36px | ✅ |
| `font.weight.regular/medium/semibold/bold/extrabold` | 400…800 | ✅ |
| `shadow.sm/md/lg/focus` | warm rgba(24,20,16,…) / focus persimmon | ✅ |
| `motion.fast/normal/slow/easing_out` | 140/220/380ms / cubic-bezier | ✅ |

**Tokens referenciados que NÃO existem em tokens.json: NENHUM (0).** Gate 2 satisfeito. O **mapa não introduz token novo**: container/marcador usam `--surface-*`, `--border`, `--brand`; o style dark é tratamento de filtro/tile sobre as vars existentes, não cor nova.

> Observação não-bloqueante (herdada da Phase 3): wireframes usam `#fff` puro em cards; este UI-SPEC mantém `--surface-elevated` (= `neutral.100`) para coesão warm. Se o humano exigir branco puro, adicionar `color.neutral.0: #FFFFFF` a tokens.json (decisão consciente — não inventar em CSS). **Não bloqueia esta phase.**

---

## 12. Visual regression (baseline desta phase — product/visual-regression-testing)

Componentes novos compartilhados recebem story/baseline (claro + dark):

- [ ] `jx-proof-capture` — idle / verificando-gps / gps-ok / gps-fora / low-confidence / uploading / offline-fila
- [ ] `jx-geofence-pill` — verificando / ok / fora
- [ ] `jx-direct-payment-confirm` — cash / pix / não-recebi
- [ ] `jx-tracking-timeline` — pré-coleta / a-caminho / entregue / recusada
- [ ] `jx-tracking-banner` — a-caminho / entregue
- [ ] `jx-live-map` — loading-skeleton / com-marcador (claro) / com-marcador (dark) / reduced-motion
- [ ] `jx-pending-upload-banner` — 1-foto / enviando
- [ ] `jx-notice` — aceite / a-caminho / entregue
- [ ] tela 06 (entrega ativa) · tela 07 (comprovação) · tela 13 (detalhe loja) · tela 26 (tracking) — claro+dark

Nome screenshot: `{component}-{state}-{theme}-{viewport}.png`.

---

## 13. Open questions para o humano

- [ ] **Style dark do mapa:** preferir style vetorial dark nativo (se a fonte de tiles oferecer) vs. filtro CSS `invert/brightness` sobre tiles raster OSM? **Recomendação:** style dark nativo se disponível (melhor legibilidade); fallback filtro calibrado. Decisão de implementação, não bloqueia o contrato visual (marcador `--brand`, container tokenizado garantidos). Ver §7.4.
- [ ] **Granularidade da "posição aproximada":** snap-a-via vs. arredondamento de coordenadas. **Recomendação:** snap à via mais próxima (privacidade + leitura clara). LGPD: confirmar com `br/lgpd-compliance` no research.

---

## Approval

- [ ] Humano revisou e aprovou (ou delegou ao ui-checker)
- [ ] ui-checker validou 6 dimensões: tokens, tipografia, copy, estados, interações, acessibilidade
- [ ] Gate 2 (Visual Contract) verde — tokens citados existem em tokens.json (§11)
- [ ] Aprovado em: {date}

**Próximo passo:** `/gsd:plan-phase 9` — o planner recebe este UI-SPEC como contexto e contrato de design.
