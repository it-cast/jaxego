# Phase 3: Shell frontend + design system (3 superfícies) - Context

**Gathered:** 2026-06-10 (modo --auto, decisões recomendadas)
**Status:** Ready for planning

<domain>
## Phase Boundary

Entrega o **shell frontend** e o **design system** do Jaxegô como base das 3 superfícies (app do entregador mobile-first / painel da loja web responsivo / admin desktop-first), num único codebase Angular 19 standalone + Ionic 8. Inclui: scaffold do `apps/web`, geração de CSS vars a partir de `tokens.json` com **tema claro E escuro** (DEC-001), componentes de estado canônicos (empty / error / loading skeleton / warn — REQ-055), alternância de tema, tipografia (Inter Tight + Fraunces italic + JetBrains Mono), e a **tela de login** (wireframe 01) conectada ao `/v1/auth/login` da Phase 2. **Não** entrega telas de cadastro (Phase 4/5), dashboards de negócio, nem qualquer fluxo de entrega — apenas o shell, o design system e o login.
</domain>

<decisions>
## Implementation Decisions

### Stack frontend (ADR-003 — travada)
- **D-01:** Angular 19 standalone + signals + OnPush default + control flow novo (@if/@for); Ionic 8 para componentes mobile; lazy por rota (DRV-004). [auto] travado por ADR-003.
- **D-02:** SCSS + CSS vars geradas de `tokens.json` (build step). **Zero cor hardcoded** fora da geração de tokens (verificação automatizada do ROADMAP). [auto] travado (DRV-008).

### Design system + dark mode (DEC-001)
- **D-03:** Dois temas — claro e escuro — desde o M1. Mapeamento por CSS vars semânticas (`--surface`, `--surface-elevated`, `--text`, `--text-muted`, `--border`, `--brand`, etc.) com valores por tema derivados das ESCALAS EXISTENTES de `tokens.json` (claro: neutral-50/100 surfaces, neutral-700/800 text; dark: neutral-900/800 surfaces, neutral-50/100 text; brand mantém persimmon com ajuste de luminância no dark). **Não inventar hex novo** — usar as escalas já definidas (mantém Gate 2). [auto] DEC-001.
- **D-04:** Alternância de tema: respeita `prefers-color-scheme` por padrão + toggle manual persistido (localStorage). Sem flash de tema errado no load (theme aplicado antes do paint). [auto] recomendado (skill dark-mode-theming).
- **D-05:** Contraste AA (mínimo) nos dois temas; foco visível (shadow.focus); touch targets ≥44px no mobile. [auto] (accessibility-pro, REQ obrigatório).

### Componentes de estado (REQ-055)
- **D-06:** Componentes canônicos reutilizáveis: `EmptyState`, `ErrorState`, `LoadingSkeleton`, `WarnBanner` — presentes em TODAS as telas dali pra frente (detectados nos 26 wireframes). Copy em pt-BR (ux-copywriting-ptbr). [auto] travado (REQ-055).

### Tela de login (tela 01)
- **D-07:** Tela de login conecta ao `/v1/auth/login` (Phase 2): email + senha, estados de erro (credencial inválida com mensagem anti-enumeração — não dizer se email existe), loading no submit, suporte a TOTP quando exigido (campo de código aparece se o backend pedir). [auto] (wireframe 01 + RN-011 + ADR-005).
- **D-08:** Token de acesso em memória; refresh em cookie httpOnly (web). Guarda de rota redireciona não-autenticado para login. [auto] travado (ADR-005).

### Estrutura de superfícies
- **D-09:** Um app Angular com layouts/rotas por superfície: shell do entregador (mobile-first, Ionic tabs), shell da loja (web responsivo), shell admin (desktop-first). Nesta phase, só o esqueleto navegável + login; telas reais vêm nas phases seguintes. [auto] (ADR-003, "1 código 3 superfícies").

### Claude's Discretion
- Build step exato de tokens→CSS (script Node lendo tokens.json gerando `_tokens.scss`/CSS vars).
- Organização de pastas Angular (core/shared/features/layouts).
- Biblioteca de ícones (Ionicons já vem com Ionic).
- Skeleton component approach (Ionic skeleton vs custom).
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Identidade visual (canônica)
- `docs/identidade-visual/tokens.json` — tokens canônicos (escalas brand/neutral, semantic, delivery_state, score_level, tipografia, sombras, motion). FONTE da verdade visual.
- `docs/identidade-visual/brand.md` — voz, regra do Fraunces italic (1 palavra-chave/título), tom por contexto
- `design-system/MASTER.md` — catálogo de componentes extraído dos wireframes

### Decisões
- `.planning/DECISIONS.md` — ADR-003 (Angular/Ionic), DRV-004 (signals/OnPush/lazy), DRV-008 (tokens canônicos, zero hardcode), **DEC-001 (dark mode no M1)**

### Wireframes
- `projeto/wireframes/01-login.html` — contrato da tela de login
- (shell das 3 superfícies: referências em 04-home entregador, 11-loja-dashboard, 17-admin-dashboard — só esqueleto nesta phase)

### Backend a consumir (Phase 2)
- `apps/api/app/api/v1/` — endpoints `/v1/auth/login|refresh|logout` + envelope de erro RFC-7807-like

### Requisitos
- `.planning/REQUIREMENTS.md` — REQ-056 (tokens/voz), REQ-055 (componentes de estado), REQ-005 (login UI)
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Backend `/v1/auth/*` pronto (Phase 2) — login UI consome direto.
- `tokens.json` canônico — base do build de CSS vars.
- Monorepo `apps/` da Phase 1 — `apps/web` entra ao lado de `apps/api`.

### Established Patterns
- pt-BR na UI, código em inglês (DRV-005). Vocabulário do glossário em copy.
- Envelope de erro do backend: `{ error: { code, message, request_id } }` — o frontend exibe `message` (já anti-enumeração no backend).

### Integration Points
- Login → `/v1/auth/login`; guarda de rota + refresh. CORS/dev proxy do Angular para a API (porta 8000).
</code_context>

<specifics>
## Specific Ideas

- Estética anti-AI-slop (ui-ux-pro-max): editorial-técnica, persimmon queimado + cream warm, Fraunces italic com parcimônia (1 palavra-chave por título), JetBrains Mono para IDs/valores. Dark mode deve preservar o "warm" (sombras rgba(24,20,16,...), não cinza-azulado frio).
- Sem flash de tema no load (FOUC de tema é inaceitável).
</specifics>

<deferred>
## Deferred Ideas

- Telas de cadastro de loja (F-01) / entregador (F-02) — Phase 4/5.
- Dashboards de negócio, listas, mapas — phases respectivas.
- Mapa de tracking em tempo real (DEC-002) — Phase 9.
- Visual regression testing (touches_shared_components) — quando houver baseline de componentes compartilhados; nesta phase cria-se o baseline.
</deferred>

---

*Phase: 03-shell-frontend-design-system-3-superf-cies*
*Context gathered: 2026-06-10*
