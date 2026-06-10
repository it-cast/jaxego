---
phase: 04-cadastro-e-ativa-o-de-loja
title: Cadastro e ativação de loja
status: draft
platform: web (superfície Loja — responsivo fluido)
gate2_visual_contract: pending-checker
generated_by: gsd-ui-researcher
generated_at: 2026-06-10
reuses: 03-shell-frontend-design-system-3-superf-cies
---

# UI-SPEC — Phase 4: Cadastro e ativação de loja

> Design contract da Phase 4 (Gate 2 — Visual Contract). **BLOQUEIA** `plan-phase` se não existir.
> Plataforma: **superfície Loja** (web responsivo fluido, container centrado 520–620px), Angular 19 standalone.
> **Regra de ouro Gate 2:** todo valor visual é token. Nenhum `#hex` hardcoded. Toda var/token citado existe em `docs/identidade-visual/tokens.json` (§9) ou na camada semântica da Phase 3 (`_semantic.scss`).
> **Princípio desta phase:** *reusar*, não reinventar. O sistema de temas, tipografia, motion e os 4 componentes de estado já existem (Phase 3). Aqui especificamos só o **novo**: o wizard de cadastro, os formulários BR, os estados de exceção F-01 E1–E4, o estado vazio "Ainda não chegamos aí", a seleção de plano e o onboarding pós-ativação.

---

## Fontes de verdade consultadas

- `.planning/phases/04-.../04-CONTEXT.md` — decisões D-01..D-09, F-01, anti-enumeração, planos como seeds (DRV-009), estado vazio obrigatório.
- `docs/identidade-visual/tokens.json` — tokens **canônicos** (FONTE da verdade visual).
- `.planning/phases/03-.../UI-SPEC.md` — **design system estabelecido** (21 CSS vars semânticas claro/dark, tipografia, motion, componentes de estado). Contrato herdado.
- `apps/web/src/` — **código real** a reusar: `shared/state/*` (EmptyState/ErrorState/LoadingSkeleton/WarnBanner), `core/theme/*`, `styles/_semantic.scss` + `_tokens.scss` + `typography.scss`, `features/auth/login.page.*` (padrão de form/estados).
- `projeto/wireframes/02-cadastro-loja.html`, `projeto/wireframes/16-loja-plano.html` — contratos DOM.
- `projeto/regras-negocio/fluxos.md` §F-01 (`:7-24`); `regras.md` RN-011 (anti-duplicidade), RN-021 (LGPD/PII), RN-028 (Free 2/mês).
- `.planning/ROADMAP.md` Phase 4 — flags (has_ui, has_api, has_pii, integration_check) + skills obrigatórias.

### Skills aplicadas (matriz UI + flags Phase 4)

- `product/component-library-governance` — **reusar** os 4 componentes de estado da Phase 3; o wizard é composição, não componentes novos de estado. Novo componente compartilhável governado: `jx-wizard-stepper`, `jx-field` (input + label + erro + máscara), `jx-plan-card`.
- `ux-advanced/design-tokens-system` — consumir só camada semântica (`var(--surface)`, `var(--brand)`); nunca primitivo nem hex.
- `ui-ux-pro-max` — direção editorial-técnica: dados em mono (CNPJ, valores de plano), Fraunces italic em 1 palavra-chave do H1, persimmon como única cor de ação. **Anti AI-slop:** sem gradiente genérico, sem card de plano "glow", sem confete.
- `quality/accessibility-pro` — AA nos dois temas, foco visível, touch ≥44px, erros via `aria-describedby`, `role`/`aria-live` por estado.
- `ux-advanced/empty-states-polish` — **reusar** `jx-empty-state` para "Ainda não chegamos aí" (causa + ação de captura de interesse).
- `br/ux-copywriting-ptbr` — sentence case, CTA verbo+objeto sem ponto, erro = o que houve + o que fazer, **anti-enumeração** na colisão.
- `br/brazilian-forms` — máscara/validação CNPJ/CPF (dígito verificador), telefone BR → E.164, CEP via ViaCEP, `inputmode="numeric"`, **nunca `type="number"`**.
- `ux-advanced/form-ux-mastery` — wizard com stepper, validação inline no blur, persistência de progresso parcial, um erro por campo associado por `aria-describedby`, foco gerenciado entre passos.
- `quality/error-ux-patterns` — `jx-error-state` `role="alert"`, `jx-warn-banner` não-bloqueante para pending_*, mensagem acionável.
- `ux-advanced/onboarding-patterns` — hint de primeira-entrega no dashboard pós-ativação (não modal intrusivo).
- `quality/observability-production` — `request_id` do erro logado, não exibido (salvo fallback técnico) — herdado do padrão login.
- `br/lgpd-compliance` — consentimento explícito de Termos/Privacidade antes de submeter; e-mail de captura de interesse com base legal de consentimento.

