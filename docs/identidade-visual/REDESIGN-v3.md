# Projeto de UX/UI — Redesign v3 "Já chegô, sem stress"

> **Status:** canônico a partir de 2026-10-12 (ADR-015). Substitui a direção visual v2 ("persimmon + cream + carvão marrom").
> **Fonte de verdade dos valores:** `tokens.json` (v3-jaxego). Este documento explica o **porquê** de cada valor e as regras de uso.
> **Escopo:** as 3 superfícies (loja web, admins web, app do entregador) + páginas públicas (login, cadastro, tracking) + **todas as áreas de mapa**.

---

## 1. Diagnóstico do layout v2

| Problema | Onde | Efeito no usuário |
|---|---|---|
| Paleta "terrosa" (marrom-carvão + creme + laranja queimado) | toda a UI | sensação pesada, "antiga"; o laranja não respirava — tudo parecia da mesma família tonal |
| `--surface-elevated` **mais escuro** que `--surface` no tema claro | cards, sidebars | cartões pareciam "afundados", sem hierarquia de profundidade |
| 4 shells web quase idênticos (loja, admin, equipe, plataforma), cada um com CSS próprio e fallbacks hex | `apps/web/src/layouts/*` | inconsistência visual entre perfis; dark mode quebrado nos fallbacks (`#fff`) |
| Variáveis usadas e nunca definidas (`--bg-hover`, `--success-wash`, `--error-wash`, `--text-primary`…) | ~40 telas | estados de hover/badge caíam no fallback hardcoded, ignorando o tema |
| Mapas com tiles OSM crus, marcador azul padrão do Leaflet (carregado do unpkg), polígonos `#e8722a` fixos, altura fixa e sem legenda | live-map, area-map, zona-map | mapa destoava do produto, não comunicava estado, dark mode só no live-map |
| Login com imagem estática e logo `#DB6420` hardcoded | `login.page` | primeira impressão fria, sem a promessa da marca |

## 2. Quem usa e o que precisa **sentir**

| Persona | Contexto real | Emoção-alvo | Tradução visual |
|---|---|---|---|
| **Loja** (dono de pizzaria, sexta 20h) | pico, pressa, celular ou balcão | *alívio e controle* — "resolvi em 1 clique" | CTA laranja dominante, status coloridos legíveis de longe, cards limpos |
| **Entregador** (capacete na mão, sol, 4G) | ao ar livre, uma mão, telas curtas | *motivação e justiça* — "sei quanto ganho, sei por quê" | contraste alto, números grandes em mono, verde para ganhos, tab bar flutuante com alvos ≥ 48px |
| **Admin de área / equipe** (gestor local) | desktop, rotina, muitas linhas | *confiança e calma* — "a operação está sob controle" | sidebar em azul-noite (estável), densidade Stripe, mapas de zona claros |
| **Plataforma** | auditoria, decisões | *seriedade* | mesma base, sem decoração extra |
| **Destinatário** (sem login) | link no WhatsApp | *tranquilidade* — "está chegando" | tracking com mapa vivo, pin pulsando, etapa atual destacada |

## 3. Psicologia das cores aplicada

A paleta v3 é um **sistema de 3 papéis** — energia, confiança e conquista — mais neutros frios que deixam essas três cores "acenderem".

| Papel | Cor | Hex (500) | Psicologia | Onde usar | Onde NÃO usar |
|---|---|---|---|---|---|
| **Energia / ação** | Tangerina "Já-chegô" | `#F26B1D` (fill `--brand` = 600 `#CC4A08`) | laranja = velocidade, apetite, entusiasmo, cordialidade; é a cor do "chamar entregador". Mais luminosa e solar que o persimmon v2, sem cair no neon do Rappi | CTA primário, item ativo de navegação, pin de destino, zona ativa no mapa, palavra em Fraunces italic | fundos grandes, texto de erro, tabelas |
| **Confiança / estabilidade** | Azul-noite (neutros "ink") | `#0F1426`–`#4A5270` | azul profundo = segurança, competência, dinheiro bem cuidado. Equilibra a energia do laranja e tira o ar "improvisado" | sidebar, tipografia, header do tracking, mapas no escuro, rotas | — |
| **Conquista / dinheiro** | Esmeralda | `#0B8A5F` | verde = ganho, "deu certo", seguir em frente | saldo, entregue/finalizada, toggle online, confirmações | alertas |
| Atenção | Âmbar | `#F59E0B` | alerta amigável sem pânico | coletada, pendências, prazos | — |
| Erro | Coral-vermelho | `#D0353B` | urgência **suave** — vermelho mais quente/menos agressivo reduz ansiedade em falhas de pagamento | erros, ações destrutivas | estados neutros |
| Informação | Azul royal | `#2F62E6` | clareza, novidade | aceita, dicas, links informativos | CTA |
| Destaque | Amarelo-sol | `#FFC83D` | otimismo pontual | pagamento direto, "novo", conquistas de score | blocos de texto |

