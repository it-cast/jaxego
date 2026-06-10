# Skill: safe2pay-escrow-br

> **Padrões de integração Safe2Pay para marketplace brasileiro com escrow (Pix + Cartão)**
> Categoria: `domain` · Stack: FastAPI + httpx + MySQL · Versão: 1.0 · 2026-04-18

---

## Propósito

Implementar integração correta e resiliente com o gateway Safe2Pay em contexto de marketplace com escrow — desde a criação do pagamento até o webhook de liquidação, estorno, e reconciliação contábil. Este é um domínio com muitas armadilhas sutis (HasError no corpo da resposta, múltiplos subdomínios, idempotência de webhook, diferenças Pix vs. Cartão) que causam bugs de produção quando ignoradas.

## Quando usar esta skill (triggers)

Consulte esta skill **antes de planejar ou tocar** em qualquer uma destas situações:

- Criar novo endpoint que chama qualquer API da Safe2Pay
- Modificar código de `PaymentService`, `payments router`, ou `webhook handler`
- Adicionar suporte a nova forma de pagamento (boleto, cartão de débito, assinatura recorrente)
- Implementar estorno (refund) total ou parcial
- Debugar transação que "ficou pendurada" em status intermediário
- Reconciliar extrato Safe2Pay com tabela `payments` local
- Adicionar webhook handler ou modificar validação de assinatura
- Implementar split payment (Fase 3)

## Quando NÃO usar

- Interface visual de pagamento no mobile → use `ui-ux-pro-max` + `ionic-patterns` (Onda 1)
- Criar tela de "pagamentos do admin" sem tocar em chamadas Safe2Pay → use `angular-material-patterns` (Onda 1)
- Copywriting de mensagens de erro pro usuário → use `ux-copywriting-ptbr` (Onda 2)

---

## Conceitos-chave da Safe2Pay

### Subdomínios (e por que importam)

Safe2Pay roteia diferentes operações em **subdomínios diferentes**. Errar o subdomínio é uma das causas mais comuns de `404` ou `"HasError": true` sem mensagem clara.

| Subdomínio | Finalidade | Exemplos de endpoints |
|---|---|---|
| `payment.safe2pay.com.br` | Criação e consulta de transações | `POST /v2/Payment` (Pix), `POST /v2/Payment/Credit` (cartão), `GET /v2/Transaction/{id}` |
| `api.safe2pay.com.br` | Operações administrativas, subcontas, refunds | `POST /v2/Transaction/Refund`, `GET /v2/Account/Balance` |
| `services.safe2pay.com.br` | Serviços auxiliares (validação de CPF/CNPJ, consultas) | `GET /v2/Lookup/Document` |

**Regra mnemônica:** `payment` cria, `api` administra, `services` consulta.

### Autenticação

Safe2Pay aceita dois modos, não misture:

1. **`x-api-key` no header** — token por ambiente (sandbox / produção). Preferível para server-to-server.
2. **`TokenAuthentication` no header** — usado em contextos SDK/mobile. Não usar no backend.

No GBC, o token vive em `system_settings` (AES-256 encrypted) e é lido pelo `Safe2PayService` no startup. **Nunca** hard-code token. **Nunca** logar token em clear text (mascarar `****` exceto últimos 4 chars).

### O padrão `HasError`

Este é o erro #1 em integrações Safe2Pay malfeitas.

**Resposta HTTP 200 da Safe2Pay NÃO significa sucesso.** Safe2Pay retorna `200` mesmo quando a operação falhou, e indica erro via campo `HasError` no corpo:

```json
{
  "HasError": true,
  "Error": "Código 40012",
  "ErrorCode": "40012",
  "ResponseDetail": {
    "Message": "Valor abaixo do mínimo permitido para Pix"
  }
}
```

**Padrão obrigatório no backend:**

```python
async def _call_safe2pay(url: str, payload: dict) -> dict:
    """Chamada resiliente à Safe2Pay com tratamento correto de HasError."""
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(url, json=payload, headers=self._headers())
            response.raise_for_status()  # 4xx/5xx viram exception
        except httpx.HTTPStatusError as e:
            logger.error("safe2pay_http_error", status=e.response.status_code, url=url)
            raise PaymentGatewayError(f"Safe2Pay HTTP {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error("safe2pay_network_error", error=str(e), url=url)
            raise PaymentGatewayError("Safe2Pay inacessível") from e

        data = response.json()

        # ⚠️ CRÍTICO: HasError ignora status HTTP
        if data.get("HasError"):
            error_code = data.get("ErrorCode", "unknown")
            error_detail = data.get("ResponseDetail", {}).get("Message", data.get("Error", ""))
            logger.error(
                "safe2pay_business_error",
                error_code=error_code,
                error_detail=error_detail,
                url=url,
            )
            raise PaymentGatewayError(
                f"Safe2Pay erro {error_code}: {error_detail}",
                code=error_code,
            )

        return data.get("ResponseDetail", data)
```