---

## Telas / estados cobertos por esta fase

1. **§2 — Tela 02: Wizard de cadastro de loja** (4 passos: identificação → confirmação e-mail/SMS → endereço/área → plano)
2. **§3 — Formulários BR** (CNPJ/CPF, telefone E.164, CEP+endereço com autocomplete)
3. **§4 — Estados de exceção F-01 E1–E4** (CNPJ inativo, colisão anti-enumeração, pending_payment, pending_validation)
4. **§5 — Estado vazio "Ainda não chegamos aí"** (endereço fora de área + captura de interesse)
5. **§6 — Tela 16: Seleção de plano** (cards, Free pré-selecionado, sem dark pattern, valores de SEEDS)
6. **§7 — Onboarding pós-ativação** (hint de primeira entrega no dashboard)
7. **§8 — Acessibilidade**; **§9 — Tabela de tokens (Gate 2)**

**Fora de escopo (deferido):** checkout pago real Safe2Pay e tabela de faturas/cobranças da tela 16 (Phase 10 — aqui só o caminho Free e os avisos pending_*), cadastro de entregador (Phase 5), criação de entregas (Phase 7). **A tabela de faturas do wireframe 16 NÃO é especificada aqui.**

---

## 1. Reuso do design system da Phase 3 (não reinventar)

Esta phase **herda integralmente** o contrato visual da Phase 3. Não redefine temas, tipografia, motion nem componentes de estado. Referências canônicas:

| Asset herdado | Arquivo real (apps/web) | Uso na Phase 4 |
|---|---|---|
| Temas claro/dark (21 vars semânticas) | `styles/_semantic.scss` | tudo consome `var(--surface)`, `var(--brand)`, etc. DEC-001 vale em todo wizard. |
| Tokens primitivos `--jx-*` | `styles/_tokens.scss` (gerado de tokens.json) | nunca consumidos direto em componente. |
| Tipografia (escala + italic + mono) | `styles/typography.scss` | H1 com Fraunces italic; valores de plano e CNPJ em mono. |
| Anti-FOUC + toggle de tema | `index.html` (script) + `core/theme/theme.service.ts` + `theme-toggle.component.ts` | já no shell da Loja; cadastro respeita tema ativo. |
| `jx-empty-state` | `shared/state/empty-state.component.ts` | **estado "Ainda não chegamos aí"** (§5). |
| `jx-error-state` (`role="alert"`) | `shared/state/error-state.component.ts` | erro de CNPJ inativo (E1), colisão (E2), falha de passo. |
| `jx-warn-banner` (`role="status"`, dispensável) | `shared/state/warn-banner.component.ts` | aviso persistente pending_payment (E3) e pending_validation (E4). |
| `jx-loading-skeleton` | `shared/state/loading-skeleton.component.ts` | validação Receita em curso, geocoding, carga de planos. |
| Padrão de form/estados | `features/auth/login.page.*` | máscaras, `aria-busy`, foco no erro, sem token em localStorage. |

**Novos componentes compartilháveis desta phase** (governança `component-library-governance`, ganham story + baseline em §10):
- `jx-wizard-stepper` — indicador de passos.
- `jx-field` — wrapper input/label/erro/máscara (encapsula `aria-describedby`, máscara BR, estado de validação).
- `jx-plan-card` — card de plano (tela 16), data-driven por SEED.

