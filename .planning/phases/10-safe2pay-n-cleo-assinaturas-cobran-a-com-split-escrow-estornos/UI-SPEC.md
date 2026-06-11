---
status: draft
phase: 10
gate: 2
---

# UI-SPEC — Phase 10: Safe2Pay núcleo — assinaturas, cobrança com split, escrow, estornos

> Design contract. Gerado por `gsd-ui-researcher` em 2026-06-11. Aprovado por `gsd-ui-checker` em {date}.
> **BLOQUEIA** `plan-phase` se não existir (Gate 2 do framework). Tokens canônicos: `docs/identidade-visual/tokens.json` — confirmados existentes (ver §13).
> Plataforma: **web** (Angular standalone, lojista no desktop/responsivo). Telas mobile do entregador (extrato/saque) são Phase 11.
> **⚠ É DINHEIRO REAL.** Checkout transmite confiança (trust-safety-ux). Cartão NUNCA em texto puro — RSA-OAEP 2048 no cliente (D-02). Dois temas (DEC-001).

---

## 1. Fontes de verdade consultadas

- `docs/identidade-visual/tokens.json` (v2-jaxego) — **canônico, Gate 2**. Editorial-técnico: persimmon queimado + cream warm + carvão amarronzado. Inter Tight (display/body) + Fraunces italic (1 acento por título) + JetBrains Mono (valores/IDs).
- `apps/web/src/styles/_tokens.scss` (primitivos `--jx-*`, gerado) + `_semantic.scss` (camada semântica `--surface`/`--brand`/`--error`/`--state-*`, **dois temas DEC-001**). Componentes consomem SEMPRE a camada semântica, nunca primitivo nem hex.
- `docs/SAAS-BILLING-DOCS.md` — §4 (cripto AES-256-GCM token + RSA-OAEP cartão), §5-6 (fluxos cartão/PIX automático), §9 (guard assinatura ativa), §10 (inadimplência 10/20d), §12 (rotas). **CLAUDE.md §18: lei de billing.**
- `10-CONTEXT.md` — D-01..D-09, DEC-003 (suposições `[ASSUMIDO]` atrás de interface própria).
- `projeto/regras-negocio/regras.md` — RN-004 (estorno), RN-006 (escrow 24h), RN-010 (MEI p/ repasse), RN-023 (taxa nas 3 modalidades), RN-029 (upgrade pro-rata/downgrade agendado).
- `projeto/regras-negocio/fluxos.md` — F-03 (criação, E3 recusa), F-07 (pagamento corrida/taxas, split, escrow).
- `projeto/wireframes/16-loja-plano.html` (planos + cobranças), `12-loja-nova-entrega.html` (pagamento cartão/PIX agora ativo).

### Fases anteriores — componentes herdados (REUSO, não re-especificar)

| Phase | UI-SPEC | Componentes reusados nesta fase |
|-------|---------|---------------------------------|
| 3 | shell + design system | tokens, `jx-notice` (toast/inline), estados loading/empty/error, `theme-toggle`, layout `<main>` |
| 4 | cadastro loja | `jx-plan-card` (Plan interface — GET /v1/plans, DATA-DRIVEN), `jx-field` (CVA, máscara BR, erro `aria-describedby`) |
| 6 | área operável | `jx-data-table` (histórico de cobranças/faturas) |
| 7 | criação de entrega | `jx-estimate-box` (frete mediana + taxa), `jx-state-badge` (7 estados), `jx-upgrade-modal` (E4, anti-dark-pattern), `jx-direct-payment-confirm` |
| 9 | execução/tracking | `jx-notice` como toast de evento (success/warning/error) |

### Skills consultadas (matriz UI M1 + Phase 10 do ROADMAP)

