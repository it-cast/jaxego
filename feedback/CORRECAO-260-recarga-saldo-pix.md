# CORRECAO-260 — Recarga de saldo via PIX

## Data
2026-07-14

## Pedido
Botão "Adicionar saldo" na tela `/loja/saldo` — modal com valores prontos
(R$20/50/100/200) + campo pra digitar outro valor, gera um PIX pra conta da
ITCAST filha, e ao confirmar o pagamento credita o valor no saldo da loja.
Cobrando taxa PIX + taxa de sistema do plano em cima do valor pedido (ex.:
taxa_pix=R$0,50, taxa_servico=R$1,00 → recarregar R$10 cobra R$11,50).
Mínimo de recarga: R$5,00. Explicado antes de implementar, plano aprovado
pelo usuário sem alterações além do valor mínimo.

## Desenho

### Duas colunas novas (migration 0049)
- `platform_charges.merchant_id` — as cobranças de recarga não são amarradas
  a uma entrega nem a uma assinatura (os dois jeitos que já existiam de saber
  "de quem é essa cobrança"); precisava de um terceiro.
- `platform_charges.net_amount_cents` — separa o TOTAL cobrado no PIX
  (`amount_cents`, já com as taxas somadas) do valor que efetivamente vira
  saldo (só a recarga, sem as taxas — que ficam de receita da plataforma,
  mesma lógica de hoje pra corrida de entrega).
- `merchant_credit_ledger.charge_id` — chave de idempotência do lançamento
  `topup` (uma cobrança credita o saldo no máximo uma vez, mesmo se o
  webhook da Safe2Pay reenviar o evento).

### Novo kind "topup"
Adicionado em `CHARGE_KINDS` (`payments/models.py`) e
`MERCHANT_CREDIT_KINDS` (`merchants/models.py`) — cabe em `String(16)`
(5 caracteres).

### Fluxo
1. `GET /v1/merchants/plan-taxas` — retorna `taxa_pix_cents`/
   `taxa_servico_cents` do plano ativo da loja. Chamado quando o modal abre,
   pra mostrar o resumo (recarga + taxas = total) ANTES da loja confirmar —
   mesmos valores que o servidor vai cobrar de verdade.
2. `POST /v1/merchants/credit-topup` (`{amount_cents}`, mínimo 500 = R$5) —
   resolve as taxas de novo no servidor (nunca confia em nada vindo do
   cliente), cria o PIX via Safe2Pay (`create_pix_authorization`, mesmo
   adapter/rota que a criação de entrega usa) pelo total (recarga+taxas),
   grava a `platform_charges` com `kind="topup"`, `status="open"`,
   `merchant_id`, `net_amount_cents=amount_cents` (só a recarga). Devolve
   QR code + copia-e-cola.
3. Modal mostra o QR e consulta `GET /v1/merchants/credit-topup/{charge_id}/
   status` a cada 5s (mesmo padrão de polling da tela de Plano —
   `plano.page.ts`).
4. Quando a Safe2Pay confirma o pagamento, o webhook
   (`payments/webhooks_router.py::_process_event`) já tinha duas branches
   (assinatura, entrega) — adicionei uma terceira: `kind == "topup"` →
   `credit.record_topup(amount_cents=charge.net_amount_cents)` — credita só
   a recarga, não o total com taxas. Idempotente por `charge_id`.
5. Polling detecta `paid=true` → modal mostra sucesso → ao fechar, recarrega
   saldo/extrato da tela.

## Arquivos

### Backend
- `alembic/versions/0049_platform_charge_merchant_topup.py` (nova) — as 3
  colunas.
- `app/payments/models.py` — `CHARGE_KINDS` + campos novos em
  `PlatformCharge`.
- `app/merchants/models.py` — `MERCHANT_CREDIT_KINDS` + `charge_id` em
  `MerchantCreditLedger`.
- `app/merchants/credit.py` — `record_topup()` (idempotente por
  `charge_id`).
- `app/merchants/schemas.py` — `CreditTopupBody` (min R$5),
  `CreditTopupResponse`, `CreditTopupStatusResponse`.
- `app/merchants/router.py` — `_active_plan_taxas()` (helper compartilhado),
  `GET /plan-taxas`, `POST /credit-topup`, `GET /credit-topup/{id}/status`.
- `app/payments/repo.py` — `get_topup_charge_for_merchant()` (IDOR-safe,
  scoped por merchant_id).
- `app/payments/webhooks_router.py` — branch nova pro `kind == "topup"`.

### Frontend
- `apps/web/.../financeiro/saldo.page.ts` — modal completo: presets, campo
  custom (reusa `maskBrl`/`parseBrl`/`formatCents` de
  `@jaxego/shared/util/money`, mesmos helpers da tela de nova entrega),
  resumo com taxas reais buscadas ao abrir o modal, submit, polling de
  status, tela de sucesso. `kindLabel()` ganhou `'topup'` → "Recarga de
  saldo".
- `.html`/`.scss` — modal + breakdown + QR/copia-cola, estilo espelhando
  `plano.page.ts`/`.scss` (mesmo padrão de modal PIX já usado na assinatura).

## Validado
- Import do backend limpo.
- Testado direto contra o banco (sem gerar PIX real): `_active_plan_taxas`
  retornou as taxas reais do plano (R$0,50 / R$1,00 — bateu com o exemplo
  que você deu). `record_topup` creditou certo (saldo 100→1100 pra uma
  recarga de R$10 simulada) e a segunda chamada com o mesmo `charge_id` não
  duplicou (idempotência confirmada). Dado de teste removido depois
  (`merchant_credit_ledger` não tem trigger de proteção, então a limpeza foi
  direta).
- `ng build web` — verde.
- Migration aplicada, API/worker reiniciados.

## Não testado
Não gerei um PIX real de ponta a ponta (custaria dinheiro de verdade e
exigiria escanear/pagar). A parte de criação do PIX reusa exatamente o mesmo
adapter (`create_pix_authorization`) já validado nas entregas e na
assinatura, então o risco é baixo, mas fica registrado que o fluxo completo
(gerar → pagar → webhook → saldo aparecer) não foi exercitado ao vivo.

## Tech debt / pontos em aberto
- Sem valor MÁXIMO de recarga — só mínimo (R$5). Não foi pedido, não
  implementei.
- Se a loja fechar o modal no meio do polling (PIX pendente, ainda não
  pago), a cobrança fica `status="open"` órfã — se ela pagar depois mesmo
  assim, o webhook credita normalmente (não depende do modal estar aberto),
  só não vai ver a confirmação na hora. Mesmo comportamento que a tela de
  Plano já tem hoje pra assinatura, não é regressão nova.
