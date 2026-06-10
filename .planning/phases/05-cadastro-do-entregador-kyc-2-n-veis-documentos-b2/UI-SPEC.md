---
phase: 05-cadastro-do-entregador-kyc-2-n-veis-documentos-b2
title: Cadastro do entregador + KYC 2 níveis + documentos B2
status: draft
platform: web+mobile (entregador = Ionic mobile-first; admin de área = web desktop-first)
gate2_visual_contract: pending-checker
generated_by: gsd-ui-researcher
generated_at: 2026-06-10
reuses: 03-shell-frontend-design-system-3-superf-cies, 04-cadastro-e-ativa-o-de-loja
---

# UI-SPEC — Phase 5: Cadastro do entregador + KYC 2 níveis + documentos B2

> Design contract da Phase 5 (Gate 2 — Visual Contract). **BLOQUEIA** `plan-phase` se não existir.
> Plataformas: **superfície Entregador** (Ionic 8, mobile-first, conteúdo ≤480px, captura por câmera) e **superfície Admin de área** (web desktop-first, fila de revisão densa).
> **Regra de ouro Gate 2:** todo valor visual é token. Nenhum `#hex` hardcoded. Toda var/token citado existe em `docs/identidade-visual/tokens.json` (§9) ou na camada semântica da Phase 3 (`_semantic.scss`).
> **Princípio desta phase:** *reusar*, não reinventar. Temas claro/dark (DEC-001), tipografia, motion, 4 componentes de estado, `jx-wizard-stepper` e `jx-field` **já existem** (Phase 3/4). Aqui especificamos só o **novo**: o upload de documento com câmera (`jx-doc-upload`), o card de documento com status (`jx-doc-card`), a fila e a revisão item-a-item do admin, e os estados especiais `pending_kyc` / `mei_pending` / reenvio item-a-item / escalação 48h.

---

## Fontes de verdade consultadas

- `.planning/phases/05-.../05-CONTEXT.md` — decisões D-01..D-08 (wizard, área, 2 níveis ADR-011, item-a-item, B2 ADR-004, MEI/RN-024, status).
- `docs/identidade-visual/tokens.json` — tokens **canônicos** (FONTE da verdade visual).
- `.planning/phases/03-.../UI-SPEC.md` — design system estabelecido (21 CSS vars semânticas claro/dark, tipografia, motion, 4 componentes de estado). Contrato herdado.
- `.planning/phases/04-.../UI-SPEC.md` — **padrão de wizard já estabelecido** (`jx-wizard-stepper`, `jx-field`, máquina de estado por passo, persistência de progresso, formulários BR, anti-enumeração). **Seguimos o mesmo padrão.**
- `apps/web/src/` — código real a reusar: `shared/state/*` (4 estados), `shared/components/wizard-stepper/*`, `shared/components/field/*`, `core/theme/*`, `styles/_semantic.scss` + `_tokens.scss` + `typography.scss`, `features/loja/cadastro/*` (padrão de wizard/máscaras/persistência/PII).
- `projeto/wireframes/03-cadastro-entregador.html`, `projeto/wireframes/19-admin-area-entregador-detalhe.html` — contratos DOM.
- `projeto/regras-negocio/fluxos.md` §F-02 (`:27-48`) — etapas 1-9 + exceções E1-E5.
- `.planning/ROADMAP.md` Phase 5 — flags (has_ui, has_api, mobile, integration_check, has_pii) + skills obrigatórias.

### Skills aplicadas (matriz UI + flags Phase 5)