Tudo abaixo usa **apenas** vars semânticas já existentes. Nenhuma var semântica nova é necessária.

---

## 2. Tela 02 — Wizard de cadastro de loja (D-01, F-01 passos 1–7)

### 2.1 Layout e cabeçalho

- **Container:** superfície Loja, `<main>` centrado `max-width` 520–620px (acompanha wireframe), margem topo `--jx-space-6` (32), padding lateral `--jx-space-4` (16). Responsivo fluido: em mobile vira full-width com padding `--jx-space-4`.
- **H1 (do wireframe):** "Cadastre sua loja. É *rapidinho.*" — `rapidinho.` em Fraunces italic `--brand` weight 500, `font.size.2xl` (28), -.02em. Regra do italic: 1 palavra só.
- **Stepper** logo abaixo do H1 (§2.2).
- **Footer de consentimento (LGPD, do wireframe):** "Ao continuar você concorda com os [Termos] e a [Política de Privacidade]." — `font.size.xs`, `--text-subtle`, links `--info`. Aparece no passo final, antes do submit.

### 2.2 `jx-wizard-stepper` (form-ux-mastery)

Indicador horizontal de 4 passos. Substitui os `fieldset` empilhados do wireframe por navegação por passos com persistência (Discretion D-01: stepper + progresso parcial).

| Passo | Rótulo (pt-BR) | Conteúdo |
|---|---|---|
| 1 | Identificação | CNPJ/CPF, nome da loja, categoria |
| 2 | Confirmação | e-mail (link) + telefone (SMS OTP) |
| 3 | Endereço | CEP + endereço → geocoding → vínculo de área |
| 4 | Plano | seleção de plano (Free pré-selecionado) → ativar |

- **Anatomia:** linha de 4 nós (`full` radius), nó concluído `--brand` com check, nó atual `--brand` contornado + label `--text` weight 600, nó futuro `--surface-sunken` + label `--text-subtle`. Conector entre nós `--border` (futuro) / `--brand` (concluído).
- **Tokens:** nó ativo/concluído `--brand`/`--brand-contrast`; futuro `--surface-sunken`/`--text-subtle`; conector `--border`; gap `--jx-space-2`; label `font.size.xs` (12) uppercase letter-spacing .08em (overline pattern).
- **A11y:** `<nav aria-label="Etapas do cadastro">` com `<ol>`; passo atual `aria-current="step"`; passos concluídos clicáveis para voltar (`<button>`), futuros não-interativos. Indicador textual "Passo 2 de 4" em `aria-live="polite"` ao trocar. Não depende só de cor — usa check + peso + `aria-current`.
- **Motion:** transição de passo = slide horizontal `motion.normal` (220ms) `easing_out`; respeita `prefers-reduced-motion` (fade simples).

### 2.3 Estados por passo (idle / validando / erro / sucesso)

Cada passo tem máquina de estado local. CTA "Continuar" só habilita com o passo válido.

| Estado | Quando | Aparência | A11y |
|---|---|---|---|
| **Idle** | passo montado, sem interação | campos vazios/preenchidos do progresso salvo, CTA "Continuar" habilitado se já válido | foco no 1º campo do passo |
| **Validando** | submit do passo / chamada async (Receita, OTP, geocoding) | CTA desabilitado + `jx-loading-skeleton` no slot do resultado; campo com spinner inline mono opcional; `aria-busy="true"` no form | sem duplo submit |
| **Erro de campo** | validação inline falha (dígito/formato) | `jx-field` em estado erro: borda `--error`, mensagem `--error` abaixo via `aria-describedby` | `aria-invalid="true"`, foco move ao 1º campo inválido |
| **Erro de passo** | exceção async (E1/E2/E4) | `jx-error-state` (`role="alert"`) acima do CTA do passo | foco move ao alerta |
| **Sucesso de passo** | passo válido + async ok | avança ao próximo passo (sem toast festivo); marca nó concluído no stepper | `aria-live` anuncia novo passo |

### 2.4 Persistência de progresso parcial (D-01 Discretion)