- `ux-advanced/payment-checkout-ux` — valor exato antes de confirmar; método único visível por vez; estado de processamento bloqueante; recusa com causa + saída.
- `ux-advanced/trust-safety-ux` — indicador de segurança (cadeado + "criptografado"), nunca pedir dado desnecessário, transparência de cobrança, sem urgência falsa.
- `ui-ux-pro-max` — editorial-técnico, valores em mono, 1 acento Fraunces por título, anti-AI-slop (sem gradiente roxo, sem emoji decorativo no checkout).
- `quality/accessibility-pro` — AA nos dois temas, form de pagamento com label/erro associado, foco gerenciado, touch ≥44px.
- `br/ux-copywriting-ptbr` — direto, sem "Ops!", sem jargão; valores em R$ pt-BR.
- `ux-advanced/empty-states-polish` · `ux-advanced/dark-mode-theming` (DEC-001) · `product/component-library-governance` · `ux-advanced/form-ux-mastery` + `quality/error-ux-patterns` (form de cartão).
- `ux-advanced/data-tables-ux` — histórico de cobranças.

---

## 2. Telas e superfícies cobertas por esta fase

1. **Tela 16 — Plano e assinatura** (escolha de plano, checkout cartão/PIX, estado da assinatura, inadimplência, histórico de cobranças).
2. **Tela 16b — Upgrade/Downgrade** (comparativo + pro-rata RN-029) — modal/painel sobre a tela 16.
3. **Tela 12 — Nova entrega · pagamento cartão/PIX agora ATIVO** (split implícito, corrida + taxa, recusa → retry / trocar p/ direto F-03 E3).

> **FORA do escopo (não especificar aqui):** fatura mensal de taxas do pagamento direto e bloqueio por fatura vencida (Phase 11, tela 16 seção "Faturas de taxas" do wireframe fica desabilitada/placeholder); saques, extrato do entregador, disputas (Phase 11); relatório de revenue share (Phase 13).

---

## 3. Design tokens (herdados + específicos desta fase)

**Herdados de `docs/identidade-visual/tokens.json`:** sem mudanças. Toda cor/spacing/tipo/raio/sombra vem da camada semântica `--surface`/`--text`/`--brand`/`--success`/`--warning`/`--error`/`--info` e dos primitivos `--jx-space-*`, `--jx-text-*`, `--jx-radius-*`, `--jx-shadow-*`, `--jx-motion-*`. **Zero `#hex` em código (Gate 2).**

**Novos tokens propostos:** **NENHUM.** Os 4 status de assinatura (trial/active/blocked/cancelado) e os 4 status de cobrança (aberto/pago/falhou/cancelado) mapeiam 1:1 a tokens semânticos JÁ existentes — mesma mecânica do `jx-state-badge` (Phase 7), reaproveitando `--info`/`--success`/`--warning`/`--error`/`--text-muted` como texto vívido sobre `--surface-sunken`. Não há `_bg` pastel novo (padrão dark-mode-theming — funciona nos dois temas sem token extra).

### Mapa status-assinatura → token semântico (sem token novo)

| Status assinatura | Token texto/borda | Glyph | Significado também no texto (nunca só cor) |
|-------------------|-------------------|-------|--------------------------------------------|
| `trial` | `--info` | `◷` | "Teste · N dias restantes" |
| `active` | `--success` | `✓` | "Ativa · renova em DD/MM" |
| `blocked` | `--error` | `!` | "Bloqueada · regularize o pagamento" |
| `cancelado` | `--text-muted` | `×` | "Cancelada" |

### Mapa status-cobrança → token (reusa vocabulário da tela 16 wireframe)

| `situacao` | Rótulo | Token |
|-----------|--------|-------|
| 1 pago | "PAGA" | `--success` |
| 0 aberto | "EM ABERTO · vence DD/MM" | `--warning` |
| 2 falhou | "FALHOU · pagar" | `--error` |
| 3 cancelado | "CANCELADA" | `--text-muted` |

---

## 4. Tipografia