- `product/component-library-governance` — **reusar** os 4 estados (Phase 3) + `jx-wizard-stepper`/`jx-field` (Phase 4). Novos componentes governados (story + baseline §10): `jx-doc-upload`, `jx-doc-card`, `jx-kyc-review-row`, `jx-kyc-queue-table`.
- `ux-advanced/design-tokens-system` — consumir só camada semântica (`var(--surface)`, `var(--brand)`); nunca primitivo nem hex.
- `ui-ux-pro-max` — editorial-técnica: IDs (`cou_…`), CPF mascarado, CNAE, placa e timestamps em mono; Fraunces italic em 1 palavra-chave do H1; persimmon como única cor de ação. **Anti AI-slop:** sem gradiente, sem dropzone "glow", sem check animado festivo, sem badge neon.
- `ux-advanced/file-upload-ux` — **núcleo desta phase:** captura câmera/galeria, preview, estados idle/selecionando/comprimindo/enviando(%)/sucesso/erro, mensagens acionáveis, retomada, upload via URL pré-assinada (não bloqueia UI).
- `ux-advanced/gesture-touch-patterns` (mobile) — alvos ≥44px, toque para abrir câmera, sem gesto destrutivo escondido, feedback de toque (scale .97), foto em tela cheia por tap no preview.
- `quality/accessibility-pro` — AA nos dois temas, foco visível, touch ≥44px, upload operável por teclado, erros via `aria-describedby`, progresso por `aria-live`, status por texto+ícone (nunca só cor).
- `br/ux-copywriting-ptbr` — sentence case, CTA verbo+objeto sem ponto, erro = o que houve + o que fazer, **anti-enumeração** na colisão de CPF (E2).
- `br/brazilian-forms` — máscara/validação CPF (dígito), telefone BR → E.164, placa Mercosul, MEI/CNPJ; `inputmode="numeric"`, **nunca `type="number"`**.
- `ux-advanced/form-ux-mastery` — wizard com stepper, validação inline no blur, persistência parcial (retomada 30 dias), foco gerenciado entre passos, um erro por campo.
- `quality/error-ux-patterns` — `jx-error-state` `role="alert"`, `jx-warn-banner` não-bloqueante para `mei_pending`, mensagem acionável.
- `ux-advanced/onboarding-patterns` — wizard progressivo, retomada parcial com lembretes (dia 3/7), tela de "em análise" pós-submit (não modal intrusivo).
- `ux-advanced/trust-safety-ux` — transparência LGPD: por que pedimos cada documento, segurança do upload (bucket privado), banner `mei_pending` explicativo (não punitivo), motivo verificável na reprovação.
- `owasp-security` — upload seguro (content-type/tamanho validados, sem PII em log, URL assinada de expiração curta), proteção de dados sensíveis.
- `br/lgpd-compliance` — consentimento de uso de documentos (KYC), aviso de retenção/anonimização (RN-021), nunca expor documento por URL pública.
- `quality/observability-production` — `request_id` do erro logado, não exibido (salvo fallback técnico).
- `domain/ionic-patterns` — wizard do entregador em Ionic (`ion-content`, safe-area, captura nativa via `capture`), tabbar do shell preservada.

---

## Telas / estados cobertos por esta fase

1. **§2 — Tela 03: Wizard do entregador** (Ionic, mobile-first): (1) área + dados, (2) selfie com documento, (3) veículo, (4) documentos completos condicionais (CNH/CRLV/MEI/antecedentes).
2. **§3 — `jx-doc-upload`** (upload de documento com câmera/galeria, preview, estados, compressão, URL pré-assinada).
3. **§4 — `jx-doc-card`** (card de documento com status por item: pending/uploading/approved/rejected + reenvio).
4. **§5 — Tela 19: Painel de revisão do admin de área** (fila de KYC + revisão item-a-item: aprovar/reprovar com motivo, status por item, escalação).
5. **§6 — Estados especiais:** `pending_kyc` (em análise), `mei_pending` (banner permanente), reprovação item-a-item (reenvio só do item), escalação 48h.
6. **§7 — Trust & safety / LGPD**; **§8 — Acessibilidade**; **§9 — Tabela de tokens (Gate 2)**; **§10 — Visual regression**.

**Fora de escopo (deferido — NÃO especificar aqui):**
- **Etapa 5 do wireframe 03 (bairros que atende + tabela de preços/piso)** → **Phase 6**. O stepper desta phase NÃO inclui "Bairros e preços".
- Online/offline/busy + ofertas/despacho → Phase 8.
- Bloqueio de repasse via plataforma por MEI (RN-010) + saques → Phase 10/11.
- Score do entregador (bloco "Score" do wireframe 19) → Phase 13 — renderizado como placeholder inerte `—`, não interativo nesta phase.
- Recurso de suspensão (RN-016) UI completa → Phase 13 (aqui o painel mostra a ação "Suspender com motivo" do wireframe, mas o fluxo de recurso é fora de escopo).

---

## 1. Reuso do design system Phase 3/4 (não reinventar)

Esta phase **herda integralmente** o contrato visual. Não redefine temas, tipografia, motion nem os componentes já existentes. Referências canônicas:

| Asset herdado | Arquivo real (apps/web) | Uso na Phase 5 |
|---|---|---|
| Temas claro/dark (21 vars semânticas) | `styles/_semantic.scss` | tudo consome `var(--surface)`, `var(--brand)`, etc. DEC-001 vale no wizard e no painel admin. |
| Tokens primitivos `--jx-*` | `styles/_tokens.scss` (gerado de tokens.json) | nunca consumidos direto em componente. |
| Tipografia (escala + italic + mono) | `styles/typography.scss` | H1 com Fraunces italic; CPF/CNPJ/CNAE/placa/IDs/timestamps em mono. |
| Anti-FOUC + toggle de tema | `index.html` + `core/theme/*` | já no shell; wizard e painel respeitam tema ativo. |
| `jx-empty-state` | `shared/state/empty-state.component.ts` | fila de KYC vazia (admin); "em análise" pós-submit (entregador). |
| `jx-error-state` (`role="alert"`) | `shared/state/error-state.component.ts` | CPF já cadastrado na mesma área (E2), falha de passo, erro ao carregar documento (URL assinada expirada). |
| `jx-warn-banner` (`role="status"`, dispensável/persistente) | `shared/state/warn-banner.component.ts` | **`mei_pending`** (persistente, NÃO dispensável); aviso de upload offline-pendente. |
| `jx-loading-skeleton` | `shared/state/loading-skeleton.component.ts` | validação CPF/MEI em curso, carga da fila de KYC, thumbnail de documento carregando. |
| `jx-wizard-stepper` | `shared/components/wizard-stepper/wizard-stepper.component.ts` | stepper do wizard do entregador (3 ou 4 passos conforme nível). |
| `jx-field` | `shared/components/field/field.component.ts` | nome, CPF, nascimento, telefone, email, senha, placa, MEI/CNPJ. Já encapsula `aria-describedby`, máscara, mono, erro, foco. |
| Padrão de wizard/persistência/PII | `features/loja/cadastro/*` | máquina de estado por passo, retomada de progresso, máscaras BR, sem senha em storage, anti-enumeração. |