- Progresso salvo em `sessionStorage('jx-merchant-onboarding')` a cada passo válido (somente dados **não-sensíveis** e não-PII-bruta — **NUNCA senha**; CNPJ/CPF mascarado em memória, conforme padrão PII fora de log). Ao recarregar, retoma no último passo incompleto.
- Indicador discreto "Rascunho salvo" `font.size.xs` `--text-subtle` ao concluir passo (não toast).
- LGPD: o rascunho local é limpo ao ativar a loja ou ao expirar a sessão; sem persistência server-side de cadastro incompleto além do necessário.

---

## 3. Formulários BR (brazilian-forms + form-ux-mastery + error-ux-patterns)

`jx-field` encapsula label + input + máscara + erro + estado. Todos os inputs: borda repouso `--border-strong`, fundo `--surface-elevated`, texto `--text`, radius `md` (6), padding `--jx-space-3` (12); focus → `--focus-ring`; erro → borda `--error`. Label `font.size.sm` (13) weight 600 `--text`. Placeholder `--text-subtle`. Altura mínima do toque ≥44px.

### 3.1 Passo 1 — Identificação

| Campo | Tipo / atributos | Máscara | Validação inline |
|---|---|---|---|
| Documento (CNPJ ou CPF) | `text`, `inputmode="numeric"`, `autocomplete="off"`, `aria-describedby="doc-error"`, `maxlength` 18 (CNPJ) | CNPJ `00.000.000/0001-00` / CPF `000.000.000-00` (detecta por contagem de dígitos) | **dígito verificador** (front + back); rejeita sequências repetidas; `type` nunca `number` |
| Nome da loja | `text`, `required`, `autocomplete="organization"` | — | não-vazio, ≤120 chars |
| Categoria | `select`, `required` (opções do wireframe: Restaurante/Lanchonete, Comércio, Farmácia, Mercado, Outro) | — | seleção obrigatória (placeholder "Selecione…" não-submetível) |

- **Mono nos dados:** o documento, uma vez válido, exibe-se em `font.family.mono` (padrão ui-ux-pro-max: IDs/documentos em mono).
- Validação de CNPJ na Receita acontece no submit do passo (assíncrono → §4 E1/E4), não no blur.

### 3.2 Passo 1 (cont.) / Passo 2 — Contato e acesso

| Campo | Tipo / atributos | Máscara/normalização | Validação |
|---|---|---|---|
| Telefone (WhatsApp) | `tel`, `inputmode="numeric"`, `autocomplete="tel"`, `aria-describedby="phone-error"`, placeholder "(22) 99999-1234" | exibe `(DD) 9XXXX-XXXX`; **normaliza para E.164** `+55DDXXXXXXXXX` ao submeter | DDD válido + 11 dígitos (celular) |
| E-mail | `email`, `inputmode="email"`, `autocomplete="email"`, `aria-describedby="email-error"` | — | formato + domínio plausível |
| Senha | `password`, `minlength="10"`, `autocomplete="new-password"`, toggle mostrar/ocultar com `aria-label` | — | ≥10 chars (herda regra login); **nunca persistida em storage** |

- **Passo 2 — Confirmação:** após criar conta, dois sub-blocos: "Confirme seu e-mail" (instrução: "Enviamos um link para *email*. Abra para confirmar.") com botão "Reenviar link" (desabilitado em cooldown, contador mono); "Confirme seu telefone" com campo OTP `inputmode="numeric"` `autocomplete="one-time-code"` `maxlength="6"` em `font.family.mono`, botão "Reenviar SMS" (cooldown). Estado de envio = `jx-loading-skeleton`; falha de OTP = `jx-error-state` acionável ("Código incorreto. Confira e tente de novo, ou reenvie.").

### 3.3 Passo 3 — Endereço com autocomplete (CEP via ViaCEP)

| Campo | Tipo / atributos | Comportamento |
|---|---|---|
| CEP | `text`, `inputmode="numeric"`, `autocomplete="postal-code"`, `aria-describedby="cep-error"`, maxlength 9 | máscara `00000-000`; ao completar 8 dígitos → busca **ViaCEP** (autocomplete de rua/bairro/cidade/UF), estado `validando` com skeleton nos campos auto-preenchidos |
| Rua e número | `text`, `required`, `autocomplete="address-line1"` | rua autopreenchida (editável); número sempre manual |
| Bairro | `text`, `required`, `autocomplete="address-level3"` | autopreenchido (editável) |
| Cidade / UF | `text` readonly autopreenchido | de ViaCEP |

