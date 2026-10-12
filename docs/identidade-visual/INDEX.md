# docs/identidade-visual/ — INDEX

> Atualizado pelo ingestor em 2026-06-10 com a identidade real do Jaxegô (origem: `projeto/identidade-visual/`).

## Canônicos

- `tokens.json` — **fonte de verdade visual** (v3-jaxego, 2026-10-12 — ADR-015). Tangerina `#F26B1D` (brand-500; fill de botão `--brand` = brand-600 `#CC4A08`) + azul-noite (neutros frios `#F6F7FB`→`#0A0E1C`) + esmeralda `#0B8A5F` para dinheiro/sucesso; `semantic_dark` (variantes AA no escuro) e `map.zone_1..8` (paleta categórica de mapas). Inclui paletas semânticas, **cores por estado de entrega** (criada/aceita/coletada/entregue/recusada/cancelada/finalizada) e **cores por nível de score** (probation→diamante). Gate 2 (Visual Contract) valida contra este arquivo.
- `REDESIGN-v3.md` — **projeto de UX/UI do redesign v3** (canônico): diagnóstico da v2, personas × emoção-alvo, psicologia das cores (60-30-10), tabela de contraste AA, layout das superfícies (shell unificado, tab bar flutuante, login, tracking) e especificação de **todas as áreas de mapa**.
- `brand.md` — voz, regra do italic (Fraunces em 1 palavra-chave por título, NUNCA em botões/labels/erros), tom por contexto, vocabulário, formatos de número/data/CPF, gramática (sentence case, CTA ≤4 palavras).
- `design-system.md` — template do framework (ver `design-system/MASTER.md` na raiz para o consolidado gerado pelo ingestor).

## Subpastas

- `wireframes/`, `mockups/` — vazias; os 26 wireframes HTML canônicos vivem em `projeto/wireframes/` (contrato verificável v0.9.7 — não duplicar).

## Regra de uso

Nada de cor/fonte/espaçamento hardcoded: SCSS consome CSS vars geradas de `tokens.json` (`projeto/stacks/stack.md:26`). Fontes: Inter Tight (tudo), Fraunces italic (acento), JetBrains Mono (dados/IDs/valores).