**Novos componentes compartilháveis desta phase** (governança `component-library-governance`, ganham story + baseline §10):
- `jx-doc-upload` — campo de upload de documento (câmera/galeria + preview + estados + %).
- `jx-doc-card` — card de um documento com status por item (compõe `jx-doc-upload` no wizard; modo somente-leitura no painel admin).
- `jx-kyc-review-row` — linha de revisão de um item no painel admin (thumb + dados + aprovar/reprovar com motivo).
- `jx-kyc-queue-table` — fila de KYC do admin de área (data-tables + saas-dashboard).

Tudo abaixo usa **apenas** vars semânticas já existentes. **Nenhuma var semântica nova é necessária.**

---

## 2. Tela 03 — Wizard do entregador (Ionic, mobile-first — D-01/D-02)

### 2.1 Plataforma e layout

- **Superfície Entregador** = Ionic 8 dentro do shell `ion-tabs` da Phase 3. O wizard abre fora das tabs (rota dedicada `/entregador/cadastro`), `ion-content` com `--surface`, padding lateral `--jx-space-4` (16), conteúdo centrado `max-width` 480px (acompanha wireframe), **safe-area insets** respeitados (notch/home indicator).
- **CTA principal fixo (mobile keyboard avoidance):** botão "Continuar" / "Enviar para análise" em barra inferior sticky acima do teclado (`ion-footer` ou sticky com `env(safe-area-inset-bottom)`), full-width, ≥44px.
- **H1 (do wireframe):** "Entregue na sua cidade. Comece *hoje.*" — `hoje.` em Fraunces italic `--brand` weight 500, `font.size.2xl` (28) ou `xl` (22) em telas estreitas, -.02em. Regra do italic: 1 palavra só.

### 2.2 `jx-wizard-stepper` (reuso Phase 4) — passos condicionais ao nível KYC

O stepper é **dinâmico** conforme o nível exigido pela área escolhida (D-03):

| Nível da área | Passos | Rótulos (overline, uppercase) |
|---|---|---|
| **SIMPLES** | 3 | `1 Dados` · `2 Selfie` · `3 Veículo` |
| **COMPLETA** | 4 | `1 Dados` · `2 Selfie` · `3 Veículo` · `4 Documentos` |

- A etapa "Bairros e preços" do wireframe **NÃO entra** (Phase 6). O número de passos do stepper é definido **após** a escolha da área (passo 1), pois é a área que define o nível. Antes disso o stepper assume o caminho mais curto e expande se a área exigir completa (transição anunciada por `aria-live`).
- Anatomia/tokens/a11y do stepper: **idênticos à Phase 4 §2.2** (nó concluído `--brand` + check, nó atual `--brand` contornado, futuro `--surface-sunken`/`--text-subtle`, conector `--border`/`--brand`; `<nav><ol>`, `aria-current="step"`, "Passo N de M" em `aria-live="polite"`, não depende só de cor).

### 2.3 Passo 1 — Área + dados (D-01 etapa 1, D-02)

Campos via `jx-field` (mesmas regras visuais da Phase 4 §3: borda `--border-strong`, fundo `--surface-elevated`, focus `--focus-ring`, erro `--error`, ≥44px):

| Campo | Tipo / atributos | Máscara / validação |
|---|---|---|
| Cidade onde vai entregar (área) | `select` `required` — lista de áreas **ativas** | seleção obrigatória; define o nível KYC do stepper |
| Nome completo | `text` `required` `autocomplete="name"` | não-vazio |
| CPF | `text` `inputmode="numeric"` `autocomplete="off"` `aria-describedby` | máscara `000.000.000-00`; **dígito verificador** (front+back) + situação (Receita, async no submit do passo); mono quando válido |
| Data de nascimento | `date` `required` | maioridade conforme regra |
| Telefone | `tel` `inputmode="numeric"` `autocomplete="tel"` placeholder "(22) 99999-1234" | máscara BR → **E.164** ao submeter; OTP por SMS (sub-bloco abaixo) |
| E-mail | `email` `inputmode="email"` `autocomplete="email"` | formato; confirmação por link em paralelo (não bloqueia) |
| Senha | `password` `minlength="10"` `autocomplete="new-password"` + toggle mostrar/ocultar (`aria-label`) | ≥10 chars (argon2id no back); **nunca persistida em storage** |

