# Integração — Safe2Pay (CRÍTICA)

**Fonte:** `projeto/docs-externos/integracoes.md:7-36` · ADR-009 v2 (`projeto/decisoes-existentes/adrs.md:48-53`) · Skill obrigatória: `domain/safe2pay-escrow-br` + `docs/SAAS-BILLING-DOCS.md` (CLAUDE.md §18)

> ⚠ **[DECIDIR] OQ-3 — bloqueia Phase 10:** confirmar na conta Safe2Pay contratada a disponibilidade de split/marketplace no plano, prazo de repasse de subconta e taxa por transação. Ajustar o escrow interno se o provedor já retiver.

## Usos
1. **Assinatura recorrente da loja** (cartão ou PIX recorrente)
2. **Cobrança por entrega** cartão/PIX com **split**: corrida → subconta do entregador (escrow interno 24h), taxa → conta Jaxegô (+ revenue share da área quando configurado)
3. **Fatura mensal de taxas** (pagamento direto + excedentes) — PIX/cartão/**boleto**
4. **Transferência de saque** para a chave PIX do MEI

## Contrato (simplificado)

```json
POST /v2/Payment
{
  "Amount": 10.50,
  "Reference": "dlv_01HXAQ3K9P",
  "Splits": [
    {"Recipient": "subconta_entregador", "Amount": 8.50},
    {"Recipient": "conta_jaxego", "Amount": 2.00}
  ],
  "Customer": { "...dados da loja..." }
}
```
Retorna: `IdTransaction`, status (`authorized|paid|refused`), QRCode PIX quando aplicável.

## Subcontas
Entregador elegível (MEI ativo — RN-010) cadastrado como recebedor com a conta do MEI; disparo na aprovação do MEI no KYC.

## Webhooks Safe2Pay → Jaxegô
Status de cobrança (paga, recusada, estornada, boleto compensado). Validar assinatura/token do header; **idempotente por `IdTransaction`** (tabela de eventos processados); responder 200 em <5s; trabalho pesado em fila arq.

## Comportamento em falha
- Recusa na criação da entrega → entrega **NÃO nasce** (F-03 E3); retry + opção de trocar para pagamento direto
- API fora do ar → circuit breaker; cartão/PIX indisponíveis com aviso; **pagamento direto continua**
- Cancelamento pré-aceite → estorno total automático; parcial conforme RN-004; excedente devolvido em até 5 dias úteis
- Conciliação diária extrato × registros; divergência > R$ 0,01 → alerta admin plataforma

## Decisão arquitetural
Camada de pagamento atrás de **interface própria** — trocar de PSP de novo não pode doer (já trocou Pagar.me → Safe2Pay).