- Após endereço completo → **geocoding** (adapter, Discretion) → vínculo de área. Estado `validando` com skeleton no slot de resultado.
- **Sem cobertura de área** → renderiza §5 (estado vazio "Ainda não chegamos aí") no lugar do CTA do passo. **Com cobertura** → chip de confirmação "Você está na área de *Pádua*" (Fraunces italic na cidade, ou mono no codename) e libera passo 4.
- CEP inexistente/ViaCEP fora: `jx-warn-banner` não-bloqueante "Não encontramos esse CEP. Preencha o endereço manualmente." (não impede prosseguir — resiliência).

### 3.4 Regras de erro acionáveis (error-ux-patterns + ux-copywriting-ptbr)

- Um erro por campo, abaixo do input, `font.size.xs` `--error`, associado por `aria-describedby`. Formato: **o que houve + o que fazer**, nunca "Campo inválido".
- Exemplos: "CNPJ incompleto. Confira os 14 dígitos." · "Esse CEP tem 8 dígitos. Faltam alguns." · "Telefone precisa de DDD e 9 dígitos." · "A senha precisa de pelo menos 10 caracteres."
- Validação inline **no blur** (não a cada tecla), exceto contagem de senha que pode dar feedback progressivo positivo.

---

## 4. Estados de exceção F-01 E1–E4

Todos reusam componentes da Phase 3. Nenhum hex novo; cores semânticas mapeadas claro/dark já resolvidas em `_semantic.scss`.

### 4.1 E1 — CNPJ inativo/inexistente na Receita (bloqueante)

- **Componente:** `jx-error-state` (`role="alert"`) no passo 1, após resposta da Receita.
- **Copy (do wireframe + suporte):** "CNPJ não está ativo na Receita Federal. Confira o número ou fale com o suporte." + link "Falar com o suporte" (`--info`).
- **Tokens:** `--error`, `--error-bg`, borda esquerda 3px `--error`, radius `md`, padding `--jx-space-3`.
- **Comportamento:** bloqueia avanço; o campo documento fica `aria-invalid`; foco move ao alerta.

### 4.2 E2 — Colisão de dados (anti-enumeração, RN-011)

- **Componente:** `jx-error-state` (`role="alert"`).
- **Copy (RN-011 / F-01 E2 — NUNCA revelar QUAL dado colide):** **"Já existe uma conta com esse dado. Quer recuperar o acesso?"** + link "Recuperar acesso" → fluxo de login/recuperação.
- **Regra inviolável:** mensagem **única e idêntica** se colidir CNPJ, telefone OU e-mail. O frontend exibe `error.message` vindo do backend (já anti-enumeração); não infere nem destaca campo específico. Sem `aria-invalid` em campo individual (não revelar por foco qual colidiu).
- **Tokens:** idênticos ao E1.

### 4.3 E3 — Pagamento da assinatura falha → pending_payment

- Nesta phase só o caminho Free ativa de fato. Se o usuário escolheu plano pago (§6), o merchant é criado em `pending_payment` e usa Free imediatamente.
- **Componente:** `jx-warn-banner` (`role="status"`, **persistente, não dispensável** neste caso) no topo do dashboard pós-cadastro.
- **Copy:** "Seu pagamento do plano *Profissional* ainda não foi concluído. Você está usando o Free por enquanto." + CTA "Concluir pagamento" (`--brand`) → (Phase 10; aqui leva a tela de plano).
- **Tokens:** `--warning`, `--warning-bg`, borda esquerda 3px `--warning`. No dark: fundo `--surface-elevated` (neutro escuro) + texto/borda `--warning` vivos (padrão herdado).
- **Não-bloqueante:** loja opera no Free; banner permanece até pagamento concluir.

### 4.4 E4 — Receita Federal fora do ar → pending_validation