- **Confirmação telefone (SMS OTP):** sub-bloco com campo OTP `inputmode="numeric"` `autocomplete="one-time-code"` `maxlength="6"` em mono + "Reenviar SMS" (cooldown, contador mono). Mesmo padrão da Phase 4 §3.2.
- **E2 — CPF já cadastrado na MESMA área (anti-enumeração):** `jx-error-state` (`role="alert"`) — **"Você já tem cadastro nessa cidade. Recupere o acesso."** + link "Recuperar acesso" (`--info`). CPF em OUTRA área → permite (novo vínculo). Mensagem única e idêntica; não revela mais do que o informado.

### 2.4 Passo 2 — Selfie com documento (D-01 etapa 2)

- Um único `jx-doc-card` do tipo **selfie** (§4) usando `jx-doc-upload` (§3) com `capture="user"` (câmera frontal).
- Instrução (trust-safety): "Tire uma foto sua segurando seu documento (CNH ou RG). É só para confirmar que é você."
- Microcopy de privacidade abaixo (LGPD, §7): "Sua foto vai criptografada e só o admin da sua cidade vê. A gente nunca publica."

### 2.5 Passo 3 — Veículo (D-01 etapa 3)

| Campo | Tipo | Validação |
|---|---|---|
| Tipo | `select` `required` (Moto / Bicicleta / Carro / A pé) | obrigatório |
| Placa (se motorizado) | `text` placeholder "ABC1D23" | máscara/validação placa Mercosul; **só obrigatória** se tipo ∈ {moto, carro}; mono quando preenchida; oculta para bicicleta/a pé |

### 2.6 Passo 4 — Documentos completos (condicional — D-01 etapa 4, D-03, D-07)

Aparece **só se a área exige COMPLETA**. Abre com aviso de contexto (`jx-warn-banner` `role="status"`, não-dispensável, informativo):

> "Pádua pede validação **completa**: CNH com EAR, CRLV e MEI. Sem MEI você ainda entrega recebendo direto da loja." *(cidade dinâmica; texto do wireframe + RN-024)*

Itens (cada um é um `jx-doc-card`, §4):

| Item | Componente | Obrigatório? | Particularidade |
|---|---|---|---|
| CNH com EAR | `jx-doc-card` upload (`capture="environment"`) | sim (completa) | foto; back valida legibilidade no review |
| CRLV | `jx-doc-card` upload | sim (completa) | foto |
| MEI (CNPJ) | `jx-field` CNPJ + status auto | **não** (opcional) | consulta Receita: situação + CNAEs (`4930-2/01`, `4930-2/02`, `5320-2/02`, `5229-0/99`). Ausente/inativo → segue com **`mei_pending`** (§6.2) |
| Antecedentes criminais | `jx-doc-card` upload | só se a área exigir | renderiza condicionalmente |

- **Submit:** botão "Enviar para análise" → status `pending_kyc` (§6.1). Botão secundário "Salvar e continuar depois" (outline `--brand`, do wireframe) → salva rascunho (retomada 30 dias, D-01/E1).

### 2.7 Estados por passo (idle / validando / erro / sucesso) — padrão Phase 4

Idêntico à Phase 4 §2.3: CTA "Continuar" só habilita com passo válido; `validando` mostra `jx-loading-skeleton` + `aria-busy`; erro de campo via `jx-field` + `aria-describedby`; erro de passo via `jx-error-state` `role="alert"`; sucesso avança e marca nó concluído. **Diferença mobile:** durante upload de documento o passo NÃO bloqueia (upload assíncrono via URL pré-assinada, §3.4) — o usuário pode continuar enquanto o arquivo sobe.

### 2.8 Persistência e retomada (D-01 / E1 — retomada 30 dias)

- Progresso salvo em `sessionStorage`/back a cada passo válido (**nunca senha**; CPF/CNPJ mascarado em memória — padrão PII Phase 4). Retomada por **30 dias** (server-side draft), lembretes e-mail dia 3 e dia 7.
- Indicador discreto "Rascunho salvo" `font.size.xs` `--text-subtle` ao concluir passo (não toast).
- **Documentos já enviados sobrevivem à retomada:** ao voltar, `jx-doc-card` mostra estado `enviado` (thumbnail via URL assinada) — não re-upload.

### 2.9 Motion (gesture-touch + reduced-motion)

- Toque no botão/upload: scale .97 `motion.fast` (140ms). Troca de passo: slide horizontal `motion.normal` (220ms) `easing_out`. Preview de foto: fade-in `motion.fast`. **`prefers-reduced-motion`** → fade simples, sem slide/scale.

---

## 3. `jx-doc-upload` — upload de documento (file-upload-ux + owasp-security)

Componente compartilhável central. Encapsula captura, preview, validação, compressão e upload via URL pré-assinada.

### 3.1 Anatomia (dropzone editorial-técnica, anti-slop)

- **Estado idle:** área tracejada `2px dashed --border-strong`, fundo `--surface-sunken`, radius `lg` (10), padding `--jx-space-5` (24), centrada. Ícone leve (Ionicon câmera/documento) `--text-subtle`; rótulo `font.size.sm` (13) `--text-muted`; **dois botões** ≥44px: "Tirar foto" (`--brand` fill) e "Escolher da galeria" (outline `--brand`). **Sem "glow", sem gradiente.**
- **Mobile (Ionic):** "Tirar foto" usa `<input type="file" accept="image/*" capture="environment|user">` (câmera nativa). Galeria = mesmo input sem `capture`.