- Scale herdada (uso nesta fase): h1 tela = `--jx-text-2xl` (28px); título de seção/card = `--jx-text-md`/`--jx-text-lg`; corpo = `--jx-text-base` (14px, line-height 1.5); legenda/hint = `--jx-text-xs`/`--jx-text-sm`.
- **Valores monetários e IDs SEMPRE em mono** (`--jx-font-mono`): preço do plano, "R$ corrida + taxa", QR copia-e-cola, transaction_id, últimos 4 dígitos do cartão. (ui-ux-pro-max).
- Acento Fraunces (`--jx-font-serif-accent`, italic): no máximo 1 palavra-chave no título da tela 16 (ex.: "Seu *plano*"). Nunca em valor ou em botão.
- Pesos: regular 400 (corpo), medium 500, semibold 600 (rótulos/CTA), bold 700 (preços/valores de confirmação). Via `--jx-weight-*`.
- Font-family só via token; nenhum `font-family:"X"` inline.

---

## 5. Espaçamento

- Base 4px. Scale: `--jx-space-1..9` (4/8/12/16/24/32/48/64/96).
- Padding de card de checkout: `--jx-space-5` (24px). Gap entre campos do form de cartão: `--jx-space-4` (16px). Gap do grid de planos: `--jx-space-3` (12px).
- **Touch/click target ≥44px** em todo radio de método, CTA e linha de cobrança acionável (a11y).
- Nunca `padding:16px` literal — sempre `var(--jx-space-4)`.

---

## 6. Componentes NOVOS desta fase (especificação)

> Reusar primeiro (§1). Especificar abaixo SÓ o que não existe. Prefixo `jx-`, standalone, OnPush, tokens-only.

### 6.1 `jx-checkout-method-toggle` (escolha cartão | PIX)

- Dois radios grandes (cartão / PIX automático), padrão visual do `.pay` do wireframe 12: borda `--border`, selecionado borda `--brand` + fundo `--brand-wash`. Cada opção ≥44px, `role="radiogroup"`, label associado.
- Acima: linha de segurança — `🔒 Pagamento criptografado · Safe2Pay` (texto, não emoji decorativo isolado; ícone cadeado `aria-hidden`, significado no texto). trust-safety-ux.
- Estados: `idle` (seleção), `processando` (toggle desabilitado, foco preso no painel ativo), `aprovado` (esconde toggle, mostra sucesso), `recusado` (mantém toggle + erro inline).

### 6.2 `jx-card-form` (form de cartão — RSA-OAEP no cliente)

- Campos via `jx-field`: **Nome no cartão** (`autocomplete="cc-name"`), **Número** (`inputmode="numeric"`, `autocomplete="cc-number"`, mono, máscara `#### #### #### ####`), **Validade MM/AAAA** (`autocomplete="cc-exp"`, mono), **CVV** (`inputmode="numeric"`, `autocomplete="cc-csc"`, mono, maxlength 4). CPF do titular (`jx-field` máscara CPF) quando exigido pela cobrança (D-02/SAAS-BILLING §6.1).
- **Segurança visível e mecânica (não negociável):**
  - Antes de enviar, o componente busca a chave pública em `GET /auth/pagamento/chave-publica` e cifra `{nomeTitular,numeroCartao,validade,cvv}` com **RSA-OAEP 2048 (SHA-256)** → base64. **O texto puro do cartão NUNCA sai do componente, nunca vai a estado global, nunca a log, nunca a analytics.** Só o blob cifrado vai no POST `/api/empresas/assinar`.
  - `autocomplete="off"` no `<form>` para CVV não persistir; CVV nunca pré-preenchido.
  - Banda de confiança: cadeado + "Seus dados são criptografados no seu navegador antes de enviar. A Jaxegô não armazena o número do seu cartão." (trust-safety-ux — transparência honesta).
  - Bandeira detectada por BIN só para exibição (mono, últimos 4 após validar) — sem validação externa.
