# decisoes-existentes/

**Decisões já tomadas, restrições, ADRs prévios.**

## O que jogar aqui

- ADRs (Architecture Decision Records) já feitas
- Restrições impostas por cliente / regulador / time
- Decisões de tecnologia já fechadas
- Compromissos contratuais
- Coisas que NÃO podem mudar

## Formatos aceitos

`.md`, `.txt`, `.pdf`

## Exemplos

```
adr-001-mysql-nao-postgres.md
adr-002-locale-ptbr-only.md
restricoes-juridicas.txt
contrato-cliente-prazo.pdf
restricoes-lgpd.md
nao-usar-aws.md             # "cliente exige VPS dedicado, não cloud premium"
```

## Por que isso importa

Quando Claude planeja phases, ele não vai sugerir "migrar para Postgres" se há um ADR aqui dizendo "MySQL obrigatório". Não vai propor "deploy AWS" se há restrição contratual.

Tudo aqui vira **invariantes** no `DECISIONS.md` gerado. Não negociáveis sem novo ADR formal.

## Formato sugerido

```md
# ADR-XXX: Título curto

**Data:** YYYY-MM-DD
**Status:** Aceito (não negociável)

## Contexto
Por que essa decisão foi tomada.

## Decisão
O que foi decidido.

## Consequências
- Positiva: ...
- Negativa: ...

## Não pode mudar sem
- Aprovação de [stakeholder]
- Novo ADR formal
```

Não precisa estar nesse formato exato — qualquer texto que descreva a decisão funciona. Claude estrutura no `DECISIONS.md`.

## O que NÃO jogar aqui

- Decisões em ABERTO (vai virar discovery question no `/gsd:ingest`)
- Sugestões / preferências negociáveis (vai em `regras-negocio/` ou similar)