### 3.2 Estados (file-upload-ux — máquina completa)

| Estado | Quando | Aparência | A11y |
|---|---|---|---|
| **idle** | sem arquivo | dropzone + 2 botões | `aria-label` no input; operável por teclado |
| **selecionando** | abrindo câmera/galeria | botão em press, sem bloqueio de tela | — |
| **comprimindo** | pós-seleção, antes do upload | preview esmaecido + texto "Otimizando a imagem…" + `jx-loading-skeleton` fino | `aria-busy="true"` |
| **enviando (%)** | upload em curso | preview + **barra de progresso** (`--brand` sobre `--surface-sunken`, radius `full`) + "% enviado" em mono | progresso em `aria-live="polite"` ("Enviando 60%") |
| **sucesso** | upload concluído (hash confirmado) | preview nítido + selo "Enviado" `--success` (ícone + texto) + ação "Trocar foto" | `role="status"` "Documento enviado" |
| **erro** | falha de tipo/tamanho/rede/hash | borda `--error`, mensagem acionável (`--error`) + botão "Tentar de novo" | `role="alert"`, foco move ao erro |

### 3.3 Validação e feedback de compressão (client-side, owasp)

- **Tipo:** só `image/*` (JPEG/PNG/HEIC) — PDF aceito só onde a área pedir (antecedentes). Tipo inválido → erro "Esse arquivo não é uma imagem. Tire uma foto ou escolha uma da galeria."
- **Tamanho:** valida antes do upload (limite ex. 10 MB pré-compressão). Acima → erro "A imagem é muito grande. Tente outra ou tire uma foto nova."
- **Compressão:** redimensiona client-side para máx 1920px e converte para WebP/JPEG **antes** do upload (reduz dados móveis); feedback "Otimizando a imagem…". Compressão server-side definitiva (1920px/WebP) + **hash SHA-256** confirmados no back (D-05).
- **Preview:** miniatura do arquivo escolhido; tap abre em tela cheia (gesture-touch). Foto borrada/escura: orientação textual "Confira se está legível antes de enviar" (não bloqueia, mas o admin pode reprovar — E4).

### 3.4 Upload via URL pré-assinada (não bloqueia a UI — D-05/ADR-004)

- Fluxo: cliente pede **URL pré-assinada** ao backend → faz **PUT direto ao B2** (não passa pelo backend) → confirma com o backend (hash). Indicar no spec: **o upload roda em background**; o usuário pode avançar no wizard enquanto a barra de progresso completa.
- **Resiliência offline (CONTEXT §specifics / offline-tolerante):** se o upload falhar por rede, o arquivo fica retido no device e um `jx-warn-banner` (`role="status"`, não-bloqueante) avisa "Sem conexão. Sua foto sobe sozinha quando a internet voltar." Reenvio automático ao reconectar; o passo não trava.
- **Segurança (owasp/LGPD):** nenhuma URL pública; só URL assinada de expiração curta. PII (CPF/documento) **nunca** em log. Bucket privado `jaxego-kyc-prod`.

---

## 4. `jx-doc-card` — card de documento com status por item (D-04)

Card que representa **um documento e seu status de KYC**. Dois modos: **edição** (wizard do entregador — compõe `jx-doc-upload`) e **leitura** (entregador acompanhando análise; admin revisando).

### 4.1 Anatomia

- Container: fundo `--surface-elevated`, borda `--border`, radius `lg` (10), padding `--jx-space-4` (16). Topo: nome do documento (`font.size.sm` (13) weight 600 `--text`) + **badge de status** (§4.2). Corpo: thumbnail/preview (ou `jx-doc-upload` no modo edição) + metadados em mono `font.size.xs` (12) `--text-muted` (ex. "enviado 23/04", "Honda Biz · ABC1D23", "CNAE 5320-2/02 · Receita: ATIVO").

### 4.2 Status por item (badge — texto + ícone + cor, nunca só cor)

| Status | Badge texto | Token cor texto | Fundo | Ícone |
|---|---|---|---|---|
| **pending** (aguardando análise) | "Em análise" | `--warning` | `--warning-bg` | relógio |
| **uploading** (enviando) | "Enviando…" | `--info` | `--info-bg` | seta-cima |
| **approved** | "Aprovado" | `--success` | `--success-bg` | check |
| **approved (auto)** (MEI via Receita) | "Aprovado (automático)" | `--success` | `--success-bg` | check |
| **rejected** | "Reprovado" | `--error` | `--error-bg` | alerta |
| **mei_pending** (MEI ausente/inativo) | "MEI pendente" | `--warning` | `--warning-bg` | info |

- Badge: radius `full`, padding `--jx-space-1`/`--jx-space-2`, `font.size.2xs` (11) weight 600 uppercase. No **dark**, fundos `_bg` claros não funcionam → herda o padrão da Phase 3: fundo `--surface-elevated` + texto/borda na cor semântica viva.

