---
name: saas-billing-canonical
category: domain
description: Aponta para SAAS-BILLING-DOCS.md como referência canônica para qualquer trabalho de assinatura, plano, cobrança ou Safe2Pay. Não inventar lógica de billing.
---

# SaaS Billing Canonical — referência para assinaturas

> **Skill obrigatória para qualquer phase que toque em assinatura, plano, cobrança ou Safe2Pay.**

## Regra única

Quando a phase envolve:
- Assinaturas (criação, renovação, cancelamento)
- Planos (free, premium, enterprise)
- Cobrança (cards, PIX, boleto)
- Safe2Pay (gateway brasileiro)
- Billing cycles
- Trial periods
- Coupons / discounts

**SEMPRE consulte `docs/SAAS-BILLING-DOCS.md` antes de planejar ou executar.**

## Por que esta skill existe

Lógica de billing é uma das áreas onde "vibe coding" mais quebra projetos:
- Cálculos de proração errados
- Estados inválidos de assinatura (active mas expirada)
- Webhooks de gateway perdidos
- Dupla cobrança em race conditions
- Compliance fiscal brasileiro complexo (NF-e, ICMS, ISS)

`SAAS-BILLING-DOCS.md` é a fonte de verdade calibrada de projeto real (converzas) que resolveu esses problemas.

## O que fazer

1. **Antes de planejar:** abrir `docs/SAAS-BILLING-DOCS.md` e ler integralmente
2. **No PLAN.md:** citar esta skill em `## Skills Consultadas` com referência específica:
   ```markdown
   - `domain/saas-billing-canonical` — usado para [seção X de SAAS-BILLING-DOCS]
   ```
3. **No código:** seguir os padrões documentados literalmente, não improvisar
4. **Em decisões novas:** se SAAS-BILLING-DOCS não cobre o caso, **abrir ADR** documentando a decisão antes de codar

## O que NÃO fazer

❌ Improvisar fluxo de cobrança "que parece certo"
❌ Copiar lógica de billing de tutorial genérico do Stripe sem adaptar para Safe2Pay
❌ Pular validação fiscal brasileira (LGPD não cobre fiscal)
❌ Implementar trial sem considerar billing_cycle_anchor
❌ Webhook de gateway sem idempotência

## Onde está o documento

- Default: `docs/SAAS-BILLING-DOCS.md` (vem com o framework)
- Atualizado por: equipe de product/financeiro do projeto
- Não modificar localmente sem trazer de volta para o framework