**Regra 60-30-10:** 60% neutros frios (fundo `#F6F7FB` + cartões brancos), 30% azul-noite (texto, sidebar), 10% tangerina (ação). O verde/âmbar/coral aparecem só como **significado**, nunca como decoração.

### Contraste (WCAG 2.1 AA)

| Par | Contraste | Uso permitido |
|---|---|---|
| texto `#1A2038` sobre branco | 16:1 | tudo |
| texto-muted `#5F6884` sobre branco / fundo | 5,5:1 / 5,2:1 | texto secundário |
| branco sobre `--brand` `#CC4A08` | 4,6:1 | botões primários (texto ≥ 14px) |
| branco sobre sidebar `#0F1426` | 18:1 | navegação |
| `--text-subtle` `#9AA2B8` | 2,6:1 | **somente** decorativo/placeholder (mesma regra da v2) |
| dark: texto `#F6F7FB` sobre `#0A0E1C` | 18:1 | tudo |
| dark: `--brand` `#FF8840` com texto `#0F1426` | 7,7:1 | botões no escuro |
| erro `#D0353B` / info `#2F62E6` sobre branco | 4,9:1 / 5,2:1 | texto de erro e links informativos |
| dark: sucesso/erro/info/alerta usam variantes claras (`semantic_dark`) | ≥ 7:1 | badges e mensagens no escuro |

## 4. Tipografia (mantida — é assinatura da marca)

Inter Tight (UI) + **Fraunces italic em 1 palavra-chave por título** + JetBrains Mono (dados). A v3 muda só o *uso*: títulos de página ganham peso 700 e `letter-spacing: -0.025em`; números de destaque (saldo, ETA, KPIs) usam `--jx-text-3xl`/`4xl` em mono.

## 5. Forma, profundidade e movimento

| Token | v2 | v3 | Por quê |
|---|---|---|---|
| radius sm/md/lg/xl | 4/6/10/16 | **6/10/14/20** (+ `2xl` 28) | cantos mais arredondados = mais amigável/acessível, padrão de apps de consumo (iFood, Nubank) |
| sombras | marrom `rgba(24,20,16)` | **azul-noite** `rgba(15,20,38)` mais difusas + `glow` laranja para o CTA | profundidade limpa e moderna; o CTA "brilha" e atrai o olhar |
| superfícies | elevated mais escuro que o fundo | **fundo `#F6F7FB`, cartão branco**, sunken `#EDEFF5` | hierarquia de profundidade correta |
| motion | 140/220/380ms | igual + `--jx-motion-spring` | entrada de página (fade + 6px), hover com lift de 1px, pin pulsando; tudo desligado em `prefers-reduced-motion` |

## 6. Layout — arquitetura das superfícies

### 6.1 Shell web unificado (`jx-app-shell`, packages/shared)

Um único componente serve **loja, admin de área, equipe e plataforma** (cada shell vira um wrapper fino que só passa a navegação):

```
┌───────────────┬──────────────────────────────────────────────┐
│ [J] Jaxegô    │  (conteúdo — max 1280px, padding 32px)       │
│  LOJA         │                                              │
│ ┌───────────┐ │                                              │
│ │ Pizzaria X│ │  ← cartão de contexto (loja/área)            │
│ └───────────┘ │                                              │
│ ● Painel      │  ← ativo: pílula tangerina + barra de luz    │
│ ○ Entregas    │                                              │
│ ○ Favoritos   │                                              │
│ …             │                                              │
│               │                                              │
│ ☀/☾ Tema      │                                              │
│ ⎋ Sair        │                                              │
└───────────────┴──────────────────────────────────────────────┘
 sidebar azul-noite 264px · recolhível p/ 76px (desktop) · drawer (< 960px)
```

- Sidebar **sempre azul-noite** (nos dois temas): ancora a navegação, dá sensação de produto profissional e faz o conteúdo claro "saltar".
- Mobile (< 960px): topbar translúcida com blur + drawer com overlay; foco gerenciado, `Esc` fecha.
- Toggle de tema disponível em todos os perfis (antes só admin/plataforma).
- Conteúdo entra com animação curta (`jx-page-enter`).