### 4.3 Reenvio item-a-item (D-04 / E4) — modo entregador

- Documento **reprovado** mostra: badge "Reprovado" + **motivo específico** do admin (`font.size.xs` `--error`, ex. "Ilegível", "Sem EAR", "Vencida") + `jx-doc-upload` reaberto **só para aquele item** com CTA "Reenviar CNH".
- **Invariante (CONTEXT §specifics):** reprovar a CNH **não invalida** selfie já aprovada. Cada `jx-doc-card` tem status independente; só o item reprovado fica editável.
- Anúncio: ao reprovar, o entregador recebe notificação; ao abrir, foco no card reprovado, `role="alert"` com o motivo.

---

## 5. Tela 19 — Painel de revisão do admin de área (saas-dashboard + data-tables)

Superfície **Admin** (web desktop-first, layout sidebar da Phase 3). Densa, mono nos dados, sem festividade.

### 5.1 `jx-kyc-queue-table` — fila de KYC (data-tables-ux)

Lista de entregadores `pending_kyc` da área do admin (AreaScoped).

- **Colunas:** Entregador (nome + `cou_…` em mono) · Nível exigido (simples/completa, badge) · Itens (ex. "2 de 4 aprovados", mono) · Esperando há (tempo relativo; **destaca ≥48h** — escalação §6.4) · Ação ("Revisar →").
- **Tokens:** cabeçalho `--surface-sunken` + `--text-muted` overline; linhas `--surface`/`--surface-elevated` (zebra opcional via `--surface-elevated`); divisor `--border`; hover de linha `--brand-wash`. Linha em escalação (≥48h): selo `--warning` + ícone (texto "Atrasada", não só cor).
- **Estados (data-tables):** loading = `jx-loading-skeleton` (linhas); **vazio** = `jx-empty-state` "Nenhum entregador na fila. Quando alguém se cadastrar, aparece aqui." (causa + contexto, sem CTA falso); erro = `jx-error-state` com retry.
- **A11y:** `<table>` semântica com `<th scope="col">`; ordenação por "Esperando há" com `aria-sort`; cada linha navegável por teclado; "Revisar" ≥44px de área de clique.

### 5.2 Cabeçalho do detalhe (do wireframe 19)

- Voltar "← Entregadores" (`--info`). H1: nome + `cou_…` em mono `--text-muted`. Subtítulo `font.size.sm` `--text-muted`: "Validação exigida em *Pádua*: **completa** · cadastro há 2 dias · moto ABC1D23" (placa em mono). Contador "Itens da validação · 2 de 4 aprovados" (`font.size.md` weight 600).

### 5.3 `jx-kyc-review-row` — revisão item-a-item (D-04)

Uma linha por documento, dentro de um card `--surface-elevated` (radius `lg`, padding `--jx-space-4`). Grid: **thumb (90×64) · dados · ação** (do wireframe).

- **Thumb:** preview via **URL assinada de expiração curta** (D-05). Estado de carga = `jx-loading-skeleton` (bloco). Tap/click abre o documento em visualizador full-size (também via URL assinada, expira). Falha/expirou = `jx-error-state` "Não foi possível abrir o documento. Recarregue." + retry (regenera URL).
- **Dados:** nome do item (weight 600) + metadados mono `--text-muted` (CPF mascarado `123.***.***-09`, CNAE, "enviada há 5h", placa). **CPF sempre mascarado** (PII/LGPD).
- **Ação por item:**
  - **Aprovar** — botão `--success` fill, ≥44px. Item vira `approved` otimista + grava `audit_log`.
  - **Reprovar** — botão outline `--error` (`--error` texto + borda). Ao clicar, revela **`<select>` de motivo** (enum) + **`<textarea>` de detalhe** obrigatório. Motivos (enum do wireframe): Ilegível · Sem EAR · Vencida · Não confere com o titular (variam por item). **Reprovar sem motivo é bloqueado** → `jx-error-state` "Selecione o motivo antes de reprovar — o entregador precisa saber o que corrigir." (texto do wireframe).
  - Itens **automáticos** (MEI via Receita) aparecem como "Aprovado (automático)" sem botões.
- **Status visual por item:** mesmo vocabulário de badges do `jx-doc-card` §4.2 (texto+ícone+cor).
- **Nota de processo (do wireframe):** "A reprovação avisa o entregador com o motivo e libera reenvio só do item reprovado. Tudo fica no audit log." `font.size.xs` `--text-muted`.
- **Bloco Score (Phase 13):** renderizado como placeholder inerte (`—` em mono), **não interativo** nesta phase. Bloco "Ações · Suspender com motivo" do wireframe presente (select motivo + textarea obrigatórios), mas o **fluxo de recurso** é Phase 13.

### 5.4 Estados do painel admin

