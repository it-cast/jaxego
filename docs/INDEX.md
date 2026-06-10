# docs/ — INDEX

> Índice principal de documentação. Claude lê este arquivo primeiro ao contextualizar.
> Atualizado por `gsd-project-ingestor` em 2026-06-10.

## Arquivos nesta pasta

### Canônicos (lidos no bootstrap)

- `project-brief.md` — **fonte de verdade**: identidade, problema, modelo de negócio, KPIs, escopo M1, fora de escopo. Atualizado: 2026-06-10
- `glossario.md` — vocabulário canônico obrigatório em UI/copy (entregador, corrida vs frete, pagamento direto…). Atualizado: 2026-06-10
- `INDEX.md` — este arquivo

### Do framework (referência)

- `SAAS-BILLING-DOCS.md` — padrão canônico de billing/Safe2Pay (lei para phases 10–11)
- `SKILLS-USAGE-MANUAL.md` — quais skills consultar por momento do fluxo
- `PLATFORM-NOTES.md` / `KNOWN-LIMITS.md` — notas de plataforma e limitações do framework

## Subpastas temáticas

| Pasta | Conteúdo | Relevância |
|---|---|---|
| `regras-negocio/` | Visão, 27 entidades, fluxos F-01..F-08, regras RN-001..RN-030 | **canônico** |
| `personas/` | 6 personas (loja dono/operador, entregador, admins, destinatário) | **canônico** |
| `integracoes/` | Safe2Pay (CRÍTICA, [DECIDIR] pendente), Menu Certo (CRÍTICA), serviços de suporte | **canônico** |
| `identidade-visual/` | `tokens.json` (fonte de verdade visual) + `brand.md` (voz/copy) | **canônico** |
| `adrs/` | ADRs novas do projeto (as 17 pré-existentes estão em `.planning/DECISIONS.md`) | alta |

## Fontes originais

`projeto/` é o material bruto de entrada (nunca deletar): regras-negocio, decisoes-existentes, stacks, docs-externos, identidade-visual, **wireframes/ (26 telas HTML — contrato verificável de UI, não duplicadas aqui)**, referencias.

## Pendências de decisão humana

Ver `DISCOVERY-REPORT.md` na raiz: 3 Open Questions críticas `[DECIDIR]` + 14 suposições `[ASSUMIDO]`.
