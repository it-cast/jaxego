# docs/identidade-visual/ — INDEX

> Atualizado pelo ingestor em 2026-06-10 com a identidade real do Jaxegô (origem: `projeto/identidade-visual/`).

## Canônicos

- `tokens.json` — **fonte de verdade visual** (v2-jaxego, 2026-04-25). Persimmon queimado `#E84E1B` (brand-500) + cream warm `#FAF6EE` + carvão amarronzado `#181410`. Inclui paletas semânticas, **cores por estado de entrega** (criada/aceita/coletada/entregue/recusada/cancelada/finalizada) e **cores por nível de score** (probation→diamante). Gate 2 (Visual Contract) valida contra este arquivo.
- `brand.md` — voz, regra do italic (Fraunces em 1 palavra-chave por título, NUNCA em botões/labels/erros), tom por contexto, vocabulário, formatos de número/data/CPF, gramática (sentence case, CTA ≤4 palavras).
- `design-system.md` — template do framework (ver `design-system/MASTER.md` na raiz para o consolidado gerado pelo ingestor).

## Subpastas

- `wireframes/`, `mockups/` — vazias; os 26 wireframes HTML canônicos vivem em `projeto/wireframes/` (contrato verificável v0.9.7 — não duplicar).

## Regra de uso

Nada de cor/fonte/espaçamento hardcoded: SCSS consome CSS vars geradas de `tokens.json` (`projeto/stacks/stack.md:26`). Fontes: Inter Tight (tudo), Fraunces italic (acento), JetBrains Mono (dados/IDs/valores).