| Estado | Quando | Aparência |
|---|---|---|
| **loading** | carga do detalhe/fila | `jx-loading-skeleton` (linhas da fila / cards de item) |
| **success** | dados carregados | fila + revisão item-a-item |
| **empty** | fila sem pendências | `jx-empty-state` (§5.1) |
| **error** | 4xx/5xx, ou URL de documento expirada | `jx-error-state` `role="alert"` + retry (regenera URL assinada) |
| **ação otimista** | aprovar/reprovar | item atualiza na hora; rollback + `jx-error-state` se a chamada falhar |

---

## 6. Estados especiais

### 6.1 `pending_kyc` — em análise (pós-submit do entregador)

- Após "Enviar para análise" → tela de status (não modal), reusa `jx-empty-state` variante informativa: ícone `--text-subtle`, título "Recebemos seu cadastro." causa/ação "Estamos conferindo seus dados. Avisamos assim que liberar — costuma sair rápido." Lista os `jx-doc-card` em modo leitura com status "Em análise" por item.
- Sem festividade (sem confete). `role="status"`. Não bloqueia o app (entregador pode navegar nas tabs, mas não fica online — Phase 8).

### 6.2 `mei_pending` — banner permanente (D-07 / RN-024 — trust-safety)

- **Quando:** validação completa, MEI ausente/inativo na Receita. Cadastro **segue**; flag `mei_pending`.
- **Componente:** `jx-warn-banner` (`role="status"`, **persistente, NÃO dispensável**) — fixo no topo do perfil/início do entregador.
- **Copy (trust-safety, explicativo não punitivo):** "Você ainda **não tem MEI ativo**. Pode entregar recebendo **direto da loja**. Para receber pela plataforma, regularize seu MEI." + CTA "Como regularizar" (`--info`, abre orientação) e/ou "Adicionar MEI" (reabre o item, `--brand`).
- **Tokens:** `--warning`/`--warning-bg` (dark: `--surface-elevated` + `--warning` vivo). Borda esquerda 3px `--warning`.
- **Importante:** o **bloqueio de repasse** por falta de MEI (RN-010) é Phase 10/11 — aqui só o banner + restrição lógica ao "direto". Não especificar fluxo de saque.

### 6.3 Reprovação item-a-item (D-04 / E4)

- Coberto em §4.3 (entregador) e §5.3 (admin). Reforço: notificação ao entregador com **motivo específico**; reenvio libera **só o item**; itens aprovados permanecem aprovados.

### 6.4 Escalação 48h (E5)

- **Admin de área:** na fila (`jx-kyc-queue-table`), entregadores esperando ≥48h ganham selo "Atrasada" (`--warning`, ícone + texto) e sobem para o topo (ordenação por tempo). Não é erro — é prioridade.
- **Visibilidade admin plataforma:** mesmos itens aparecem numa visão consolidada (fila cross-área) — mesmo componente `jx-kyc-queue-table` com coluna extra "Área". Notificação ao admin de área disparada pelo back; a UI só reflete o selo.
- **A11y:** o atraso é comunicado por texto ("Atrasada · esperando há 53h") além do selo colorido.

---

## 7. Trust & safety / LGPD (trust-safety-ux + lgpd-compliance + owasp)

- **Por que pedimos cada documento (transparência):** cada `jx-doc-card` no wizard tem microcopy curta de propósito:
  - Selfie: "Confirma que é você de verdade."
  - CNH com EAR: "Mostra que você pode dirigir fazendo entregas."
  - CRLV: "Confirma que o veículo está regular."
  - MEI: "Necessário só para você receber pela plataforma."
- **Segurança do upload (visível ao usuário):** linha de confiança no passo de documentos: "Seus documentos vão **criptografados**, ficam num cofre privado e só o admin da sua cidade vê. **Nunca** publicamos." (reflete bucket privado + URL assinada).
- **Consentimento (LGPD):** antes de "Enviar para análise", checkbox/aceite "Concordo com o uso dos meus dados e documentos para validação, conforme a [Política de Privacidade]." (`--info` link). Base legal de consentimento registrada.
- **Retenção/anonimização (RN-021):** nota discreta "Seus documentos são guardados só pelo tempo necessário e depois anonimizados." `font.size.xs` `--text-subtle`.
- **Admin:** CPF sempre mascarado na fila e no detalhe; documento só via URL assinada de expiração curta; toda aprovação/reprovação/suspensão gravada em `audit_log` (visível como nota de processo).

---

## 8. Acessibilidade (accessibility-pro — AA nos dois temas)

