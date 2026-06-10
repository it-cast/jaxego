# ADRs — Architecture Decision Records

> Decisões arquiteturais de longo prazo. Toda mudança de stack, protocolo, estrutura de dados cross-cutting, ou regra invariante passa por ADR.
> Diferente de `.planning/DECISIONS.md`: ADRs são de **longo prazo** e ficam no repo mesmo se o planning for resetado.

## Quando criar ADR

- Mudança de stack (framework, linguagem, banco)
- Mudança de protocolo (REST → GraphQL, HTTP → WebSocket)
- Escolha de biblioteca que impacta o design (ORM, state manager)
- Regra de negócio que vai afetar múltiplas fases (ex: "usuário pode editar proposta até aceite")
- Desvio dos defaults do framework (override de gate)

## Formato

Ver `ADR-template.md`. Cada ADR tem:
- Status: proposed | accepted | deprecated | superseded
- Context: o problema sendo resolvido
- Decision: a escolha feita
- Consequences: o que muda

## Nomenclatura

`ADR-NNN-kebab-case-short-title.md` — NNN começa em 001, sequencial.

## Lifecycle

1. Proposta (`status: proposed`) — discussão via PR
2. Aceita (`status: accepted`) — merge no main, nenhuma edição de conteúdo depois, apenas append de consequências
3. Se substituída: marcar `status: superseded by ADR-NNN` e criar ADR nova

ADRs são imutáveis após aceite. Para "mudar", cria-se nova ADR e marca a antiga como superseded.