### Estados de uma transação (state machine)

Estados que `payments.status` pode assumir, e quem os transiciona:

```
      ┌─────────────┐
      │   PENDING   │ ← criação (cliente gerou QR Pix ou submeteu cartão)
      └──────┬──────┘
             │ webhook Safe2Pay (Transação aprovada)
             ▼
      ┌─────────────┐
      │    HELD     │ ← escrow retido (sucesso do pagamento)
      └──────┬──────┘
             │
       ┌─────┴─────┐
       │           │
 cliente       72h passam
 confirma      sem ação
 conclusão     (auto-release)
       │           │
       ▼           ▼
  ┌─────────────┐
  │  RELEASED   │ ← valor liberado pro profissional (12% fica pro GBC)
  └─────────────┘

       OU

  ┌─────────────┐
  │  REFUNDED   │ ← estorno (cliente cancelou antes do serviço, ou disputa resolvida a favor)
  └─────────────┘

       OU

  ┌─────────────┐
  │   FAILED    │ ← transação rejeitada (cartão negado, Pix expirou sem pagamento)
  └─────────────┘
```

**Regras invioláveis:**
- Transição só acontece via **webhook** (HELD, RELEASED, REFUNDED, FAILED) ou via **scheduler** de auto-release (RELEASED após 72h)
- **Nunca** o usuário muda status diretamente via endpoint
- `service_timeline` deve registrar **cada transição** com `actor`, `timestamp`, `reason`
- Transição atômica no banco: `status` + `service_timeline` + (se aplicável) notificação — tudo no mesmo `BEGIN/COMMIT`

---

## Fluxos principais

### 1. Criar pagamento Pix (client paga)

```python
# services/payment.py
async def create_pix_payment(
    self,
    *,
    service_request_id: UUID,
    client_id: UUID,
    amount: Decimal,  # preço do serviço; taxa 12% é somada aqui
) -> PixPaymentResponse:
    """Cria cobrança Pix com QR code via Safe2Pay."""
    fee = (amount * Decimal("0.12")).quantize(Decimal("0.01"))
    total = amount + fee

    # Idempotência: 1 payment por service_request (constraint no banco)
    async with self.db.begin():
        payment = await self.repo.create_pending(
            service_request_id=service_request_id,
            client_id=client_id,
            amount=amount,
            fee=fee,
            total=total,
            method="pix",
            idempotency_key=str(uuid4()),  # para webhook
        )

    payload = {
        "Amount": float(total),
        "Reference": str(payment.id),  # echoed back no webhook
        "Callback": f"{settings.API_BASE_URL}/api/v1/webhooks/safe2pay",
        "Customer": await self._build_customer_block(client_id),
        "PaymentMethod": 6,  # 6 = Pix no vocabulário Safe2Pay
    }

    try:
        result = await self._call_safe2pay(
            url=f"{self.PAYMENT_URL}/v2/Payment",
            payload=payload,
        )
    except PaymentGatewayError as e:
        # Marca o payment como falha para não ficar pendurado
        await self.repo.mark_failed(payment.id, reason=str(e))
        raise

    # Atualiza payment com transaction_id e qr code da Safe2Pay
    await self.repo.attach_gateway_data(
        payment.id,
        gateway_transaction_id=result["IdTransaction"],
        qr_code_base64=result["PaymentObject"]["QrCode"],
        qr_code_text=result["PaymentObject"]["Key"],
        expires_at=parse_datetime(result["PaymentObject"]["ExpirationDate"]),
    )

    return PixPaymentResponse(
        payment_id=payment.id,
        qr_code_base64=result["PaymentObject"]["QrCode"],
        qr_code_text=result["PaymentObject"]["Key"],
        expires_at=result["PaymentObject"]["ExpirationDate"],
    )
```

### 2. Webhook de confirmação (Safe2Pay → GBC)

