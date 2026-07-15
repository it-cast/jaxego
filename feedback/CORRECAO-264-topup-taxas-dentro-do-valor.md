# CORRECAO-264 — Recarga de saldo: taxas descontadas do valor, não somadas em cima

## Data
2026-07-15

## Pedido
Formato anterior (CORRECAO-260): digitar R$ 50,00 gerava PIX de R$ 51,50
(50 + taxa PIX 0,50 + taxa serviço 1,00) — a loja pagava a mais que o
digitado. Pedido: "não pode contar as taxas nessa parte, se eu colocar 50,
ele tem que pagar 50" — o valor digitado passa a ser o TOTAL cobrado no PIX;
as taxas saem de dentro dele, o saldo creditado é o que sobra.

## O que mudou

**Backend** (`apps/api/app/merchants/router.py::create_credit_topup`):
- Antes: `total_cents = body.amount_cents + taxa_pix_cents + taxa_servico_cents`
  (PIX cobrado > digitado).
- Agora: `total_cents = body.amount_cents` (PIX cobra exatamente o digitado);
  `net_amount_cents = total_cents - taxa_pix_cents - taxa_servico_cents`
  (o que vira saldo).
- Nova validação: se `net_amount_cents <= 0` (valor não cobre as taxas),
  422 `topup_below_fees` — "Valor informado nao cobre as taxas da recarga."
  Antes disso não existia esse risco (taxas eram somadas, nunca subtraídas).
- `charge.net_amount_cents` agora grava o líquido calculado (antes gravava
  `body.amount_cents` direto). O webhook (`webhooks_router.py`) já creditava
  `charge.net_amount_cents` — não precisou mudar, o valor que ele lê que
  mudou de significado.
- `CreditTopupResponse.amount_cents` continua com o mesmo papel semântico
  ("o que vira saldo") — só o número que veio nele mudou. `total_cents`
  continua "o que o PIX cobra" — mesmo campo, mesma semântica, cálculo
  diferente. Não precisei mexer no schema.

**Frontend** (`apps/web/src/features/loja/financeiro/saldo.page.ts` +
`.html`):
- `topupExpectedTotalCents` (amount + taxas) virou `topupExpectedNetCents`
  (amount - taxas) — a prévia agora mostra quanto vira saldo, não quanto
  vai pagar a mais.
- `topupValid` passou a exigir também `topupExpectedNetCents() > 0` (senão
  o botão "Fazer recarga" fica desabilitado antes mesmo de bater no
  backend).
- No modal: "Total a pagar via PIX" agora mostra o valor digitado
  (`topupAmountCents()`) direto — antes mostrava amount+taxas. "Recarga
  (vira saldo)" passou a mostrar o líquido — antes mostrava o valor
  digitado bruto. Ordem das linhas invertida (taxas primeiro, recarga
  líquida por último, total = valor digitado) pra bater com a lógica nova
  de "de dentro do valor que você digitou saem as taxas, sobra isso pro
  saldo".
- Mensagem de erro nova quando o valor não cobre as taxas (distinta da
  mensagem genérica de "digite um valor maior que R$ 0,00").

## Exemplo (taxa pix 0,50 + taxa serviço 1,00)
Digitar R$ 50,00 → PIX cobra R$ 50,00 → vira saldo R$ 48,50.

## Validado
- `docker compose exec api python -c "import app.merchants.router; import
  app.main"` — import limpo.
- `ng build web` — verde, sem erro novo (só warnings pré-existentes de
  outras páginas, nada relacionado a essa mudança).
- API reiniciada, `/health` ok.

## Não testado
Não testei o fluxo end-to-end criando um PIX de verdade com essa fórmula
nova (pagamento real via Safe2Pay) — só validei import limpo + build. Vale
a loja testar uma recarga pequena pra confirmar que o saldo que cai bate
com valor digitado menos as taxas do plano.

## Tech debt / pontos em aberto (já existiam, não mudou aqui)
- `CREDIT_TOPUP_MIN_CENTS` continua em 1 centavo (reduzido de R$5
  temporariamente, CORRECAO-260) — precisa voltar pra 500 antes de
  produção. Com a fórmula nova, o piso real relevante passou a ser
  "valor > taxa_pix + taxa_servico", que já é validado em runtime
  (`topup_below_fees`) independente desse mínimo fixo.