- Validação inline (error-ux): número (Luhn client-side), validade não-expirada, CVV 3-4 dígitos. Erro associado por `aria-describedby` (já no `jx-field`).
- Estados: `idle` / `cifrando+enviando` (botão vira spinner, campos `readonly`) / `aprovado` / `recusado` (erro: causa + "tente outro cartão").

### 6.3 `jx-pix-qr` (PIX automático — QR + copia-e-cola + deep link)

- Renderiza `pix_qr_code_base64` (imagem) + EMV `pix_copy_and_paste` (mono, botão "Copiar código") + `deep_link` (botão "Abrir app do banco", visível em viewport touch).
- Estado **aguardando**: spinner discreto + "Aguardando pagamento…" + `role="status"` `aria-live="polite"`; **polling** do status da autorização (GET `/api/empresas/assinatura`) — a ativação real chega por webhook (SAAS-BILLING §8.1), a UI só reflete `pix_autorizacao_status`.
- Transições: `CRIADA` → (webhook `APROVADA`/`ATIVA`) → `aprovado` (some o QR, mostra sucesso); `CANCELADA`/`EXPIRADA` → erro "Cobrança expirou. Gerar novo QR Code." (regenera).
- "Copiar código" → toast `jx-notice` success "Código PIX copiado".

### 6.4 `jx-subscription-status` (estado da assinatura)

- Banner/card no topo da tela 16. Mostra `status` (mapa §3), plano atual, próximo vencimento (mono, DD/MM/AAAA), método (cartão •••• 4 últimos / PIX).
- Variante por status:
  - **trial**: `--info`, "Teste — N dias restantes" + CTA "Escolher um plano" (sem urgência falsa; N vem da API, mono).
  - **active**: `--success`, "Ativa · renova em DD/MM por R$ X,XX" (mono).
  - **blocked**: `--error` (banner forte, `role="alert"`), copy de regularização (§7) + CTA "Regularizar pagamento" → reabre checkout/link. Explica o bloqueio em texto claro (>10 dias).
  - **cancelado**: `--text-muted`, "Cancelada em DD/MM" + CTA "Reativar plano".
- Nunca color-only: ícone (`aria-hidden`) + rótulo textual + valor mono sempre presentes.

### 6.5 `jx-plan-compare` (upgrade/downgrade — RN-029)

- Reusa `jx-plan-card` em grid; o plano atual marcado `selected` (pílula "Seu plano"). CTA por card depende da relação preço×atual:
  - **mais caro → upgrade**: "Fazer upgrade (cobrança pro-rata hoje)".
  - **mais barato → downgrade**: "Mudar no próximo ciclo (DD/MM)".
- Ao escolher upgrade → **painel de confirmação pro-rata** (§ não-dark-pattern): "Você paga **R$ Y,YY** agora pelos dias restantes deste ciclo e passa para o plano Pro imediatamente." (Y vem do backend, mono). Botões de peso igual: "Confirmar upgrade" e "Cancelar".
  - Downgrade: "Seu plano muda para Início em **DD/MM** (fim do ciclo atual). Até lá você mantém os limites atuais." Sem cobrança agora; botão "Agendar mudança" + "Cancelar" de peso igual.
- **Anti-dark-pattern (payment-checkout-ux / herdado de `jx-upgrade-modal`):** sem contagem regressiva, sem "última chance", sem pré-seleção forçada do plano caro, "Cancelar" com o mesmo peso visual da confirmação, downgrade nunca escondido.

### 6.6 `jx-charge-history` (histórico de cobranças)

- Reusa `jx-data-table`. Colunas: Data (mono DD/MM), Descrição ("Assinatura Início · abril"), Valor (mono), Status (mapa §3 — texto + cor), Ação (2ª via quando houver). Empty state: "Nenhuma cobrança ainda — sua primeira cobrança aparece após ativar um plano."
- A seção "Faturas de taxas (entregas com pagamento direto)" do wireframe 16 fica **fora desta fase** — renderizar placeholder desabilitado "Disponível em breve" (Phase 11), sem dado falso.