- Cadastro **segue** (resiliência — não bloqueia); merchant em `pending_validation`, usa Free com limite, job revalida (retry 6/6/12/24h).
- **Componente:** `jx-warn-banner` (`role="status"`, persistente) no dashboard.
- **Copy:** "Estamos confirmando seu CNPJ na Receita. Sua loja já funciona no plano Free enquanto isso." (sem alarme — é degradação esperada).
- **Tokens:** `--warning`/`--warning-bg`.
- **Diferença de E1:** E1 é bloqueio (Receita respondeu "inativo"); E4 é Receita indisponível → segue com aviso. Visualmente: E1 = `error` no passo; E4 = `warning` no dashboard.

---

## 5. Estado vazio "Ainda não chegamos aí" (D-05, F-01 passo 5 — obrigatório)

Endereço geocodificado sem área cobrindo. **Reusa `jx-empty-state`** da Phase 3 (causa + ação), com slot de captura de interesse.

- **Onde:** substitui o resultado do passo 3 (não é erro — é estado legítimo de cobertura).
- **Anatomia:** ícone/glyph leve `--text-subtle` → título `font.size.lg` `--text` → frase de causa `font.size.base` `--text-muted` → bloco de captura (e-mail + cidade) + CTA.
- **Copy (causa + ação, do wireframe, brand voice):**
  - Título: **"Ainda não chegamos na sua cidade."**
  - Causa/ação: "Deixe seu e-mail e a cidade que avisamos quando o Jaxegô chegar aí."
- **Captura de interesse (LGPD — consentimento):** `jx-field` e-mail (`autocomplete="email"`) + `jx-field` cidade (texto, pré-preenchida do ViaCEP se houver) → CTA **"Avisar quando chegar"** (`--brand`, verbo+objeto). Submete a `/v1/interest` (do wireframe).
- **Pós-captura:** troca para confirmação inline `jx-empty-state` com `--success` no ícone: "Pronto. Avisaremos *você* assim que chegarmos." (sem festividade exagerada).
- **Tokens:** fundo `--surface`; ícone `--text-subtle`; CTA `--brand`/`--brand-contrast`; sucesso `--success`; padding `--jx-space-6` (32).
- **A11y:** `role="status"`; foco move ao título ao aparecer; campos com label; CTA touch ≥44px.

---

## 6. Tela 16 — Seleção de plano (D-06/D-07, valores de SEED)

**Apenas a seção de planos** da tela 16 (a tabela de faturas/cobranças é Phase 10). Usada no passo 4 do wizard e como tela standalone de gestão de plano.

### 6.1 `jx-plan-card` (data-driven — valores de SEED, NUNCA hardcode)

- **Regra dura (DRV-009):** preço, limite de entregas e taxa vêm de `subscription_plans` (SEED via API). **Proibido hex/valor literal de plano no template.** O card recebe `{ codename, nome, preco, entregas_mes, taxa_entrega, is_current, is_free }` da API. Os valores R$0/R$49/R$129/R$299 do wireframe são **ilustrativos do seed**, não constantes de UI.
- **Anatomia (do wireframe):** grid responsivo (4 col desktop → 2 col tablet → 1 col mobile), gap `--jx-space-3`. Cada card: fundo `--surface-elevated`, borda 2px `--border`, radius `lg` (10), padding `--jx-space-4`, centrado.
  - Nome do plano (`font.size.lg` weight 600).
  - **Preço em mono** (`font.family.mono`, `font.size.xl` (22), weight extrabold) — formatado pt-BR "R$ 0".
  - Detalhes `font.size.xs` `--text-muted`: "2 entregas/mês · taxa R$ 2,00/entrega" (valores do seed).
  - CTA por estado (§6.2).
- **Plano selecionado/atual:** borda `--brand` (2px) + pílula "SEU PLANO" topo-centro (`--brand`/`--brand-contrast`, `radius.full`, `font.size.2xs` (11) uppercase). Free vem **pré-selecionado** no cadastro.

### 6.2 Sem dark pattern (CONTEXT §specifics — botão "agora não" visível)

