# ADR-015: Redesign visual v3 — paleta "tangerina + azul-noite", shell unificado e kit de mapa

- **Status:** accepted
- **Data:** 2026-10-12
- **Autor:** Claude Code (a pedido do dono do produto)
- **Deciders:** dono do produto (Grupo Itcast)

## Contexto

O dono pediu a reestruturação completa do layout: "atraente, dinâmico, moderno, usando psicologia das cores para que as pessoas queiram usar o sistema", incluindo **todas as áreas de mapa**. A direção v2 (persimmon `#E84E1B` + cream `#FAF6EE` + carvão marrom `#181410`, DRV-008) era coerente mas pesada/terrosa; tinha `--surface-elevated` mais escuro que o fundo (cartões "afundados"), 4 shells web duplicados com fallbacks hex que quebravam o dark mode, ~40 telas usando variáveis nunca definidas, e mapas com tiles crus, marcador padrão do Leaflet servido pelo unpkg e cores de polígono hardcoded.

O projeto de UX/UI completo (diagnóstico, personas × emoção-alvo, psicologia das cores, contraste, layout, especificação de mapas) está em `docs/identidade-visual/REDESIGN-v3.md`.

## Decisão

Adotar a **identidade visual v3** (`tokens.json` v3-jaxego), que supera DRV-008:

1. **Paleta de 3 papéis:** tangerina (energia/ação, 10%) + azul-noite como base fria de neutros e navegação (confiança, 30%) + esmeralda (conquista/dinheiro). Verde/âmbar/coral só carregam significado. Fundo `#F6F7FB` com cartões brancos; dark mode em azul-noite profundo com variantes semânticas clareadas (`semantic_dark`) para AA.
2. **Forma e profundidade:** raios maiores (6/10/14/20/28), sombras azul-noite difusas, `glow` tangerina no CTA, motion de entrada de página e pins pulsantes (tudo desligado em `prefers-reduced-motion`).
3. **Shell web único** `jx-app-shell` (packages/shared) com sidebar azul-noite em ambos os temas; os shells de loja/admin/equipe/plataforma viram wrappers. App do entregador ganha tab bar flutuante.
4. **Kit de mapa compartilhado** (`@jaxego/core/map`: loader único do Leaflet via npm, tema por tokens CSS lidos em runtime, pins SVG da marca, `_map.scss` global) aplicado a: detalhe da entrega, tracking público, editor de zonas (+ nova visão geral de cobertura), zonas do entregador (+ nova visão geral) e **novo mapa de rota na entrega ativa** do entregador (respeitando RN-013).
5. Tipografia (Inter Tight + Fraunces italic em 1 palavra + JetBrains Mono) e voz (`brand.md`) **mantidas**.

## Alternativas consideradas

### Opção A — Só ajustar a v2 (clarear o fundo, corrigir variáveis)
- Prós: diff pequeno.
- Contras: não atende ao pedido de redesenho; mantém a sensação terrosa e os mapas crus.

### Opção B — Trocar a cor da marca (ex.: roxo/verde)
- Prós: ruptura visual forte.
- Contras: perde o laranja, que é a cor certa para delivery (velocidade, apetite) e já é reconhecida pelos usuários do piloto.

### Opção C — v3: manter o laranja, trocar a base para azul-noite frio (escolhida)
- Prós: o laranja "acende" sobre neutros frios; azul-noite comunica confiança (dinheiro, comprovação); AA verificado; tudo via tokens, propaga para ~80 telas sem tocar cada uma.
- Contras: diff grande em estilos; screenshots de regressão visual precisam de nova baseline.
- **Escolhida porque:** maximiza o efeito percebido com o menor risco funcional (só camada de apresentação).

## Consequências

### Positivas
- Hierarquia de profundidade correta, dark mode consistente (aliases + tokenização de ~60 hex fixos em .scss/.ts).
- Uma fonte para a navegação web; um loader e um tema para todos os mapas.
- Três novas áreas de mapa úteis: visão geral de zonas (admin), visão geral de cobertura (entregador), rota da entrega ativa.

### Negativas
- `leaflet-draw` continua vindo do unpkg sob demanda (não há pacote no monorepo) — ver TD-V3-01.
- Baseline de regressão visual (`apps/web/scripts/visual-baseline.mjs`) precisa ser regenerada.

### Neutras / requer atenção
- Tiles seguem OSM (TD-019); o visual por tema é feito com filtro CSS, independente do provider.
- `--text-subtle` continua decorativo (2,6:1) — não usar em texto informativo.