### 6.7 Reuso na tela 12 (nova entrega) — pagamento cartão/PIX

- O `<fieldset>` "Pagamento da corrida" já existe (Phase 7, wireframe 12) com 3 radios: **direto** (default, coexiste — RN-023/024) | **PIX** | **cartão**. Phase 7 deixou PIX/cartão "em breve"; **agora ATIVOS**:
  - Selecionar **cartão** → expande `jx-card-form` inline (cripto RSA igual §6.2) abaixo do `jx-estimate-box`.
  - Selecionar **PIX** → ao confirmar, abre `jx-pix-qr` (PIX avulso da corrida) — entrega só nasce `CRIADA` após pagamento confirmado.
  - `jx-estimate-box` (já existente) mostra **corrida + taxa de plataforma** (split implícito; taxa via RN-023 nas 3 modalidades). O valor exato é exibido ANTES de confirmar (payment-checkout-ux).
- **F-03 E3 (recusa):** cartão/PIX falha → **a entrega NÃO nasce**. Erro `role="alert"`: "Cartão recusado. A entrega não foi criada." + 2 saídas de peso igual: **"Tentar de novo"** e **"Pagar direto ao entregador"** (troca para modalidade `direct` sem perder o formulário preenchido).

---

## 7. Copy (texto visível ao usuário) — `br/ux-copywriting-ptbr`

| Localização | Texto | Observação |
|-------------|-------|------------|
| Header tela 16 | "Seu plano" (Fraunces em "plano") | direto |
| CTA primário checkout | "Assinar {plano} — R$ X,XX/mês" (valor mono) | verbo+valor exato, payment-checkout-ux |
| CTA confirmar cobrança | "Confirmar pagamento de R$ X,XX" | valor exato antes de confirmar |
| Banda de segurança cartão | "Seus dados são criptografados no seu navegador antes de enviar. A Jaxegô não armazena o número do seu cartão." | transparência honesta, trust-safety |
| PIX aguardando | "Aguardando o pagamento. Assim que cair, seu plano é ativado." | sem cronômetro de pressão |
| Empty histórico | "Nenhuma cobrança ainda — sua primeira cobrança aparece após ativar um plano." | acionável |
| Trial banner | "Teste — {N} dias restantes. Escolha um plano para continuar sem interrupção." | N da API, sem urgência falsa |
| **Blocked (>10d)** | "Sua assinatura está bloqueada por falta de pagamento (mais de 10 dias em atraso). Regularize para voltar a criar entregas. Após 20 dias o plano é cancelado." | explica causa + consequência + saída (error-ux + SAAS §10) |
| Cancelado | "Sua assinatura foi cancelada. Reative quando quiser para voltar a usar a plataforma." | sem culpa |
| Erro cartão (assinatura) | "Não foi possível processar este cartão. Confira os dados ou use outro cartão. Você também pode pagar por PIX." | causa provável + alternativas |
| Erro cartão (entrega F-03 E3) | "Cartão recusado. A entrega não foi criada. Tente outro cartão ou pague direto ao entregador." | igual ao wireframe 12 |
| PIX expirado | "Esse código PIX expirou. Gere um novo para continuar." | recuperável |
| Upgrade pro-rata | "Você paga R$ Y,YY agora pelos dias restantes deste ciclo e muda para o {plano} na hora." | valor exato, sem letra miúda escondida |
| Downgrade agendado | "Seu plano muda para {plano} em DD/MM (fim do ciclo). Até lá os limites atuais continuam." | honesto, sem perda surpresa |
| Estorno (RN-004) | "Cancelamento após a coleta: cobramos R$ Z,ZZ (100% + retorno). O excedente já pago volta ao seu cartão/PIX em até 5 dias úteis." | regra exata + prazo (F-07 E1) |
| Sucesso assinatura | "Plano {nome} ativado." | pretérito, curto |
| Sucesso pagamento entrega | "Pagamento confirmado. Procurando entregador…" | encadeia ao próximo estado |