```python
# routers/webhooks.py
@router.post("/safe2pay", status_code=200)
async def safe2pay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Recebe notificação da Safe2Pay. Idempotente."""
    body = await request.body()
    signature = request.headers.get("x-signature")

    # 1. Validar assinatura (HMAC-SHA256 com secret)
    if not _verify_signature(body, signature):
        logger.warning("safe2pay_webhook_invalid_signature", ip=request.client.host)
        raise HTTPException(403, "Assinatura inválida")

    payload = json.loads(body)
    transaction_id = payload["IdTransaction"]
    status_code = payload["Status"]  # 3 = aprovada, 13 = cancelada, etc.
    reference = payload.get("Reference")  # payment.id que mandamos

    service = PaymentService(db)

    # 2. Idempotência: payment.gateway_transaction_id é UNIQUE
    # Se mesma Safe2Pay transaction já foi processada, retornar 200 sem side-effects
    already_processed = await service.was_webhook_processed(transaction_id, status_code)
    if already_processed:
        return {"ok": True, "idempotent": True}

    # 3. Transição de estado atômica
    if status_code == 3:  # aprovada
        await service.mark_held(payment_id=reference, transaction_id=transaction_id)
    elif status_code in (6, 13):  # recusada / cancelada
        await service.mark_failed(payment_id=reference, reason=f"Safe2Pay status {status_code}")
    elif status_code == 11:  # estornada
        await service.mark_refunded(payment_id=reference, transaction_id=transaction_id)
    else:
        logger.info("safe2pay_webhook_unhandled_status", status=status_code)

    return {"ok": True}
```

### 3. Estorno (Pix ou Cartão) — um dos gaps atuais do MVP

Estorno Pix e estorno Cartão usam **endpoints diferentes** em **subdomínios diferentes**:

```python
async def refund(self, payment_id: UUID, *, reason: str) -> None:
    """Estorna pagamento. Funciona para Pix e Cartão, com rotas diferentes."""
    payment = await self.repo.get(payment_id)
    if not payment:
        raise NotFound("Pagamento não encontrado")
    if payment.status not in (PaymentStatus.HELD,):
        raise BusinessRule(
            f"Só é possível estornar pagamento em estado HELD. Estado atual: {payment.status}"
        )

    # ⚠️ Roteamento por método de pagamento
    if payment.method == "pix":
        url = f"{self.API_URL}/v2/Transaction/Refund"  # api subdomain
        payload = {
            "IdTransaction": payment.gateway_transaction_id,
            "Amount": float(payment.total),  # refund total apenas no MVP
        }
    elif payment.method == "credit":
        url = f"{self.API_URL}/v2/CreditCard/Reverse"  # api subdomain, endpoint diferente
        payload = {
            "IdTransaction": payment.gateway_transaction_id,
            "Amount": float(payment.total),
        }
    else:
        raise BusinessRule(f"Estorno não suportado para método {payment.method}")

    try:
        await self._call_safe2pay(url=url, payload=payload)
    except PaymentGatewayError as e:
        logger.error("refund_failed", payment_id=str(payment_id), error=str(e))
        raise

    # Transição atômica: payment.status + service_timeline + conversa arquivada
    async with self.db.begin():
        await self.repo.mark_refund_pending(payment.id, reason=reason)
        await self.timeline.log(
            service_request_id=payment.service_request_id,
            actor="system",
            event="refund_requested",
            detail=reason,
        )

    # O webhook final confirmará o REFUNDED (status 11)
```

---

## Armadilhas conhecidas (erros que já vi ou vou ver)

### A1. Misturar subdomínios

**Sintoma:** HTTP 404 ou `HasError: true` sem mensagem útil.

**Causa:** chamar `api.safe2pay.com.br/v2/Payment` (que só existe em `payment.safe2pay.com.br`) ou `payment.safe2pay.com.br/v2/Transaction/Refund` (que só existe em `api`).

**Solução:** ter 3 base URLs no `Safe2PayService` — `PAYMENT_URL`, `API_URL`, `SERVICES_URL` — lidas de `system_settings`, nunca concatenar strings.

### A2. Ignorar `HasError` porque o HTTP foi 200

**Sintoma:** código acha que deu tudo certo, mas a transação nunca foi criada.

**Causa:** não checar `data["HasError"]` porque `response.status == 200`.

**Solução:** helper `_call_safe2pay` centralizado que **sempre** checa HasError.

### A3. Webhook não-idempotente

**Sintoma:** mesma transação é processada 2x (Safe2Pay às vezes reenvia), payment `status` oscila, `service_timeline` tem entradas duplicadas.

**Causa:** handler não verifica se webhook com mesmo `(transaction_id, status)` já foi processado.

**Solução:** tabela `webhook_events` com UNIQUE(`gateway_transaction_id`, `status_code`) + verificação no início do handler.

### A4. Validação de assinatura faltando ou errada

**Sintoma:** atacante pode POSTar webhook falso, liberando escrow sem pagamento real.