| Estado do card | CTA | Tokens |
|---|---|---|
| Free, pré-selecionado no cadastro | "Continuar no Free" (primário visível, `--brand` fill) — **igual peso** que upgrade | `--brand`/`--brand-contrast` |
| Plano pago, no cadastro | "Escolher *Profissional*" (outline `--brand`) → leva a pending_payment (E3) nesta phase | borda `--brand`, texto `--brand`, fundo transparente |
| Plano atual (gestão) | "Plano atual · 12/40 usadas" (desabilitado, `--text-muted`) | — |
| Downgrade/upgrade (gestão) | "Mudar no próximo ciclo" / "Fazer upgrade" | outline/fill `--brand` |

- **Anti-dark-pattern explícito:** no passo 4 do cadastro, a ação "Continuar no Free" tem **o mesmo destaque visual** que escolher um plano pago (não escondida, não cinza, não "pular"). Sem checkbox pré-marcado de upgrade, sem contagem regressiva de "oferta".
- **Comparativo:** os 4 cards lado a lado já são o comparativo; diferenças (entregas/mês, taxa) na mesma posição em cada card para varredura vertical.
- **A11y:** `<section aria-label="Planos disponíveis">`; cada card é `<article>`; CTA touch ≥44px; estado "atual" comunicado por texto além de cor.

---

## 7. Onboarding pós-ativação (onboarding-patterns, F-01 passo 7)

Após loja `active` (Free ativado), dashboard da Loja libera com hint de primeira entrega — **não modal intrusivo**.

- **Componente:** card de boas-vindas no topo do dashboard (`jx-empty-state` reusado, variante com CTA) — pois a loja ainda não tem entregas.
- **Copy (brand, primeira-entrega):** Título "Tudo pronto. Bora a *primeira* entrega?" (Fraunces italic em "primeira"). Causa/ação: "Crie sua primeira entrega e acompanhe em tempo real." + CTA "Criar entrega" (`--brand`).
- **Onboarding leve:** no máximo 1 hint persistente + dispensável (`jx-warn-banner` ou tooltip ancorado), nunca tour de múltiplos passos bloqueante (onboarding-patterns: progressive disclosure, não tour forçado).
- **Coexistência com pending_*:** se a loja está em pending_payment (E3) ou pending_validation (E4), o `jx-warn-banner` correspondente aparece **acima** do hint de onboarding. Ordem: aviso de status → hint de primeira entrega.
- **Tokens:** card `--surface-elevated`, CTA `--brand`; sem festividade (sem confete/gradiente — ui-ux-pro-max).

---

## 8. Acessibilidade (accessibility-pro — AA nos dois temas)

- **Contraste AA nos DOIS temas:** herda mapas validados da Phase 3 (`--text`/`--surface`, `--brand-contrast`/`--brand`, semânticos sobre superfície escura no dark). Cards de plano, stepper e campos validados em claro+dark pelo checker (axe + contraste).
- **Foco visível:** `--focus-ring` em todo interativo (campos, CTAs do stepper, cards de plano, toggles). Nunca `outline:none` sem substituto.
- **Touch ≥44×44px:** CTA "Continuar"/"Ativar", botões do stepper, reenviar OTP/SMS, CTA de plano, "Avisar quando chegar", mostrar/ocultar senha.
- **Labels e erros:** todo input com `<label for>`; cada erro associado por **`aria-describedby`** ao input; `aria-invalid="true"` no campo inválido (exceto E2 colisão — sem campo individual, para não vazar qual dado).
- **Live regions:** `jx-error-state` `role="alert"` (E1/E2/erro de passo); `jx-warn-banner`/`jx-empty-state` `role="status"` (E3/E4/sem-área); skeleton `aria-hidden` + form `aria-busy` durante validação; troca de passo anunciada `aria-live="polite"` ("Passo 2 de 4").
- **Stepper sem depender de cor:** passo atual/concluído marcado por `aria-current="step"` + check + peso, não só persimmon.
- **Teclado:** ordem de tabulação lógica por passo; Enter avança passo válido; passos concluídos voltáveis por teclado; `prefers-reduced-motion` desliga slide do stepper e pulse do skeleton.
- **`lang="pt-BR"`**, landmarks `<main>`/`<nav>`/`<section>`. `axe-core` no wizard e na seleção de plano: zero violações críticas (verificação ROADMAP).