**Sem "Ops!", sem jargão (token, gateway, RSA), sem abreviação de valor.** Valores sempre completos em R$ pt-BR.

---

## 8. Estados por tela (mínimo 5)

### 8.1 Tela 16 — Plano e assinatura

| Estado | Quando | Como aparece |
|--------|--------|--------------|
| Loading | carregando assinatura + planos | skeleton do `jx-subscription-status` + grid de cards skeleton (não spinner) |
| Empty (sem cobrança) | assinatura nova/trial | histórico vazio com copy acionável; grid de planos visível |
| Success | assinatura carregada | status banner + planos + histórico |
| Error (API) | 4xx/5xx ao carregar | "Não conseguimos carregar seu plano. Tente novamente." + retry |
| Blocked | inadimplência >10d | banner `--error` `role="alert"` + CTA regularizar (estado de negócio, não erro técnico) |

### 8.2 Checkout (cartão / PIX) — estados de pagamento

| Estado | Cartão | PIX |
|--------|--------|-----|
| idle | form vazio, CTA habilitado | método escolhido, CTA "Gerar PIX" |
| processando | botão spinner, campos readonly, foco preso, `aria-busy` | QR + "Aguardando pagamento" `aria-live=polite`, polling |
| aprovado | sucesso `--success` + "Plano ativado" | webhook APROVADA → some QR + sucesso |
| recusado | erro inline `role=alert` + causa + alternativa PIX | EXPIRADA/CANCELADA → "Gerar novo QR" |

### 8.3 Tela 12 — pagamento da corrida (cartão/PIX ativo)

| Estado | Como aparece |
|--------|--------------|
| Loading estimativa | `jx-estimate-box` skeleton |
| idle | radios método (direto/PIX/cartão), estimativa corrida+taxa, CTA "Chamar entregador" |
| processando | botão spinner; cartão → cifra+cobra; PIX → QR; bloqueia reenvio |
| aprovado | entrega nasce `CRIADA` → toast "Pagamento confirmado. Procurando entregador…" + estado CRIADA |
| recusado (E3) | `role=alert` "Cartão recusado. A entrega não foi criada." + "Tentar de novo" / "Pagar direto" (peso igual) |
| limite de plano (E4) | `jx-upgrade-modal` (já existe) — sem dark pattern |

---

## 9. Interações e micro-animações — `micro-animations-delight`

- CTA ao clicar: scale 0.97 em `--jx-motion-fast` (140ms), `--jx-motion-easing-out`.
- Painel pro-rata / card-form inline: slide-down + fade em `--jx-motion-normal` (220ms).
- Aprovação de pagamento: ✓ em `--success` + fade do checkout 380ms (`--jx-motion-slow`), **uma vez, sem loop**.
- PIX aguardando: pulse discreto no spinner (opacity), respeitando `prefers-reduced-motion` (sem animação → texto estático "Aguardando…").
- Proibido: animação >500ms em ação crítica de pagamento; loop infinito; animar além de `transform`/`opacity`; confete/celebração exagerada em cobrança (é dinheiro, não jogo).

---

## 10. Acessibilidade (AA, dois temas — DEC-001) — `accessibility-pro`

