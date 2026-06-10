# Design System — Jaxegô (MASTER)

> Gerado por `gsd-project-ingestor` em 2026-06-10 consolidando `projeto/identidade-visual/tokens.json` (v2-jaxego — **canônico**, não sugestão), `brand.md` e a análise estrutural dos 26 wireframes HTML.
> Identidade: **editorial-técnica** — informação manda, com calor tipográfico. Anti-referências: laranja neon do Rappi, saturação da 99.

---

## 1. Fundamentos (de tokens.json — valores travados)

### Cor

| Papel | Token | Valor |
|---|---|---|
| Brand primário | `color.brand.500` | `#E84E1B` (Persimmon queimado) |
| Brand hover/escuro | `color.brand.600/700` | `#C73E0F` / `#A0300A` |
| Brand wash (fundos de destaque) | `color.brand.50/100` | `#FFF1E8` / `#FFDEC1` |
| Papel (background app) | `color.neutral.50` | `#FAF6EE` (cream warm) |
| Superfície de card | `#fff` + borda `neutral.200` | `#E5DBCC` |
| Texto | `color.neutral.800` | `#181410` (carvão amarronzado) |
| Texto secundário | `color.neutral.500` | `#6B5F50` |
| Success / Warning / Error / Info | semantic | `#1B998B` / `#E89B0E` / `#C71D1D` / `#0A66C2` (+ `_bg` pastel cada) |

**Cores por estado de entrega** (estado = cor única, lição do Linear): criada `#6B5F50` · aceita `#0A66C2` · coletada `#E89B0E` · entregue `#1B998B` · recusada_no_destino `#E84E1B` · cancelada `#9D8E7A` · finalizada `#0F6E62`.

**Cores por nível de score:** probation `#9D8E7A` · bronze `#A66D2F` · prata `#7E7B73` · ouro `#D4A017` · diamante `#1B998B`.

### Tipografia — a regra do italic

- **Inter Tight** — display, body, UI (tudo)
- **Fraunces italic** — UMA palavra-chave por título/hero, na cor brand ("Chegou *rapidinho*"). NUNCA em botões, labels, tabelas, erros, dados
- **JetBrains Mono** — TODO dado: valores R$, IDs, timestamps, métricas, placas, scores

Escala: 11/12/13/**14 (base)**/16/18/22/28/36/48/72px · pesos 400–800 · letter-spacing negativo (-.02em) em headings.

### Espaçamento, raio, sombra, motion

- Spacing: 4/8/12/16/24/32/48/64/96px
- Radius: sm 4 · md 6 · lg 10 (cards) · xl 16 · full 9999 (pills/toggles)
- Sombras **warm** `rgba(24,20,16,…)` (sm/md/lg) + focus ring `0 0 0 3px rgba(232,78,27,.28)`
- Motion: fast 140ms · normal 220ms · slow 380ms · easing `cubic-bezier(0.16,1,0.3,1)`

### Implementação

SCSS consome CSS vars **geradas de tokens.json** (build step). Nada de cor hardcoded — Gate 2 (Visual Contract) valida tokens citados em UI-SPEC contra tokens.json.

---

## 2. Detectado dos wireframes (26 telas HTML — DOM analisado)

### Padrões estruturais por superfície

| Superfície | Layout | Telas |
|---|---|---|
| App entregador | mobile 420px max, tabbar fixa inferior (Início/Entregas/Ganhos/Perfil), cards empilhados | 03–10 |
| Painel loja | web centrado 620–860px, fieldsets com legend uppercase | 02, 11–16 |
| Admin área/plataforma | desktop-first, tabelas densas (referência Stripe), mono em valores | 17–25 |
| Tracking público | mobile 480px, sem chrome de app, timeline vertical | 26 |

### Componentes recorrentes (catálogo candidato)

- **Card** — fundo `#fff`, borda `#E5DBCC` 1px, radius 10px, padding 14–16px
- **Toggle online/offline** — pill (radius full) com fundo `success_bg`/`neutral.100`
- **Money display** — JetBrains Mono, 26–32px, weight 800, letter-spacing -.02em; ganhos em `success` com prefixo `+`
- **Label de seção** — 10–12px uppercase, letter-spacing .06–.1em, `neutral.500`, weight 600
- **Oferta (bottom sheet)** — fundo escuro `#181410` atrás, sheet cream radius 20px topo, cronômetro mono `aria-live=polite`, pins A/B, CTA primário cheio + recusa ghost
- **Pay selector** — grid 3 colunas de radio-cards; selecionado = borda brand + wash `#FFF1E8`
- **Estimate box** — wash brand `#FFF1E8` borda `#FFDEC1`, `role=status`
- **Timeline de estados** — `ol` com bullets coloridos (done `success`, current `brand`), timestamps mono
- **Badge de pagamento direto** — `#FFF8C2`/`#8B5A05` "PAGAMENTO DIRETO 💵"
- **Status de fatura** — texto colorido weight 700: PAGA `success`, vencida `error`, aberta `#8B5A05`
- **Plan card** — grid 4 colunas, atual com borda brand + flag "SEU PLANO"
- **GPS feedback** — chip `gps-ok` (success_bg) / `gps-bad` (error_bg) com `role=status/alert`
- **Camera input** — área dashed `#C8BAA5` com instrução de enquadramento

### Estados obrigatórios (contrato — REQ-055)

Detectados no DOM de todas as telas: `empty-state` (com causa + ação), `error-state` (`role=alert`, o que houve + o que fazer), `loading skeleton` (animação pulse 1.2s), `warn` (avisos não-bloqueantes). **Toda tela implementada deve cobrir os estados do wireframe correspondente** (`gsd-tools wireframe-contract`).

### Acessibilidade já presente nos wireframes (manter)

`lang="pt-BR"`, `aria-labelledby` em seções, `role=alert/status`, `aria-live=polite` no cronômetro, `aria-current=page` na tabbar, inputs com label explícito, `inputmode`/`capture` adequados.

---

## 3. Voz e copy (de brand.md — resumo operacional)

- Sentence case sempre; CTA verbo+objeto ≤4 palavras, sem ponto final ("Chamar entregador")
- Confirmação = fato sem festa; erro = o que houve + o que fazer; nunca "Algo deu errado"
- Score: delta + causa, sem moralismo; suspensão: motivo verificável + prazo de recurso
- Formatos: R$ 1.234,56 · 2,5 km · 87,4 (score 1 decimal) · 25/04/2026 / "hoje, 14:30" · CPF mascarado "123.***.***-09"
- Vocabulário: glossário canônico (`docs/glossario.md`) — "corrida" no app do entregador, "frete" na UI da loja

## 4. Gaps declarados

- Logo: não há arquivo de logo em `projeto/identidade-visual/` — apenas a assinatura tipográfica ("Jaxegô. Chegou *rapidinho*."). **[GAP]** confirmar se existe logo gráfico ou se a marca é 100% tipográfica.
- Dark mode: tokens não definem paleta dark. Wireframes são light-only. **[GAP]** decidir se M1 suporta dark mode (CLAUDE.md ativa skill dark-mode-theming apenas "se suporta").
- Ícones: wireframes usam emoji (🛵, 📍, 💵). **[INFERRED]** produção deve substituir por iconografia consistente (Ionicons já vem com Ionic 8) — exceto onde emoji é intencional na copy do destinatário.