---

## 9. Tabela de tokens citados (Gate 2 — todos existem em `tokens.json`)

Cada token referenciado, com caminho em `docs/identidade-visual/tokens.json`. **Confirmado: 100% existem (zero inventados).** Toda var semântica usada (`--surface`, `--brand`, `--error`, `--warning`, `--success`, `--info`, `--focus-ring`, etc.) já está definida em `apps/web/src/styles/_semantic.scss` (Phase 3), derivada das primitivas abaixo.

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
| `spacing.2` / `.3` / `.4` / `.6` (8/12/16/32px) | — | ✅ |
| `radius.md` / `lg` / `full` (6/10/9999px) | — | ✅ |
| `font.family.display` | Inter Tight… | ✅ |
| `font.family.serif_accent` | Fraunces… | ✅ |
| `font.family.mono` | JetBrains Mono… | ✅ |
| `font.size.2xs` / `xs` / `sm` / `base` / `lg` / `xl` / `2xl` (11/12/13/14/18/22/28) | — | ✅ |
| `font.weight.regular` / `medium` / `semibold` / `extrabold` (400/500/600/800) | — | ✅ |
| `shadow.focus` (→ `--focus-ring`) | rgba(232,78,27,.28) | ✅ |
| `motion.normal` / `easing_out` (220ms / cubic-bezier) | — | ✅ |

**Tokens referenciados que NÃO existem em tokens.json: NENHUM (0).** Nenhuma var semântica nova foi necessária — a Phase 4 reusa integralmente as 21 vars da Phase 3. Gate 2 satisfeito.

---

## 10. Visual regression (baseline desta phase)

Novos componentes/telas que recebem story + baseline (`product/visual-regression-testing`):

- [ ] `jx-wizard-stepper` — stories: passo-1/2/3/4, concluído · claro+dark
- [ ] `jx-field` — stories: idle, focus, erro, mono-preenchido, com-máscara · claro+dark
- [ ] `jx-plan-card` — stories: free-selecionado, pago-outline, atual-desabilitado · claro+dark
- [ ] `cadastro-loja` (tela 02) — stories: passo-1, validando, erro-CNPJ (E1), colisão (E2), sem-área (§5) · claro+dark
- [ ] `selecao-plano` (tela 16) — stories: grid-4-planos, free-pré-selecionado · claro+dark
- [ ] `dashboard-pos-ativacao` — stories: onboarding-hint, pending_payment (E3), pending_validation (E4) · claro+dark

Nome screenshot: `{component}-{state}-{theme}-{viewport}.png`.

---

## 11. Open questions para o humano

- [ ] **Geocoding provider:** Discretion (CONTEXT) — Nominatim/OSM atrás de adapter. Sem impacto visual; UI só consome o resultado (área coberta / sem cobertura). Confirmar provider não bloqueia este UI-SPEC.
- [ ] **Confirmação e-mail/telefone — ordem:** o wizard assume confirmação no passo 2 (após criar conta, antes do endereço). Alternativa: confirmar e-mail por link em background e exigir só OTP de telefone no fluxo. **Recomendação:** OTP de telefone inline (bloqueante leve no passo 2) + link de e-mail confirmável em paralelo, sem travar o passo 3 se o e-mail ainda não foi clicado (resiliência). Confirmar.

---

## Approval

- [ ] Humano revisou e aprovou (ou delegou ao ui-checker)
- [ ] ui-checker validou 6 dimensões: tokens, tipografia, copy, estados, interações, acessibilidade
- [ ] Gate 2 (Visual Contract) verde — tokens citados existem em tokens.json (§9)
- [ ] Wireframe-contract de `02-cadastro-loja.html` coberto (verificação ROADMAP)
- [ ] Aprovado em: {date}

**Próximo passo:** `/gsd:plan-phase 4` — o planner recebe este UI-SPEC como contrato de design.