- [ ] Contraste ≥4.5:1 texto / 3:1 grande, **validado nos temas claro E escuro** (camada `_semantic.scss` já tratada).
- [ ] Todo input do `jx-card-form` tem `<label>` (via `jx-field`) + erro associado `aria-describedby`/`aria-invalid`.
- [ ] Radios de método em `role="radiogroup"`, navegáveis por seta, selecionado anunciado.
- [ ] Botão icon-only (copiar PIX, fechar) com `aria-label`.
- [ ] Foco visível (`--focus-ring`) — nunca remover outline; ordem de tabulação lógica no checkout.
- [ ] Painel pro-rata / modais: `role="dialog"` `aria-modal`, focus trap + Esc, foco retorna ao gatilho (padrão herdado de `jx-upgrade-modal`).
- [ ] `jx-pix-qr` aguardando: `role="status"` `aria-live="polite"`; aprovação anunciada.
- [ ] Erro de pagamento: `role="alert"` (assertivo) — usuário precisa saber que falhou.
- [ ] Touch/click ≥44px em radios, CTAs, "copiar código", linhas acionáveis.
- [ ] Status (assinatura/cobrança) **nunca só por cor** — ícone `aria-hidden` + rótulo textual + valor mono sempre.
- [ ] QR Code com `alt`/descrição textual + alternativa copia-e-cola sempre presente (não depende de câmera/visão).
- CI: `axe-core` em staging, zero violação crítica nas telas 16 e 12.

---

## 11. Responsividade

Breakpoints herdados: 320, 480, 768, 1024, 1440.

| Tela | Mobile (320-480) | Tablet (768) | Desktop (1024+) |
|------|------------------|--------------|-----------------|
| 16 plano | status full-width; planos stack 1col; checkout full | planos 2col; checkout em painel | planos 4col; status+histórico lado a lado |
| Checkout cartão | campos stack, CTA sticky acima do teclado | painel centrado max 480px | painel centrado |
| 16b upgrade | cards stack; pro-rata full-screen sheet | 2col + dialog | dialog centrado |
| 12 entrega | form stack; `jx-card-form`/QR inline full | form 620px (wireframe) | form 620px centrado |

---

## 12. Segurança visível — `trust-safety-ux` (resumo executável)

1. **Indicador de segurança** no checkout cartão e na corrida cartão/PIX: cadeado + "Pagamento criptografado · Safe2Pay" (texto + ícone aria-hidden).
2. **Nunca pedir dado desnecessário:** só nome/número/validade/CVV (+CPF quando a cobrança exige). Sem endereço de cobrança se a API não exigir; sem "salvar cartão" opt-in escondido.
3. **Transparência de cobrança:** valor exato (corrida + taxa, ou R$/mês) sempre visível ANTES do botão de confirmação; pro-rata e estorno com valor e prazo explícitos.
4. **Cartão nunca em texto puro:** RSA-OAEP no cliente (§6.2). Sem cartão/CVV/token em estado global, log, analytics, URL ou storage.
5. **Sem padrões de pressão:** sem cronômetro, sem "última chance", sem pré-seleção do plano caro; saída de cancelar sempre de peso igual.

---

## 13. Tabela de tokens citados (Gate 2 — caminho em `tokens.json`)

Todos os tokens abaixo **existem** em `docs/identidade-visual/tokens.json` (v2-jaxego). Componentes consomem a camada semântica (`_semantic.scss`), que deriva mecanicamente destes primitivos. **Nenhum token novo é necessário.**