**Causa:** não validar header `x-signature` contra HMAC-SHA256 do body com secret.

**Solução:** função `_verify_signature(body, sig)` obrigatória. Secret vem de `system_settings` (AES-256 encrypted).

### A5. Taxa 12% calculada no frontend

**Sintoma:** cliente vê R$ 100,00 na tela e no banco foi criado payment de R$ 100,00 (sem taxa) ou R$ 112,00 (com taxa duplicada).

**Causa:** frontend calcula fee e manda total. Payload corrompível.

**Solução:** **sempre** backend calcula fee. Frontend manda `amount` (preço do serviço). Backend soma 12% e manda `total` pra Safe2Pay.

### A6. Ignorar `expiresAt` do Pix

**Sintoma:** QR code expira (geralmente 24h), cliente tenta pagar, Safe2Pay aceita o pagamento mas webhook nunca dispara porque ficou órfão.

**Solução:** salvar `expires_at` no payment. Scheduler APScheduler marca `FAILED` automático após expiração.

### A7. Estorno parcial não suportado no MVP, mas pedido mesmo assim

**Sintoma:** admin tenta estorno de R$ 50 de um payment de R$ 100. Safe2Pay aceita o parcial, mas payment local vai pra REFUNDED (total) incorretamente.

**Solução (MVP):** só permitir estorno total. Validar `amount == payment.total` antes de chamar Safe2Pay. Estorno parcial fica pra Fase 2.

### A8. Log de token Safe2Pay em clear text

**Sintoma:** violação LGPD + vulnerabilidade de segurança.

**Solução:** middleware de logging **mascara** `x-api-key` automaticamente. Nunca logar `headers` crus.

---

## Checklist de review de PR que toca Safe2Pay

Antes de aprovar qualquer PR que modifique integração Safe2Pay, verifique:

- [ ] `HasError` é checado em toda resposta (helper `_call_safe2pay` usado)
- [ ] Subdomínio correto para cada endpoint (`payment` / `api` / `services`)
- [ ] Webhook valida assinatura HMAC-SHA256 antes de qualquer efeito colateral
- [ ] Webhook é idempotente (constraint UNIQUE em `webhook_events`)
- [ ] Transição de estado é atômica (`payment.status` + `service_timeline` no mesmo commit)
- [ ] Taxa 12% calculada no backend, nunca no frontend
- [ ] `Reference` no payload da Safe2Pay é o `payment.id` local (para reconciliação)
- [ ] Token Safe2Pay vem de `system_settings` (AES-256), não hard-coded nem em `.env`
- [ ] Logs não contêm token em clear text
- [ ] Erros da Safe2Pay (HasError) são propagados com `error_code` estruturado, não string genérica
- [ ] Timeout do `httpx.AsyncClient` configurado (recomendado: 30s)
- [ ] Retry logic apenas em erros de **rede**, **nunca** em erros de negócio (HasError)
- [ ] Testes mockam Safe2Pay via `monkeypatch` — credenciais reais nunca em CI
- [ ] `service_request` e `payment` têm FK + constraint UNIQUE que impede pagamento duplicado
- [ ] Proposta aceita é atômica: `service_request` + `payment` + arquivar siblings + atualizar quote status + timeline, tudo no mesmo `BEGIN/COMMIT`

---

## Cobertura atual do GBC (gaps conhecidos)

Referência: memórias do projeto + `.planning/STATE.md`. Cobertura hoje: **4 de 26 features Safe2Pay**.

### ✅ Implementado

1. Criar pagamento Pix
2. Criar pagamento Cartão de Crédito
3. Webhook de confirmação (status 3)
4. Escrow held até confirmação do cliente / auto-release 72h

### 🔴 Gaps críticos (bloqueiam UAT full)

5. **Estorno Pix** (`api.safe2pay.com.br/v2/Transaction/Refund`)
6. **Estorno Cartão** (`api.safe2pay.com.br/v2/CreditCard/Reverse`)
7. **HasError handling consistente** — todos os calls devem passar por `_call_safe2pay`
8. **Roteamento correto entre `payment/api/services`** — auditar cada endpoint atual
9. Webhook para status ≠ 3 (6 recusada, 11 estornada, 13 cancelada)

### 🟡 Gaps não-bloqueantes (Fase 2+)