### 6.2 App do entregador (`jx-entregador-shell`)

- **Tab bar flutuante** (pílula elevada, margem 12px, blur) com indicador ativo tangerina; alvos de 56px; respeita `safe-area-inset-bottom`.
- Conteúdo com respiro inferior para não ficar sob a tab bar.

### 6.3 Páginas públicas

- **Login:** split 50/50 — formulário à esquerda, **painel de marca** à direita em gradiente azul-noite → tangerina com um *mini-mapa ilustrado* (rota tracejada animada entre loja e destino) e 3 provas de valor. No mobile o painel vira um cabeçalho compacto.
- **Tracking público:** cabeçalho azul-noite com marca, mapa **grande** (hero) com pin pulsante do entregador, cartão de status sobreposto e timeline abaixo.

## 7. Mapas — especificação (todas as áreas)

| Área | Componente | Tela(s) | v3 |
|---|---|---|---|
| Posição pontual (destino / entregador) | `jx-live-map` (shared) | detalhe da entrega (loja), tracking público | pin SVG da marca (sem imagem do unpkg), anel pulsante, chip de legenda sobreposto, controles restilizados, botão "centralizar", tema claro/escuro |
| Desenho/edição de zonas | `jx-area-map` (web) | admin › Zonas | paleta de zonas derivada dos tokens (8 cores harmônicas), zonas existentes em cinza-tracejado, ativa com stroke 3px + fill 18%, toolbar do leaflet-draw restilizada, altura responsiva, legenda |
| Zona de cobertura (entregador) | `jx-zona-map` (app) | Zonas › mapa | polígono tangerina com fill suave, tiles com tema, controles grandes para toque |

### 7.1 Kit de mapa compartilhado (`@jaxego/core/map`)

- `map-tiles.ts` — fonte de tiles **única** (TD-019 mantida): OSM no piloto, pronta para MapTiler/self-host.
- `map-theme.ts` — lê cores **dos tokens CSS em runtime** (`getComputedStyle`) para polígonos, rotas e pins: nenhum hex em componente; muda junto com o tema.
- `leaflet-loader.ts` — carregamento único e lazy do Leaflet/leaflet-draw (antes duplicado em 2 componentes).
- `_map.scss` (global) — restyle de zoom, atribuição, popups, toolbar de desenho; filtro de tiles por tema:
  - claro: `saturate(.85) contrast(1.02)` — mapa mais "limpo" para o laranja se destacar;
  - escuro: `invert(1) hue-rotate(200deg) brightness(.92) contrast(.88) saturate(.6)` — mapa noturno azulado.

### 7.2 Semântica de cor no mapa

| Elemento | Cor | Motivo |
|---|---|---|
| Destino / zona ativa | tangerina | é "o que importa agora" |
| Entregador | azul-noite com anel tangerina pulsante | movimento, presença viva |
| Zonas existentes (referência) | cinza neutro tracejado | contexto sem competir |
| Zonas em edição | paleta categórica `--map-zone-1..8` | distinguir sem significado de status |

## 8. Componentes globais adicionados

- Aliases para variáveis órfãs (`--bg-hover`, `--success-wash`, `--error-wash`, `--warning-wash`, `--text-primary`, `--bg-subtle`, `--jx-radius-2xl`, `--jx-font-serif`, `--jx-color-*`…) → ~40 telas passam a respeitar o tema sem tocar uma linha delas.
- Scrollbar fina temática, `::selection` tangerina, `jx-page-enter`.

## 9. Acessibilidade (não-negociável)

- Foco visível em tudo (`--focus-ring` tangerina 35%).
- Alvos ≥ 44px (web) / ≥ 48px (app).
- Nenhuma informação só por cor: status sempre com rótulo; mapa tem `aria-label` e legenda textual.
- `prefers-reduced-motion`: sem pulso, sem entrada animada, sem rota animada.
- Dark mode completo (DEC-001), incluindo mapas.

## 10. Plano de aplicação (executado nesta entrega)

1. `tokens.json` v3 → `npm run tokens:build`.
2. `_semantic.scss`: nova camada semântica + aliases + tokens de navegação, mapa e gradiente.
3. `global.scss` + `_map.scss`: base moderna e kit visual de mapa.
4. `jx-app-shell` compartilhado; 4 shells web viram wrappers; shell do entregador com tab bar flutuante.
5. Mapas: `jx-live-map`, `jx-area-map`, `jx-zona-map`, tracking público, card de mapa do detalhe da entrega.
6. Login com painel de marca animado.
7. Verificação: lint, testes, builds, zero-hex, screenshots claro/escuro.
