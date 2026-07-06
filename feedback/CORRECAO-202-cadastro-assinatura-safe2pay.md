---
classe: feature
data: 2026-07-06
arquivos_afetados:
  - apps/api/app/merchants/schemas.py
  - apps/api/app/plans/router.py
  - packages/shared/src/shared/components/plan-card/plan-card.component.ts
  - packages/shared/src/shared/components/components.spec.ts
  - packages/shared/src/shared/components/upgrade-modal/upgrade-modal.stories.ts
  - apps/web/src/features/loja/cadastro/merchant.models.ts
  - apps/web/src/features/loja/cadastro/merchant.service.ts
  - apps/web/src/features/loja/cadastro/cadastro.page.ts
  - apps/web/src/features/loja/cadastro/cadastro.page.html
  - apps/web/src/features/loja/cadastro/cadastro.page.scss
---

## Problema
O wizard de cadastro enviava `plan_code` ao fazer signup mas não coletava nenhum dado de pagamento para planos pagos. O backend criava o merchant com `status=pending_payment` (e uma assinatura Free ativa), mas o frontend ignorava esse estado e redirecionava para a tela de sucesso como se nada houvesse.

## Causa raiz
- O endpoint `GET /v1/plans` não retornava o `id` inteiro do plano, apenas o `codename` (string) — e o endpoint de ativação `POST /v1/payments/assinar` exige `plan_id` (inteiro)
- O wizard não tinha nenhuma lógica de pagamento pós-signup
- O endpoint `POST /v1/payments/assinar` exige autenticação, mas o usuário recém-cadastrado não tinha sessão iniciada

## Implementação

### Backend
- `PlanRead` schema: adicionado campo `id: int`
- `plans/router.py`: incluído `id=p.id` na projeção ao listar planos

### Shared components
- `Plan` interface: adicionado `id: number`
- Mocks em `components.spec.ts` e `upgrade-modal.stories.ts`: adicionado `id` nos objetos de plano

### Frontend
- `PlanDto`: adicionado `id: number`
- Adicionados `SubscribeRequest`, `SubscribeResponse`, `SubscribeResult` a `merchant.models.ts`
- `MerchantService`: adicionados métodos `getPublicKey()` e `subscribe(req)`
- `CadastroLojaPage`:
  - Injetado `AuthService`
  - `choosePlan()` agora salva `pendingPlanId = plan.id`
  - `submit()`: ao receber `status === 'pending_payment'` do backend, faz auto-login com as credenciais digitadas no wizard, busca a chave RSA pública e exibe a seção de pagamento
  - Adicionados: `submitPayment()`, `encryptCard()` (Web Crypto API — RSA-OAEP SHA-256), `setPayMethod()`, `onCardNumberInput()`, `onCardExpiryInput()`, `goToLoja()`
  - Novos signals: `showPayment`, `payMethod`, `cardHolder`, `cardNumber`, `cardExpiry`, `cardCvv`, `pixQrCode`, `pixQrB64`, `paymentError`, `paymentLoading`, `pixPending`
- HTML: adicionada seção de pagamento (card + PIX) que aparece após signup com plano pago; formulário do wizard ocultado durante o pagamento
- SCSS: adicionados estilos `.jx-cadastro__payment*` para a seção de pagamento

## Fluxo resultante
1. Usuário escolhe plano pago no wizard → clica "Ativar loja"
2. Backend cria merchant com `status=pending_payment` + assinatura Free ativa (loja funciona)
3. Frontend auto-loga com email/senha → token de acesso na memória
4. Frontend busca chave RSA pública (`GET /v1/payments/chave-publica`)
5. Exibe seção de pagamento: Cartão ou PIX
6. **Cartão**: coleta nome, número, validade, CVV → cifra com RSA-OAEP → `POST /v1/payments/assinar` → redireciona para sucesso
7. **PIX**: chama `POST /v1/payments/assinar` com method=pix → exibe QR Code → aguarda webhook do Safe2Pay para ativar assinatura automaticamente