10. Validação de assinatura HMAC no webhook (hoje pode estar faltando)
11. Idempotência robusta (tabela `webhook_events` explícita)
12. Consulta de saldo da subconta
13. Transfer entre contas (para split futuro)
14. Boleto
15. Assinatura recorrente
16. Cartão de débito
17. Antifraude (Clearsale integration)
18. Reconciliação de extrato (batch job semanal)
19. Notas fiscais (NFSe)
20. Split payment para múltiplos profissionais
21. Dashboard financeiro com gráficos
22. Export de extrato (CSV, XLSX)
23. Relatórios para contabilidade
24. Multi-currency (Fase 3+)
25. Link de pagamento (checkout externo)
26. Cobrança recorrente

**Ação imediata:** aguardar Postman collection do Cadu para confirmar endpoints exatos de estorno e ajustar URLs conforme documentação oficial.

---

## Testes

Estrutura recomendada para testes de payment:

```python
# tests/services/test_payment_service.py
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def safe2pay_mock(monkeypatch):
    """Mock que substitui _call_safe2pay sem chamar a rede."""
    mock = AsyncMock()
    monkeypatch.setattr(
        "app.services.payment.PaymentService._call_safe2pay",
        mock,
    )
    return mock

@pytest.mark.asyncio
async def test_pix_payment_success(db, safe2pay_mock, service_request):
    safe2pay_mock.return_value = {
        "IdTransaction": "s2p_tx_123",
        "PaymentObject": {
            "QrCode": "base64...",
            "Key": "00020101...",
            "ExpirationDate": "2026-04-19T22:00:00",
        },
    }
    service = PaymentService(db)
    result = await service.create_pix_payment(
        service_request_id=service_request.id,
        client_id=service_request.client_id,
        amount=Decimal("100.00"),
    )
    assert result.qr_code_text.startswith("00020101")
    payment = await service.repo.get(result.payment_id)
    assert payment.status == PaymentStatus.PENDING
    assert payment.fee == Decimal("12.00")
    assert payment.total == Decimal("112.00")

@pytest.mark.asyncio
async def test_pix_payment_has_error_raises(db, safe2pay_mock, service_request):
    from app.exceptions import PaymentGatewayError
    # Simula HasError: true da Safe2Pay
    safe2pay_mock.side_effect = PaymentGatewayError("40012: valor abaixo do mínimo", code="40012")
    service = PaymentService(db)
    with pytest.raises(PaymentGatewayError):
        await service.create_pix_payment(
            service_request_id=service_request.id,
            client_id=service_request.client_id,
            amount=Decimal("0.50"),
        )
    # Payment deve ter ficado marcado como FAILED, não PENDING órfão
    payments = await service.repo.list_for_service_request(service_request.id)
    assert payments[-1].status == PaymentStatus.FAILED

@pytest.mark.asyncio
async def test_webhook_idempotent(client, db, held_payment):
    """Enviar mesmo webhook 2x produz 1 único side-effect."""
    payload = {"IdTransaction": held_payment.gateway_transaction_id, "Status": 3, "Reference": str(held_payment.id)}
    # 1ª vez
    r1 = await client.post("/api/v1/webhooks/safe2pay", json=payload, headers=_sign(payload))
    # 2ª vez (replay)
    r2 = await client.post("/api/v1/webhooks/safe2pay", json=payload, headers=_sign(payload))
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json().get("idempotent") is True
```

---

## Anti-patterns registrados

Nunca faça:

- ❌ `requests.post(...)` síncrono — usar sempre `httpx.AsyncClient`
- ❌ Chamar Safe2Pay dentro de transação de banco aberta (I/O bloqueante lock)
- ❌ Processar webhook e retornar 500 quando erro — Safe2Pay vai reenviar indefinidamente
- ❌ Retornar 200 sem processar (só pra parar o retry) — inconsistência silenciosa
- ❌ Concatenar URL com string (use f-string ou `urllib.parse.urljoin` só com base URL confiável)
- ❌ Guardar token Safe2Pay no git, no `.env` versionado, ou em log
- ❌ Validar signature com `==` sem `secrets.compare_digest` (timing attack)

---

## Referências externas

- Docs oficiais Safe2Pay: https://developers.safe2pay.com.br (atualizar quando Postman chegar)
- PHP integration do Cadu (projeto ITCAST anterior) — usar como blueprint de endpoints exatos
- Postman collection: **pendente de envio pelo Cadu**

---

## Evolução desta skill

Última atualização: 2026-04-18 (criação)

Atualizar esta skill quando:
- Postman collection oficial chegar → confirmar URLs e payloads exatos
- Split payment for implementado (Fase 3) → adicionar seção
- Boleto for adicionado (improvável Fase 2) → adicionar seção
- Antifraude Clearsale for integrado → adicionar seção

<!-- Skill aplicada em: nenhum arquivo ainda — criada em 2026-04-18 para desbloquear UAT do MVP -->