- **Contraste AA nos DOIS temas:** herda mapas validados da Phase 3 (`--text`/`--surface`, `--brand-contrast`/`--brand`, semânticos sobre superfície escura no dark). Badges de status, barra de progresso, fila e cards validados claro+dark pelo checker (axe + contraste).
- **Foco visível:** `--focus-ring` (`shadow.focus`) em todo interativo — campos, botões de upload, "Tirar foto"/"Galeria", aprovar/reprovar, select de motivo, links. Nunca `outline:none` sem substituto.
- **Touch ≥44×44px (mobile):** "Continuar"/"Enviar para análise", botões de upload, toggle de senha, reenviar SMS, "Trocar foto", CTAs de banner. Admin: "Revisar", "Aprovar", "Reprovar" com área de clique ≥44px.
- **Upload acessível por teclado:** `<input type="file">` operável por teclado (Tab + Enter); botões "Tirar foto"/"Escolher da galeria" são `<button>`s reais; preview tem alt/`aria-label` descritivo ("Pré-visualização da CNH"); abrir em tela cheia também por teclado.
- **Labels e erros:** todo input com `<label for>`; erro associado por **`aria-describedby`**; `aria-invalid="true"` no campo inválido (exceto E2 colisão — sem campo individual, para não vazar).
- **Live regions:** progresso de upload `aria-live="polite"` ("Enviando 60%"); `jx-error-state` `role="alert"`; `jx-warn-banner`/`jx-empty-state`/sucesso de upload `role="status"`; skeleton `aria-hidden` + container `aria-busy`; troca de passo "Passo N de M" `aria-live="polite"`.
- **Status nunca só por cor:** badges de documento e selo de escalação sempre com **texto + ícone** além da cor.
- **Teclado:** ordem de tabulação lógica por passo; Enter avança passo válido; passos concluídos voltáveis; tabela do admin navegável e ordenável por teclado; `prefers-reduced-motion` desliga slide/scale/pulse.
- **`lang="pt-BR"`**, landmarks `<main>`/`<nav>`/`<section>`/`<table>`. `axe-core` no wizard e no painel admin: zero violações críticas (verificação ROADMAP).

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
| `spacing.1` / `.2` / `.4` / `.5` (4/8/16/24px) | — | ✅ |
| `radius.lg` / `full` (10/9999px) | — | ✅ |
| `font.family.display` | Inter Tight… | ✅ |
| `font.family.serif_accent` | Fraunces… | ✅ |
| `font.family.mono` | JetBrains Mono… | ✅ |
| `font.size.2xs` / `xs` / `sm` / `base` / `md` / `xl` / `2xl` (11/12/13/14/16/22/28) | — | ✅ |
| `font.weight.regular` / `medium` / `semibold` (400/500/600) | — | ✅ |
| `shadow.focus` (→ `--focus-ring`) | rgba(232,78,27,.28) | ✅ |
| `motion.fast` / `normal` / `easing_out` (140/220ms / cubic-bezier) | — | ✅ |

**Tokens referenciados que NÃO existem em tokens.json: NENHUM (0).** Nenhuma var semântica nova foi necessária — a Phase 5 reusa integralmente as 21 vars da Phase 3. Gate 2 satisfeito.

---

## 10. Visual regression (baseline desta phase)

Novos componentes/telas que recebem story + baseline (`product/visual-regression-testing`):

- [ ] `jx-doc-upload` — stories: idle, comprimindo, enviando-60%, sucesso, erro-tipo, erro-rede · claro+dark · mobile
- [ ] `jx-doc-card` — stories: edição, em-análise, aprovado, reprovado-com-motivo, mei-pendente · claro+dark
- [ ] `jx-kyc-review-row` — stories: aprovar, reprovar-motivo-aberto, auto-aprovado, thumb-carregando · claro+dark
- [ ] `jx-kyc-queue-table` — stories: com-fila, fila-vazia, item-escalado-48h, loading · claro+dark
- [ ] `cadastro-entregador` (tela 03) — stories: passo-1-dados, passo-2-selfie, passo-3-veículo, passo-4-documentos, CPF-já-cadastrado (E2), pending_kyc, mei_pending · claro+dark · mobile
- [ ] `admin-kyc-detalhe` (tela 19) — stories: revisão-2-de-4, reprovar-sem-motivo (bloqueio), documento-expirado · claro+dark

Nome screenshot: `{component}-{state}-{theme}-{viewport}.png`.

---

## 11. Open questions para o humano

- [ ] **Antecedentes criminais — formato:** alguns entregadores recebem PDF da emissão. **Recomendação:** aceitar imagem **e** PDF só neste item; demais documentos só imagem. Confirmar.
- [ ] **Compressão client-side antes do upload:** reduz dados móveis mas adiciona dependência. **Recomendação:** comprimir no cliente (máx 1920px) + recompressão server-side definitiva (D-05). Sem impacto no contrato visual. Confirmar.
- [ ] **`mei_pending` — CTA "Como regularizar":** abre orientação interna (texto) ou link externo (gov.br)? **Recomendação:** página interna de orientação curta + link externo no fim. Confirmar.

---

## Approval

- [ ] Humano revisou e aprovou (ou delegou ao ui-checker)
- [ ] ui-checker validou 6 dimensões: tokens, tipografia, copy, estados, interações, acessibilidade
- [ ] Gate 2 (Visual Contract) verde — tokens citados existem em tokens.json (§9)
- [ ] Wireframe-contract de `03-cadastro-entregador.html` e `19-admin-area-entregador-detalhe.html` coberto (verificação ROADMAP) — exceto etapa 5 (bairros/preços → Phase 6) e bloco Score (→ Phase 13), deferidos por escopo
- [ ] Aprovado em: {date}

**Próximo passo:** `/gsd:plan-phase 5` — o planner recebe este UI-SPEC como contrato de design.