| Token usado (CSS var semântica) | Deriva de (caminho em tokens.json) | Uso nesta fase |
|---------------------------------|-------------------------------------|----------------|
| `--surface` / `--surface-elevated` / `--surface-sunken` | `color.neutral.50/100/200` (dark: 900/800/700) | fundo da tela, cards de checkout, chip de status |
| `--text` / `--text-muted` / `--text-subtle` | `color.neutral.800/500/400` | corpo, hint, status cancelado |
| `--border` / `--border-strong` | `color.neutral.200/300` | borda de card, campo de cartão |
| `--brand` / `--brand-hover` / `--brand-contrast` | `color.brand.500/600/50` | CTA assinar/confirmar, radio selecionado |
| `--brand-wash` / `--brand-wash-border` | `color.brand.50/100` | fundo do método selecionado, banda de segurança |
| `--success` | `color.semantic.success` (#1B998B) | assinatura active, cobrança PAGA, pagamento aprovado |
| `--warning` | `color.semantic.warning` (#E89B0E) | cobrança em aberto/vencendo |
| `--error` / `--error-bg` | `color.semantic.error` (#C71D1D) / `error_bg` | blocked, cartão recusado, PIX expirado |
| `--info` | `color.semantic.info` (#0A66C2) | trial banner |
| `--focus-ring` | `shadow.focus` (rgba persimmon) | foco em campos/CTA |
| `--shadow-sm` / `--shadow-md` / `--shadow-lg` | `shadow.sm/md/lg` | elevação de card/dialog de checkout |
| `--jx-space-1..9` | `spacing.1..9` (4–96px) | espaçamento, gaps, touch targets |
| `--jx-radius-sm/md/lg/xl/full` | `radius.sm/md/lg/xl/full` | cantos de card, campo, pílula de status |
| `--jx-font-display` / `--jx-font-body` | `font.family.display/body` | títulos e corpo |
| `--jx-font-serif-accent` | `font.family.serif_accent` (Fraunces) | 1 acento no título da tela 16 |
| `--jx-font-mono` | `font.family.mono` (JetBrains Mono) | valores R$, QR copia-e-cola, IDs, •••• cartão |
| `--jx-text-2xs..5xl` | `font.size.*` | escala tipográfica |
| `--jx-weight-regular..extrabold` | `font.weight.*` | pesos (preço bold, rótulo semibold) |
| `--jx-motion-fast/normal/slow` + `--jx-motion-easing-out` | `motion.*` | animação de CTA/painel/aprovação |

---

## 14. Visual regression — `visual-regression-testing`

Componentes novos desta fase com story obrigatória no Storybook (claro + escuro):

- [ ] `jx-checkout-method-toggle` — stories: cartão-selecionado, pix-selecionado, processando, recusado
- [ ] `jx-card-form` — stories: idle, com-erro, cifrando, recusado
- [ ] `jx-pix-qr` — stories: aguardando, aprovado, expirado
- [ ] `jx-subscription-status` — stories: trial, active, blocked, cancelado
- [ ] `jx-plan-compare` — stories: upgrade-prorata, downgrade-agendado
- [ ] `jx-charge-history` — stories: com-dados, vazio

Nome de screenshot: `{component}-{state}-{theme}-{viewport}.png`. Baseline ao fim da fase.

---

## 15. Open questions para o humano

- [ ] **Revenue share da área (OQ-1):** default `[ASSUMIDO]` 20% — afeta apenas o split backend, **não tem superfície visual nesta fase** (relatório é Phase 13). **Recomendação:** não expor ao lojista agora; nenhuma decisão de UI pendente.
- [ ] **Sandbox vs produção (SAAS-BILLING §13):** token de cartão não funciona em sandbox; em piloto a recorrência por cartão só roda em produção. **Recomendação UI:** em ambiente sandbox, exibir nota discreta "Ambiente de teste" no checkout — não bloqueia o contrato visual.
- [ ] **Confirmação do contrato Safe2Pay (OQ-3 / DEC-003):** split/prazo/taxa são `[ASSUMIDO]`. Não muda a UI (valores vêm da API). Revisar copy de estorno/pro-rata se a regra real divergir de RN-004/RN-029.

---

## 16. Approval

- [ ] Humano revisou e aprovou (ou delegou ao ui-checker)
- [ ] ui-checker validou 6 dimensões: tokens, tipografia, copy, estados, interações, acessibilidade
- [ ] Aprovado em: {date}

**Próximo passo:** `/gsd:plan-phase 10` — o planner recebe este UI-SPEC + `docs/SAAS-BILLING-DOCS.md` + skill `safe2pay-escrow-br` como contexto.
