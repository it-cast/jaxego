---
name: competitive-analysis
category: meta
description: Análise estruturada de competidores diretos e indiretos com dimensões consistentes. Sai melhor que "olha o concorrente" ad-hoc.
---

# Competitive Analysis — Análise Competitiva

> Não é "lista de concorrentes". É matriz comparativa que orienta decisão.

## Quando esta skill é obrigatória

- `/gsd-bootstrap` em projeto novo (uma vez)
- `/gsd-discuss-phase` quando phase implementa feature já existente em concorrentes
- Antes de pricing decisions
- Antes de positioning ou redesign de homepage

## Tipos de competidor

| Tipo | Definição | Exemplo (Áugure) |
|---|---|---|
| **Direto** | Mesma categoria, mesmo job | Plataformas de simulação de mercado para empreendedores |
| **Indireto** | Categoria diferente, mesmo job | Mentoria de negócio, consultoria, livros de empreendedorismo |
| **Substituto** | Resolve job sem usar produto | Conversas com mentor, planilhas Excel, gut feeling |
| **Aspiracional** | Líder fora da sua categoria mas com UX que inspira | Linear, Notion, Stripe (não compete, mas referência) |

## Processo

### 1. Listar 5-10 competidores nas 4 categorias

Mínimo: 3 diretos, 2 indiretos, 2 substitutos, 1 aspiracional.

### 2. Definir dimensões de comparação

Escolher 5-8 dimensões relevantes para SEU produto. Exemplos:

**SaaS B2B:**
- Pricing model (free tier, trial, plans)
- Time to first value (minutos até primeiro insight)
- Onboarding type (autônomo, white-glove)
- Integrações principais
- Compliance (SOC2, LGPD, GDPR)
- API/extensibilidade
- Suporte (chat, email, fone)
- Tom de comunicação

**App B2C:**
- Custo (free, freemium, paid)
- Plataformas (iOS, Android, web)
- Tempo até primeira ação core
- Permissões pedidas
- Features principais (top 5)
- App store rating
- Estilo visual

### 3. Preencher matriz (não opinar, observar)

```markdown
| Dimensão | Concorrente A | Concorrente B | Substituto C | Áugure |
|---|---|---|---|---|
| Tempo até primeiro relatório | 2 dias (manual) | 30 min (template) | semanas (consultor) | 15 min |
| Custo entrada | R$ 500/mês | R$ 200/mês | R$ 5000+ | R$ 99/mês |
| Foco brasileiro | Não | Não | Sim | Sim |
| Compliance LGPD | Vago | Não | N/A | Sim, documentado |
```

### 4. Identificar 3-5 gaps de mercado

Onde TODOS os concorrentes são fracos? Aí está sua oportunidade.

```
Gap 1: nenhum tem foco brasileiro real (todos genéricos)
Gap 2: time-to-value é dias/semanas em todos os diretos
Gap 3: custo R$ 500+ exclui PME pequena
```

### 5. Definir posicionamento

```
Áugure é o único [SaaS de simulação de mercado]
para [empresários PME brasileiros]
que [valida ideia em 15 minutos com calibração pública e foco em LGPD],
diferente de [Bizplan e Liveplan que são genéricos americanos] e
[consultoria tradicional que é cara e demorada].
```

## Anti-patterns

❌ Competitor analysis só com diretos (esquece substitutos, que muitas vezes são o real concorrente)
❌ Dimensões opinativas ("UX boa") — usar dimensões observáveis
❌ Analysis sem gap → sem ação. Sempre extrair 3 gaps no final
❌ "Eles são piores que nós em tudo" → você não está olhando direito

## Integração

- Antes: `meta/user-persona`, `meta/jobs-to-be-done`
- Depois: `meta/north-star-vision`, `meta/opportunity-framework`
