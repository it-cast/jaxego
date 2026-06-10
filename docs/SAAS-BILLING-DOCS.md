# SaaS Billing com Safe2Pay — Documentação Completa

> **Referência canônica para todos os projetos SaaS.**
> Qualquer projeto que precise de assinaturas recorrentes por cartão ou PIX deve seguir exatamente esta mecânica.
> Implementação de referência: `converzas-api`.

---

## Índice

1. [Visão Geral da Arquitetura](#1-visão-geral-da-arquitetura)
2. [Schema do Banco de Dados](#2-schema-do-banco-de-dados)
3. [Entidades TypeORM](#3-entidades-typeorm)
4. [Criptografia](#4-criptografia)
5. [Integração Safe2Pay](#5-integração-safe2pay)
6. [Fluxos de Assinatura](#6-fluxos-de-assinatura)
7. [Cron Diário de Cobrança](#7-cron-diário-de-cobrança)
8. [Webhooks](#8-webhooks)
9. [Guard de Assinatura Ativa](#9-guard-de-assinatura-ativa)
10. [Lógica de Inadimplência](#10-lógica-de-inadimplência)
11. [Variáveis de Ambiente](#11-variáveis-de-ambiente)
12. [Rotas e Endpoints](#12-rotas-e-endpoints)
13. [Considerações de Segurança](#13-considerações-de-segurança)
14. [Guia de Adaptação para Novos Projetos](#14-guia-de-adaptação-para-novos-projetos)

---

## 1. Visão Geral da Arquitetura

```
Frontend                   Backend (NestJS)              Safe2Pay
   │                             │                           │
   │── RSA-OAEP(card data) ─────►│                           │
   │                             │── tokenize card ─────────►│
   │                             │◄── token ─────────────────│
   │                             │── charge with token ─────►│
   │                             │◄── transactionId ─────────│
   │◄── subscription active ─────│                           │
   │                             │                           │
   │                             │         [daily cron]      │
   │                             │── cobrarComToken ─────────►│
   │                             │◄── transactionId ─────────│
   │                             │                           │
   │── PIX subscription ────────►│                           │
   │                             │── criarAutorizacaoPix ───►│
   │                             │◄── autorizacaoId + QR ────│
   │◄── QR code ─────────────────│                           │
   │     [user pays]             │                           │
   │                             │◄─────────── webhook ──────│
   │                             │  (APROVADA → ativa sub)   │
   │                             │                           │
   │                             │         [daily cron]      │
   │                             │── criarAgendamentoPix ───►│
   │                             │◄── agendamentoId ─────────│
   │                             │◄─────────── webhook ──────│
   │                             │  (CONCLUIDA → próx. cob.) │
```

### Dois métodos de pagamento recorrente

| Método | Primeira cobrança | Recorrência | Gerenciada por |
|--------|-------------------|-------------|----------------|
| **Cartão** | Token criado na ativação | Token armazenado (AES-256-GCM) | Cron interno |
| **PIX Automático** | QR code da autorização | Agendamento Safe2Pay | Webhooks Safe2Pay |

---

## 2. Schema do Banco de Dados

### 2.1 Tabela `assinaturas`

```sql
CREATE TABLE assinaturas (
  id                        CHAR(36)       NOT NULL DEFAULT (UUID()) PRIMARY KEY,
  empresa_id                CHAR(36)       NOT NULL,  -- FK → empresas.id
  plano_id                  CHAR(36)       NOT NULL,  -- FK → planos.id
  status                    VARCHAR(20)    NOT NULL DEFAULT 'trial',
  -- status enum: 'trial' | 'active' | 'blocked' | 'cancelado'

  ciclo_cobranca            VARCHAR(10)    NULL,      -- 'mensal' | 'anual'
  usuario_extra             INT            NOT NULL DEFAULT 0,
  canal_extra               INT            NOT NULL DEFAULT 0,
  fluxo_extra               INT            NOT NULL DEFAULT 0,
  valor                     DECIMAL(10,2)  NOT NULL DEFAULT 0,  -- valor recorrente
  saldo_credito             DECIMAL(10,2)  NOT NULL DEFAULT 0,

  dt_assinatura             DATETIME       NULL,
  dt_vencimento             DATETIME       NULL,      -- próximo vencimento
  trial_termina_em          DATETIME       NULL,

  metodo_pagamento          VARCHAR(10)    NULL,      -- 'cartao' | 'pix'
  documento_cobranca        VARCHAR(20)    NULL,      -- CPF (cartão) ou CNPJ (pix)

  -- Cartão recorrente
  safe2pay_token            TEXT           NULL,      -- AES-256-GCM encrypted

  -- PIX Automático — estado temporário até webhook APROVADA
  pix_pendente_plano_id     CHAR(36)       NULL,
  pix_pendente_periodo      VARCHAR(10)    NULL,
  pix_pendente_valor        DECIMAL(10,2)  NULL,
  pix_pendente_transaction_id VARCHAR(100) NULL,

  -- PIX Automático — autorização permanente
  pix_autorizacao_id        VARCHAR(100)   NULL,
  pix_autorizacao_status    VARCHAR(20)    NULL,
  -- status: 'CRIADA' | 'APROVADA' | 'ATIVA' | 'CANCELADA' | 'EXPIRADA'

  -- QR code da primeira cobrança (limpo após webhook APROVADA)
  pix_qr_code               TEXT           NULL,
  pix_qr_code_base64        TEXT           NULL,
  pix_deep_link             VARCHAR(500)   NULL,

  -- Bloqueio por inadimplência
  bloqueada_em              DATETIME       NULL,
  motivo_bloqueio           TEXT           NULL,

  -- Cancelamento
  cancelada_em              DATETIME       NULL,
  motivo_cancelamento       TEXT           NULL,
  cancela_no_fim_periodo    TINYINT(1)     NOT NULL DEFAULT 0,

  created_at                DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at                DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  INDEX idx_assinaturas_empresa_id (empresa_id),
  INDEX idx_assinaturas_status (status),
  INDEX idx_assinaturas_dt_vencimento (dt_vencimento),
  INDEX idx_assinaturas_pix_autorizacao_id (pix_autorizacao_id)
);
```

### 2.2 Tabela `assinatura_cobranca`

```sql
CREATE TABLE assinatura_cobranca (
  id                CHAR(36)      NOT NULL DEFAULT (UUID()) PRIMARY KEY,
  assinatura_id     CHAR(36)      NOT NULL,
  -- FK → assinaturas.id ON DELETE CASCADE

  dt_vencimento     DATETIME      NOT NULL,
  valor             DECIMAL(10,2) NOT NULL DEFAULT 0,
  acrescimo         DECIMAL(10,2) NOT NULL DEFAULT 0,  -- em reais (não centavos)
  desconto          DECIMAL(10,2) NOT NULL DEFAULT 0,  -- em reais (não centavos)
  observacoes       TEXT          NULL,

  situacao          TINYINT       NOT NULL DEFAULT 0,
  -- 0 = aberto | 1 = pago | 2 = falhou | 3 = cancelado

  transaction_id    VARCHAR(100)  NULL,   -- Safe2Pay transaction ID
  pix_key           TEXT          NULL,   -- PIX Copia e Cola (one-time PIX)
  pix_agendamento_id VARCHAR(100) NULL,   -- ID do agendamento PIX Automático
  link_pagamento    TEXT          NULL,   -- URL fallback (cobrança falhou)

  created_at        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  INDEX idx_assinatura_cobranca_assinatura_id (assinatura_id),
  INDEX idx_assinatura_cobranca_situacao (situacao),
  INDEX idx_assinatura_cobranca_dt_vencimento (dt_vencimento),
  INDEX idx_assinatura_cobranca_transaction_id (transaction_id),
  INDEX idx_assinatura_cobranca_pix_agendamento_id (pix_agendamento_id),

  CONSTRAINT fk_assinatura_cobranca_assinatura
    FOREIGN KEY (assinatura_id) REFERENCES assinaturas(id) ON DELETE CASCADE
);
```

### 2.3 Tabela `planos`

```sql
CREATE TABLE planos (
  id                    CHAR(36)      NOT NULL DEFAULT (UUID()) PRIMARY KEY,
  nome                  VARCHAR(100)  NOT NULL,
  descricao             TEXT          NULL,
  preco                 DECIMAL(10,2) NOT NULL,  -- preço mensal base
  max_canais            INT           NOT NULL DEFAULT 1,
  max_usuarios          INT           NOT NULL DEFAULT 1,
  max_fluxos            INT           NOT NULL DEFAULT 0,
  max_storage_mb        INT           NOT NULL DEFAULT 100,
  valor_usuario_extra   DECIMAL(10,2) NOT NULL DEFAULT 0,
  valor_canal_extra     DECIMAL(10,2) NOT NULL DEFAULT 0,
  valor_fluxo_extra     DECIMAL(10,2) NOT NULL DEFAULT 0,
  is_active             TINYINT(1)    NOT NULL DEFAULT 1,
  is_popular            TINYINT(1)    NOT NULL DEFAULT 0,
  sort_order            INT           NOT NULL DEFAULT 0,
  created_at            DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at            DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 2.4 Tabela `webhook_logs`

```sql
CREATE TABLE webhook_logs (
  id          CHAR(36)     NOT NULL DEFAULT (UUID()) PRIMARY KEY,
  tipo        VARCHAR(50)  NOT NULL,
  -- 'autorizacao' | 'agendamento' | 'link-cobranca' | 'cron_erro' | 'cartao_sandbox' | 'cartao_tokenizacao' | 'cartao_cobranca'
  payload     TEXT         NOT NULL,
  created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_webhook_logs_tipo (tipo),
  INDEX idx_webhook_logs_created_at (created_at)
);
```

---

## 3. Entidades TypeORM

### 3.1 `assinatura.entity.ts`

```typescript
import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn,
         UpdateDateColumn, ManyToOne, JoinColumn } from 'typeorm';

@Entity('assinaturas')
export class Assinatura {
  @PrimaryGeneratedColumn('uuid') id: string;
  @Column({ name: 'empresa_id' }) empresaId: string;
  @Column({ name: 'plano_id' }) planoId: string;
  @Column({ default: 'trial' }) status: string;
  @Column({ name: 'ciclo_cobranca', nullable: true }) cicloCobranca: string;
  @Column({ name: 'usuario_extra', default: 0 }) usuarioExtra: number;
  @Column({ name: 'canal_extra', default: 0 }) canalExtra: number;
  @Column({ name: 'fluxo_extra', default: 0 }) fluxoExtra: number;
  @Column({ type: 'decimal', precision: 10, scale: 2, default: 0 }) valor: number;
  @Column({ name: 'saldo_credito', type: 'decimal', precision: 10, scale: 2, default: 0 }) saldoCredito: number;
  @Column({ name: 'dt_assinatura', type: 'datetime', nullable: true }) dtAssinatura: Date;
  @Column({ name: 'dt_vencimento', type: 'datetime', nullable: true }) dtVencimento: Date;
  @Column({ name: 'trial_termina_em', type: 'datetime', nullable: true }) trialTerminaEm: Date;
  @Column({ name: 'metodo_pagamento', nullable: true }) metodoPagamento: string;
  @Column({ name: 'documento_cobranca', nullable: true }) documentoCobranca: string;
  @Column({ name: 'safe2pay_token', type: 'text', nullable: true }) safe2payToken: string;
  @Column({ name: 'pix_pendente_plano_id', nullable: true }) pixPendentePlanoId: string;
  @Column({ name: 'pix_pendente_periodo', nullable: true }) pixPendentePeriodo: string;
  @Column({ name: 'pix_pendente_valor', type: 'decimal', precision: 10, scale: 2, nullable: true }) pixPendenteValor: number;
  @Column({ name: 'pix_pendente_transaction_id', nullable: true }) pixPendenteTransactionId: string;
  @Column({ name: 'pix_autorizacao_id', nullable: true }) pixAutorizacaoId: string;
  @Column({ name: 'pix_autorizacao_status', nullable: true }) pixAutorizacaoStatus: string;
  @Column({ name: 'pix_qr_code', type: 'text', nullable: true }) pixQrCode: string;
  @Column({ name: 'pix_qr_code_base64', type: 'text', nullable: true }) pixQrCodeBase64: string;
  @Column({ name: 'pix_deep_link', length: 500, nullable: true }) pixDeepLink: string;
  @Column({ name: 'cancela_no_fim_periodo', default: false }) cancelaNoFimPeriodo: boolean;
  @Column({ name: 'bloqueada_em', type: 'datetime', nullable: true }) bloqueadaEm: Date;
  @Column({ name: 'motivo_bloqueio', type: 'text', nullable: true }) motivoBloqueio: string;
  @Column({ name: 'cancelada_em', type: 'datetime', nullable: true }) canceladaEm: Date;
  @Column({ name: 'motivo_cancelamento', type: 'text', nullable: true }) motivoCancelamento: string;
  @CreateDateColumn({ name: 'created_at' }) createdAt: Date;
  @UpdateDateColumn({ name: 'updated_at' }) updatedAt: Date;

  @ManyToOne(() => Plano, { eager: true }) @JoinColumn({ name: 'plano_id' }) plano: Plano;
}
```

### 3.2 `assinatura-cobranca.entity.ts`

```typescript
import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn,
         UpdateDateColumn, ManyToOne, JoinColumn } from 'typeorm';

@Entity('assinatura_cobranca')
export class AssinaturaCobranca {
  @PrimaryGeneratedColumn('uuid') id: string;
  @Column({ name: 'assinatura_id' }) assinaturaId: string;
  @Column({ name: 'dt_vencimento', type: 'datetime' }) dtVencimento: Date;
  @Column({ type: 'decimal', precision: 10, scale: 2, default: 0 }) valor: number;
  @Column({ type: 'decimal', precision: 10, scale: 2, default: 0 }) acrescimo: number;
  @Column({ type: 'decimal', precision: 10, scale: 2, default: 0 }) desconto: number;
  @Column({ type: 'text', nullable: true }) observacoes: string;
  @Column({ type: 'tinyint', default: 0, comment: '0=aberto, 1=pago, 2=falhou, 3=cancelado' }) situacao: number;
  @Column({ name: 'transaction_id', nullable: true }) transactionId: string;
  @Column({ name: 'pix_key', type: 'text', nullable: true }) pixKey: string;
  @Column({ name: 'pix_agendamento_id', nullable: true }) pixAgendamentoId: string;
  @Column({ name: 'link_pagamento', type: 'text', nullable: true }) linkPagamento: string;
  @CreateDateColumn({ name: 'created_at' }) createdAt: Date;
  @UpdateDateColumn({ name: 'updated_at' }) updatedAt: Date;

  @ManyToOne(() => Assinatura)
  @JoinColumn({ name: 'assinatura_id' })
  assinatura: Assinatura;
}
```

---

## 4. Criptografia

### 4.1 Token Safe2Pay — AES-256-GCM

O token de cartão armazenado no banco **nunca fica em texto plano**. O formato é:

```
base64( iv[12 bytes] + authTag[16 bytes] + ciphertext )
```

**Variável de ambiente:** `DB_TOKEN_ENCRYPT_KEY` — 64 caracteres hexadecimais (= 32 bytes).

```typescript
import * as crypto from 'crypto';

const ALGO = 'aes-256-gcm';

function getTokenKey(): Buffer {
  const hex = process.env.DB_TOKEN_ENCRYPT_KEY;
  if (!hex || hex.length !== 64) {
    throw new Error('DB_TOKEN_ENCRYPT_KEY inválida: deve ser 64 chars hex (32 bytes)');
  }
  return Buffer.from(hex, 'hex');
}

export function encryptToken(plain: string): string {
  const key = getTokenKey();
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv(ALGO, key, iv) as crypto.CipherGCM;
  const encrypted = Buffer.concat([cipher.update(plain, 'utf8'), cipher.final()]);
  const tag = cipher.getAuthTag();
  return Buffer.concat([iv, tag, encrypted]).toString('base64');
}

export function decryptToken(encryptedBase64: string): string {
  try {
    const key = getTokenKey();
    const data = Buffer.from(encryptedBase64, 'base64');
    if (data.length <= 28) return encryptedBase64; // legado em texto puro
    const iv = data.subarray(0, 12);
    const tag = data.subarray(12, 28);
    const ciphertext = data.subarray(28);
    const decipher = crypto.createDecipheriv(ALGO, key, iv) as crypto.DecipherGCM;
    decipher.setAuthTag(tag);
    return Buffer.concat([decipher.update(ciphertext), decipher.final()]).toString('utf8');
  } catch {
    return encryptedBase64;
  }
}
```

### 4.2 Dados do cartão — RSA-OAEP 2048 (frontend → backend)

O frontend **nunca** envia dados de cartão em texto puro. Criptografa com a chave pública RSA antes de transmitir.

**Variáveis de ambiente:**
- `RSA_PUBLIC_KEY` — chave pública PEM (ou base64 do PEM) exposta via endpoint GET
- `RSA_PRIVATE_KEY` — chave privada PEM (ou base64 do PEM) usada apenas no backend

```typescript
import { privateDecrypt, createPrivateKey, constants } from 'crypto';

export function rsaDecrypt(privateKeyPemOrBase64: string, encryptedBase64: string): string {
  let pem = privateKeyPemOrBase64;
  if (!pem.startsWith('-----')) {
    pem = Buffer.from(pem, 'base64').toString('utf8');
  }
  const key = createPrivateKey(pem);
  const buffer = Buffer.from(encryptedBase64, 'base64');
  const decrypted = privateDecrypt(
    { key, padding: constants.RSA_PKCS1_OAEP_PADDING, oaepHash: 'sha256' },
    buffer,
  );
  return decrypted.toString('utf8');
}
```

**Payload que o frontend criptografa (JSON stringify → RSA-OAEP → base64):**
```json
{
  "nomeTitular": "NOME NO CARTAO",
  "numeroCartao": "4111111111111111",
  "validade": "12/2027",
  "cvv": "123"
}
```

### 4.3 Geração do par de chaves RSA

```bash
# Gerar par de chaves
openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -pubout -out public.pem

# Converter para base64 (para variável de ambiente em linha única)
base64 -w 0 private.pem > private.b64
base64 -w 0 public.pem > public.b64
```

---

## 5. Integração Safe2Pay

### 5.1 Configuração

```
Base URL:       https://payment.safe2pay.com.br
API V3 PIX:     https://payment.safe2pay.com.br/v3/pix/automatic/authorizations
Link Cobrança:  https://api.safe2pay.com.br/v2/singleSale/add
Header:         X-API-KEY: {SAFE2PAY_API_KEY}
```

Todos os métodos POST usam `Content-Type: application/json`.

### 5.2 Método: `processarCartao`

Fluxo unificado que trata sandbox e produção diferentemente.

**Sandbox** — cobra diretamente com dados raw (tokenização não disponível):
```typescript
POST /v2/payment
{
  IsSandbox: true,
  Application: "{NomeProjeto}",
  Vendor: "{NomeProjeto}",
  Reference: "assinatura-{timestamp}",
  Description: "{descricao}",
  PaymentMethod: "2",  // cartão
  PaymentObject: {
    CardNumber: "4111111111111111",
    Holder: "NOME NO CARTAO",
    ExpirationDate: "12/2027",  // sempre MM/YYYY (4 dígitos no ano)
    SecurityCode: "123",
    InstallmentQuantity: 1,
  },
  Customer: { Name, Identity: cpf, Email, Address },
  Products: [{ Code, Description, UnitPrice, Quantity: 1 }]
}
```

**Produção** — tokeniza primeiro, depois cobra com token:

**Passo 1 — Tokenizar:**
```typescript
POST /v2/token
{
  Holder: "NOME NO CARTAO",
  CardNumber: "4111111111111111",
  ExpirationDate: "12/2027",
  SecurityCode: "123"
}
// Retorno: { ResponseDetail: { Token: "abc123..." } }
```

**Passo 2 — Cobrar com token:**
```typescript
POST /v2/payment
{
  IsSandbox: false,
  Application: "{NomeProjeto}",
  Vendor: "{NomeProjeto}",
  Reference: "assinatura-{timestamp}",
  Description: "{descricao}",
  PaymentMethod: "2",
  PaymentObject: {
    Token: "{token_obtido_acima}",
    InstallmentQuantity: 1,
  },
  Customer: { Name, Identity: cpf, Email, Address },
  Products: [{ Code, Description, UnitPrice, Quantity: 1 }]
}
```

**Status aprovados:** `"3"` e `"4"` em `ResponseDetail.Status`.

**Retorno do método:**
```typescript
interface ResultadoProcessamento {
  token: string | null;      // null em sandbox
  transactionId: string;
}
```

### 5.3 Método: `cobrarComToken` (recorrência de cartão)

Usado pelo cron diário para cobranças recorrentes. O token já está armazenado e criptografado.

```typescript
POST /v2/payment
{
  IsSandbox: false,  // sempre produção (token não funciona em sandbox)
  Application: "{NomeProjeto}",
  Vendor: "{NomeProjeto}",
  Reference: "recorrencia-{timestamp}",
  Description: "{descricao}",
  PaymentMethod: "2",
  PaymentObject: {
    Token: "{token_descriptografado}",
    InstallmentQuantity: 1,
  },
  Customer: { Name, Identity: cpf, Email, Address },
  Products: [{ Code: "ASSINATURA_RECORRENTE", Description, UnitPrice, Quantity: 1 }]
}
// Retorno: { ResponseDetail: { IdTransaction: "...", Status: "3" } }
```

### 5.4 Método: `gerarPix` (PIX avulso/único)

Para situações onde se quer gerar um PIX único, sem autorização de débito automático.

```typescript
POST /v2/payment
{
  IsSandbox: false,
  Application: "{NomeProjeto}",
  Vendor: "{NomeProjeto}",
  Reference: "pix-{timestamp}",
  Description: "{descricao}",
  Amount: 99.90,  // valor em reais (não centavos!)
  PaymentMethod: "10",  // PIX
  PaymentObject: {
    DueDate: "DD/MM/YYYY",  // 3 dias de prazo
  },
  Customer: { Name, Identity: cpf_ou_cnpj, Email, Address },
  Products: [{ Code: "ASSINATURA_PIX", Description, UnitPrice, Quantity: 1 }]
}
// Retorno: { ResponseDetail: { QrCode, QrCodeImage, IdTransaction } }
```

### 5.5 Método: `criarAutorizacaoPix` (PIX Automático recorrente)

**Atenção:** Requer endereço completo e CNPJ da empresa pagadora.

```typescript
POST /v3/pix/automatic/authorizations
{
  Application: "{NomeProjeto}",
  Contract: {
    Description: "{descricao}",
    Name: "{descricao}",
    Customer: {
      Identity: "12345678000190",  // CNPJ sem máscara
      Name: "{nomeCliente}",
      Email: "{email}",
      Phone: "51999999999",
      Address: {
        ZipCode: "90000000",
        Street: "Rua Exemplo",
        Number: "100",
        Complement: "Sala 1",
        District: "Centro",
        StateInitials: "RS",
        CityName: "Porto Alegre",
        CountryName: "Brasil",
      },
    },
  },
  Calendar: {
    StartDate: "YYYY-MM-DD",       // hoje
    Periodicity: "MENSAL",         // "MENSAL" | "ANUAL"
    RetryPolicy: "PERMITE_3R_7D",  // 3 tentativas em 7 dias
  },
  Amount: {
    Fixed: 99.90,  // valor fixo recorrente em reais
  },
  ImmediatePayment: {
    Amount: 99.90,  // primeira cobrança imediata
    Reference: "{descricao}",
  },
}
```

**Retorno:**
```typescript
{
  data: {
    id: "autorizacaoId",         // guardar em assinaturas.pix_autorizacao_id
    status: "CRIADA",            // CRIADA → APROVADA via webhook
    immediatePayment: {
      idTransaction: "txId",     // guardar em pix_pendente_transaction_id
    },
    qrData: {
      pixCopyAndPaste: "00020...",  // EMV string para exibir ao usuário
      qrCode: "base64img",          // imagem base64
    },
    deepLink: "pix://...",
  }
}
```

**Estados da autorização:**
- `CRIADA` — aguardando pagamento do usuário
- `APROVADA` / `ATIVA` — autorização confirmada (webhook)
- `CANCELADA` / `EXPIRADA` — autorização não concluída

### 5.6 Método: `criarAgendamentoPix`

Chamado pelo cron 3-5 dias antes do vencimento para cada cobrança pendente.

```typescript
POST /v3/pix/automatic/authorizations/{autorizacaoId}/chargeSchedules
{
  Application: "{NomeProjeto}",
  Reference: "pix-schedule-{autorizacaoId}-{timestamp}",
  Calendar: {
    DueDate: "YYYY-MM-DD",
  },
  Amount: 99.90,
  AdditionalInformation: "{descricao}",
}
// Retorno: { data: { id: "agendamentoId", status: "CRIADA" } }
```

Guardar `agendamentoId` em `assinatura_cobranca.pix_agendamento_id`.

### 5.7 Método: `cancelarAutorizacaoPix`

```typescript
DELETE /v3/pix/automatic/authorizations/{autorizacaoId}
Headers: { X-API-KEY: "{apiKey}" }
```

### 5.8 Método: `criarLinkCobranca` (fallback)

Usado quando a cobrança automática de cartão falha. Gera link de pagamento que aceita cartão e PIX.

```typescript
POST https://api.safe2pay.com.br/v2/singleSale/add
{
  IsSandbox: false,
  Reference: "link-cobranca-{cobrancaId}",  // CRÍTICO: usado para lookup no webhook
  CallbackUrl: "https://api.{seudominio}/api/webhooks/link-cobranca",
  PaymentMethods: [
    { CodePaymentMethod: "2" },  // cartão
    { CodePaymentMethod: "6" },  // PIX
  ],
  Customer: { Name, Identity: cnpj_ou_cpf, Email, Address },
  Products: [{ Description, UnitPrice, Quantity: 1 }],
  Emails: ["{email}"],
  ExpirationDate: "DD/MM/YYYY",  // 30 dias
}
// Retorno: { ResponseDetail: { SingleSaleUrl: "https://..." } }
```

### 5.9 Estrutura Address (padrão para todos os métodos)

```typescript
{
  ZipCode: "90000000",       // CEP sem máscara (8 dígitos)
  Street: "Rua Exemplo",
  Number: "100",
  Complement: "Sala 1",      // opcional, pode ser ""
  District: "Centro",
  StateInitials: "RS",       // sigla 2 letras
  CityName: "Porto Alegre",
  CountryName: "Brasil",
}
```

**Fallback quando endereço não informado:** `ZipCode: "00000000"`, `Street: "Nao informado"`, `Number: "0"`, `District: "Nao informado"`, `StateInitials: "SP"`, `CityName: "Sao Paulo"`.

### 5.10 Tratamento de erros da API

A API retorna `HasError: true` em caso de erro. Verificar também `!res.ok`.

```typescript
if (!res.ok || data?.HasError) {
  const msg = data?.Error || data?.Message || data?.message || `HTTP ${res.status}`;
  throw new Error(msg);
}
```

---

## 6. Fluxos de Assinatura

### 6.1 Ativação com Cartão

```
1. Frontend envia { planoId, periodo: 'mensal'|'anual', metodoPagamento: 'cartao',
                    cartaoCriptografado: "base64rsa...", cpfCliente: "11122233344" }

2. Backend:
   a. Descriptografa cartão com RSA_PRIVATE_KEY
   b. Valida CPF (11 dígitos)
   c. Calcula valor: plano.preco * 1 (mensal) ou plano.preco * 10 (anual — 2 meses grátis)
   d. Chama safe2pay.processarCartao() → { token, transactionId }
   e. Chama encryptToken(token) → safe2payToken
   f. Atualiza assinatura:
      status = 'active'
      cicloCobranca = 'mensal'|'anual'
      metodoPagamento = 'cartao'
      valor = valorTotal
      dtAssinatura = now()
      dtVencimento = calcularProximoVencimento(now(), ciclo)
      safe2payToken = encrypted
      documentoCobranca = cpfLimpo
      trialTerminaEm = null
   g. Registra cobranças:
      - Cobrança inicial: situacao=1 (paga), transactionId
      - Próxima cobrança: situacao=0 (aberta), dtVencimento = dtVencimento da assinatura

3. Retorna assinatura ativa (sem safe2payToken)
```

**Cálculo do valor anual:** `preco_mensal * 10` (equivalente a 2 meses grátis).

### 6.2 Ativação com PIX Automático

```
1. Frontend envia { planoId, periodo, metodoPagamento: 'pix' }
   (empresa deve ter CNPJ e endereço completo cadastrado)

2. Backend:
   a. Busca empresa → valida CNPJ e endereço completo
   b. Chama safe2pay.criarAutorizacaoPix() → { autorizacaoId, immediateTransactionId, qrCode, ... }
   c. Salva na assinatura (status permanece como estava — NÃO ativa ainda):
      pixPendentePlanoId = planoId
      pixPendentePeriodo = periodo
      pixPendenteValor = valorTotal
      pixPendenteTransactionId = immediateTransactionId || autorizacaoId
      pixAutorizacaoId = autorizacaoId
      pixAutorizacaoStatus = 'CRIADA'
      pixQrCode = qrCode
      pixQrCodeBase64 = base64
      pixDeepLink = deepLink
   d. Cria cobrança inicial: situacao=0, transactionId=pixPendenteTransactionId

3. Retorna QR code para o usuário pagar

4. [usuário escaneia e paga]

5. Safe2Pay dispara webhook POST /webhooks/pix/autorizacao
   → Backend ativa a assinatura (ver seção 8.1)
```

### 6.3 Registro de cobranças (`registrarCobrancasAssinatura`)

Ao ativar por cartão, registra sempre **2 cobranças**:

```typescript
// Cobrança inicial (já paga)
{
  assinaturaId: ass.id,
  dtVencimento: new Date(),  // hoje
  valor: ass.valor,
  situacao: 1,               // pago
  transactionId: transactionId,
}

// Próxima cobrança (aberta)
{
  assinaturaId: ass.id,
  dtVencimento: ass.dtVencimento,  // próximo mês/ano
  valor: ass.valor,
  situacao: 0,
}
```

### 6.4 Cálculo do próximo vencimento

```typescript
function calcularProximoVencimento(base: Date, ciclo: string): Date {
  const proximo = new Date(base);
  if (ciclo === 'anual') {
    proximo.setFullYear(proximo.getFullYear() + 1);
    return proximo;
  }
  proximo.setMonth(proximo.getMonth() + 1);
  return proximo;
}
```

---

## 7. Cron Diário de Cobrança

**Endpoint:** `POST /api/cron/processar-cobrancas`
**Auth:** `Authorization: Bearer {CRON_API_KEY}`
**Frequência:** Diária (configurar no hosting ou cron externo)

**Proteção contra execução paralela:** flag `executando` em memória.

### 7.1 Sequência de execução

```
processarCobrancasDoDia()
  │
  ├── 1. Busca cobranças abertas (situacao=0) com dtVencimento = hoje
  │      Para cada cobrança com metodoPagamento = 'cartao':
  │         processarCobrancaCartao(cobranca, assinatura)
  │
  ├── 2. processarCancelamentosFimPeriodo()
  │      Cancela assinaturas com cancelaNoFimPeriodo=true e dtVencimento <= hoje
  │
  ├── 3. agendarCobrancasPix()
  │      Busca cobranças abertas com vencimento em 3-5 dias E pix_agendamento_id IS NULL
  │      Para assinaturas pix + pixAutorizacaoStatus='APROVADA':
  │         criarAgendamentoPix() → salva pixAgendamentoId
  │      IDEMPOTÊNCIA: uma vez agendado, o pix_agendamento_id preenchido faz o cron
  │      ignorar a cobrança nos dias seguintes (dia 4, 5) — sem agendamento duplicado
  │
  └── 4. sincronizarStatusInadimplencia()
         Para todas assinaturas 'active' ou 'blocked':
           Calcula diasAtraso da cobrança aberta mais antiga
           Aplica transição: active → blocked → cancelado
```

### 7.2 `processarCobrancaCartao` — fluxo detalhado

```typescript
// SUCESSO:
token = decryptToken(assinatura.safe2payToken)
resultado = await safe2pay.cobrarComToken({ token, valorCentavos, ... })
cobranca.situacao = 1
cobranca.transactionId = resultado.transactionId
assinatura.status = 'active'
assinatura.bloqueadaEm = null
assinatura.motivoBloqueio = null
assinatura.dtVencimento = calcularProximoVencimento(cobranca.dtVencimento, ciclo)
// cria próxima cobrança

// FALHA:
cobranca.situacao = 2
cobranca.linkPagamento = await safe2pay.criarLinkCobranca({
  reference: `link-cobranca-${cobranca.id}`,  // chave para lookup no webhook
  ...
})
// Não cria próxima cobrança — usuário precisa pagar pelo link
```

### 7.3 `sincronizarStatusInadimplencia`

```typescript
const diasAtraso = calcularDiasAtraso(cobrancaAbertaMaisAntiga?.dtVencimento, hoje)
const status = classificarStatusInadimplencia(diasAtraso)

// active → blocked (> 10 dias)
if (status === 'blocked' && assinatura.status === 'active') {
  assinatura.status = 'blocked'
  assinatura.bloqueadaEm = now()
  assinatura.motivoBloqueio = 'Bloqueio automático por inadimplência superior a 10 dias.'
}

// blocked → cancelado (> 20 dias)
if (status === 'cancelado' && assinatura.status !== 'cancelado') {
  assinatura.status = 'cancelado'
  assinatura.canceladaEm = now()
  assinatura.motivoCancelamento = 'Cancelamento automático por inadimplência superior a 20 dias.'
  // cancela todas cobranças abertas (situacao = 3)
}

// blocked → active (pagamento regularizado)
if (status === 'active' && assinatura.status === 'blocked') {
  assinatura.status = 'active'
  assinatura.bloqueadaEm = null
  assinatura.motivoBloqueio = null
}
```

---

## 8. Webhooks

### 8.1 `POST /webhooks/pix/autorizacao`

Disparado quando o status de uma autorização PIX Automático muda.

**Campos buscados no payload (flexível, aceita variações da API):**
```typescript
const autorizacaoId = payload?.data?.Id ?? payload?.Id
const status = (payload?.data?.Status ?? payload?.Status ?? '').toUpperCase()
// possíveis: 'APROVADA' | 'ATIVA' | 'CANCELADA' | 'EXPIRADA'
```

**Lógica quando `APROVADA` ou `ATIVA`:**
```typescript
// Ativa a assinatura
ass.status = 'active'
ass.planoId = planoId (do pixPendentePlanoId ou atual)
ass.cicloCobranca = pixPendentePeriodo
ass.metodoPagamento = 'pix'
ass.valor = pixPendenteValor
ass.dtAssinatura = now()
ass.dtVencimento = calcularProximoVencimento(now(), periodo)
ass.trialTerminaEm = null
ass.bloqueadaEm = null
ass.motivoBloqueio = null

// Marca cobrança inicial como paga
// Busca por: transactionId = pixPendenteTransactionId OU transactionId = autorizacaoId
cobranca.situacao = 1

// Limpa campos temporários
ass.pixPendentePlanoId = null
ass.pixPendentePeriodo = null
ass.pixPendenteValor = null
ass.pixPendenteTransactionId = null
ass.pixQrCode = null
ass.pixQrCodeBase64 = null
ass.pixDeepLink = null

// Cria próxima cobrança (se não existir)
INSERT assinatura_cobranca (assinaturaId, dtVencimento=ass.dtVencimento, valor, situacao=0)
```

**Lógica quando `CANCELADA` ou `EXPIRADA`:**
```typescript
// Cancela cobrança inicial
cobranca.situacao = 3
// Limpa QR code
ass.pixQrCode = null; ass.pixQrCodeBase64 = null; ass.pixDeepLink = null
```

### 8.2 `POST /webhooks/pix/agendamento`

Disparado quando um agendamento PIX conclui (cobrança executada).

**Campos buscados:**
```typescript
const agendamentoId = payload?.data?.AgendamentoId ?? payload?.AgendamentoId
                   ?? payload?.data?.ChargeScheduleId ?? payload?.ChargeScheduleId
                   ?? payload?.data?.id ?? payload?.id
const status = (payload?.data?.Status ?? payload?.Status ?? '').toUpperCase()
// possíveis: 'CONCLUIDA' | 'EXPIRADA' | 'REJEITADA' | 'CANCELADA'
```

**Lookup:** `assinatura_cobranca WHERE pix_agendamento_id = agendamentoId`.

**Lógica `CONCLUIDA`:**
```typescript
cobranca.situacao = 1
ass.status = 'active'
ass.bloqueadaEm = null
ass.motivoBloqueio = null
ass.dtVencimento = calcularProximoVencimento(cobranca.dtVencimento, ass.cicloCobranca)
// Cria próxima cobrança (se não existir)
```

**Lógica `EXPIRADA | REJEITADA | CANCELADA`:**
```typescript
cobranca.situacao = 2
// Inadimplência será detectada pelo cron
```

### 8.3 `POST /webhooks/link-cobranca`

Disparado quando o usuário paga pelo link de pagamento (fallback).

**Lookup — em ordem de prioridade:**
1. `reference` com formato `link-cobranca-{cobrancaId}` → busca por `id`
2. `transactionId` → busca por `transaction_id`

**Status que indicam pagamento:**
`'PAGO' | 'APROVADO' | 'APROVADA' | '3' | 'AUTORIZADO' | 'AUTHORIZED'`

**Lógica no pagamento:**
```typescript
cobranca.situacao = 1
ass.status = 'active'
ass.bloqueadaEm = null
ass.dtVencimento = calcularProximoVencimento(cobranca.dtVencimento, ciclo)
// Cria próxima cobrança
```

### 8.4 Boas práticas para webhooks

1. **Sempre logar** o payload completo em `webhook_logs` antes de processar
2. **Retornar `{ ok: true }` imediatamente** — processar de forma assíncrona
3. **Idempotência:** verificar `situacao` atual antes de marcar como pago (não re-processar)
4. **Flexibilidade de campos:** Safe2Pay pode variar nomenclatura entre versões — sempre extrair de múltiplos locais possíveis

```typescript
// Padrão para extração flexível de campos
private extractId(payload: any, ...fields: string[]): string {
  const raw = payload?.data ?? payload;
  for (const field of fields) {
    const val = raw?.[field] ?? payload?.[field];
    if (val) return String(val);
  }
  return '';
}
```

---

## 9. Guard de Assinatura Ativa

Aplicado como `APP_GUARD` global no `AppModule`.

```typescript
@Injectable()
export class AssinaturaAtivaGuard implements CanActivate {
  async canActivate(ctx: ExecutionContext): Promise<boolean> {
    const req = ctx.switchToHttp().getRequest();
    const token = req.headers.authorization?.replace('Bearer ', '');
    if (!token) return true;  // não autenticado → outro guard cuida

    const payload = this.jwt.verify(token, { secret: this.config.get('JWT_SECRET') });
    const empresaId = payload?.empresaId;
    if (!empresaId) return true;  // superadmin (sem empresaId) passa livre

    // Rotas marcadas com @SkipTrialCheck() passam livre
    const skip = this.reflector.getAllAndOverride<boolean>(SKIP_TRIAL_CHECK_KEY, [...]);
    if (skip) return true;

    const ass = await repo.findOne({ where: { empresaId }, order: { createdAt: 'DESC' } });
    if (!ass) throw new ForbiddenException('Nenhuma assinatura encontrada.');

    // Trial expirado
    if (ass.status === 'trial' && ass.trialTerminaEm && new Date(ass.trialTerminaEm) < new Date()) {
      throw new ForbiddenException('Seu período de teste expirou. Assine um plano para continuar.');
    }

    // Inadimplência (somente fora do trial)
    if (ass.status !== 'trial') {
      const cobranca = await cobrancaRepo.findOne({
        where: { assinaturaId: ass.id, situacao: 0 },
        order: { dtVencimento: 'ASC' },
      });
      const diasAtraso = calcularDiasAtraso(cobranca?.dtVencimento, new Date());
      const status = classificarStatusInadimplencia(diasAtraso);

      if (status === 'blocked') throw new ForbiddenException('Sua assinatura está bloqueada por inadimplência...');
      if (status === 'cancelado') throw new ForbiddenException('Sua assinatura foi cancelada por inadimplência...');
    }

    return true;
  }
}
```

**Rotas que devem usar `@SkipTrialCheck()`:**
- Login, registro, recuperação de senha
- Endpoint de assinatura (`/api/empresas/assinar`)
- Confirmação de PIX
- Webhooks
- Listagem de planos

---

## 10. Lógica de Inadimplência

```typescript
export const ASSINATURA_DIAS_GRACA_BLOQUEIO = 10;
export const ASSINATURA_DIAS_GRACA_CANCELAMENTO = 20;

const MS_DIA = 1000 * 60 * 60 * 24;

function inicioDoDia(data: Date) {
  return new Date(data.getFullYear(), data.getMonth(), data.getDate(), 0, 0, 0, 0);
}

// Dias de atraso baseado na cobrança aberta mais antiga
export function calcularDiasAtraso(vencimento?: Date | string | null, referencia = new Date()): number {
  if (!vencimento) return 0;
  const venc = inicioDoDia(new Date(vencimento));
  const ref = inicioDoDia(referencia);
  const diff = Math.floor((ref.getTime() - venc.getTime()) / MS_DIA);
  return Math.max(0, diff);
}

// Status calculado vs. status real no banco
export function classificarStatusInadimplencia(diasAtraso: number): string {
  if (diasAtraso > ASSINATURA_DIAS_GRACA_CANCELAMENTO) return 'cancelado';  // > 20 dias
  if (diasAtraso > ASSINATURA_DIAS_GRACA_BLOQUEIO) return 'blocked';        // > 10 dias
  return 'active';
}

// Datas úteis para exibição
export function calcularDataBloqueio(vencimento?: Date | string | null): Date | null {
  if (!vencimento) return null;
  const data = inicioDoDia(new Date(vencimento));
  data.setDate(data.getDate() + ASSINATURA_DIAS_GRACA_BLOQUEIO + 1);
  return data;  // vencimento + 11 dias
}

export function calcularDataCancelamento(vencimento?: Date | string | null): Date | null {
  if (!vencimento) return null;
  const data = inicioDoDia(new Date(vencimento));
  data.setDate(data.getDate() + ASSINATURA_DIAS_GRACA_CANCELAMENTO + 1);
  return data;  // vencimento + 21 dias
}
```

### Resumo das transições

| Dias de atraso | Status calculado | Ação do cron |
|----------------|-----------------|--------------|
| 0–10 | `active` | Nenhuma |
| 11–20 | `blocked` | Bloqueia acesso ao sistema |
| > 20 | `cancelado` | Cancela assinatura + cobra abertas canceladas |

---

## 11. Variáveis de Ambiente

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `SAFE2PAY_API_KEY` | Sim | Chave de API da Safe2Pay |
| `SAFE2PAY_SANDBOX` | Sim | `"true"` ou `"false"` |
| `DB_TOKEN_ENCRYPT_KEY` | Sim | 64 chars hex (32 bytes) para AES-256-GCM do token de cartão |
| `RSA_PRIVATE_KEY` | Sim | PEM ou base64(PEM) — descriptografar dados do frontend |
| `RSA_PUBLIC_KEY` | Sim | PEM ou base64(PEM) — exposto ao frontend via GET |
| `CRON_API_KEY` | Sim | Bearer token para `/api/cron/processar-cobrancas` |
| `JWT_SECRET` | Sim | Segredo JWT |
| `MSG_ENCRYPTION_KEY` | Opcional | 64 chars hex — para criptografar outras colunas (encryptedTransformer) |

**Geração de chaves seguras:**
```bash
# DB_TOKEN_ENCRYPT_KEY / MSG_ENCRYPTION_KEY
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"

# CRON_API_KEY
node -e "console.log(require('crypto').randomBytes(32).toString('base64url'))"

# Par RSA
openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -pubout -out public.pem
# Para .env em linha única:
base64 -w 0 private.pem
base64 -w 0 public.pem
```

---

## 12. Rotas e Endpoints

### Públicas (sem autenticação)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/planos` | Lista planos ativos |
| GET | `/auth/pagamento/chave-publica` | Retorna RSA_PUBLIC_KEY para o frontend |

### Webhooks (sem autenticação, chamadas pelo Safe2Pay)

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/webhooks/pix/autorizacao` | Status de autorização PIX Automático |
| POST | `/api/webhooks/pix/agendamento` | Conclusão de agendamento PIX |
| POST | `/api/webhooks/link-cobranca` | Pagamento via link de cobrança |
| GET | `/api/webhooks/pix/logs` | Debug — últimos 100 logs (`?tipo=autorizacao\|agendamento\|link-cobranca`) |

### Autenticadas (empresa logada) — usar `@SkipTrialCheck()` nos de pagamento

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/empresas/assinatura` | Detalhes da assinatura atual + inadimplência |
| GET | `/api/empresas/pagamentos` | Histórico de cobranças |
| POST | `/api/empresas/assinar` | Ativar plano (cartão ou PIX) |
| POST | `/api/empresas/pix/confirmar/:transactionId` | Confirmar PIX manualmente (fallback) |
| PUT | `/api/empresas/assinatura/extras` | Atualizar add-ons (usuários, canais extras) |
| POST | `/api/empresas/assinatura/migrar` | Propor mudança de plano |
| POST | `/api/empresas/assinatura/confirmar-upgrade` | Confirmar upgrade |
| POST | `/api/empresas/assinatura/confirmar-downgrade` | Confirmar downgrade |
| POST | `/api/empresas/assinatura/cancelar` | Cancelar assinatura |
| POST | `/api/empresas/pagamentos/:id/gerar-link` | Gerar link de pagamento para cobrança |

### Cron (Bearer CRON_API_KEY)

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/cron/processar-cobrancas` | Execução diária do ciclo de cobrança |

### Superadmin

| Método | Rota | Descrição |
|--------|------|-----------|
| GET/POST | `/superadmin/planos` | Listar/criar planos |
| PUT | `/superadmin/planos/:id` | Atualizar plano |
| GET/POST/PUT/DELETE | `/superadmin/planos/:id/promocoes` | Gerenciar promoções |

---

## 13. Considerações de Segurança

### Dados sensíveis
- **Dados do cartão:** nunca trafegam em texto puro. Frontend → RSA-OAEP → Backend → Safe2Pay token
- **Token Safe2Pay:** armazenado apenas em AES-256-GCM. Decriptografado somente durante o cron
- **API Key Safe2Pay:** apenas variável de ambiente, nunca no código ou logs
- **CRON_API_KEY:** rotacionar periodicamente; use Bearer token forte (32+ bytes aleatórios)

### O que **nunca** deve aparecer em logs
- Número de cartão, CVV, validade
- `safe2pay_token` descriptografado
- `SAFE2PAY_API_KEY`, `DB_TOKEN_ENCRYPT_KEY`, `RSA_PRIVATE_KEY`

### Webhook — validação futura (recomendada)
A Safe2Pay pode fornecer HMAC-SHA256 de validação. Quando disponível:
```typescript
const expected = crypto
  .createHmac('sha256', process.env.WEBHOOK_SECRET)
  .update(rawBody)
  .digest('hex');
if (req.headers['x-safe2pay-signature'] !== expected) throw new UnauthorizedException();
```

### Sandbox vs Produção
- Em sandbox: **token não é retornado** — cobrança direta com dados raw (aceito pela Safe2Pay em sandbox)
- Em sandbox: cobranças recorrentes com token **não funcionam** — só em produção
- `IsSandbox: false` sempre na cobrança com token e no link de cobrança (mesmo quando `SAFE2PAY_SANDBOX=true`)

---

## 14. Guia de Adaptação para Novos Projetos

### Checklist de implementação

```
[ ] 1. Banco de dados
       - Criar tabelas: assinaturas, assinatura_cobranca, planos, webhook_logs
       - Adaptar FK empresa_id para a entidade "tenant" do projeto (user, organization, etc.)

[ ] 2. Criptografia
       - Copiar crypto.util.ts (encryptToken, decryptToken, rsaDecrypt)
       - Gerar DB_TOKEN_ENCRYPT_KEY e par RSA
       - Endpoint GET /auth/pagamento/chave-publica

[ ] 3. Safe2PayService
       - Copiar safe2pay.service.ts
       - Substituir "Converzas" por nome do projeto nas strings
       - Atualizar CallbackUrl no criarLinkCobranca para domínio do projeto

[ ] 4. assinatura-status.util.ts
       - Copiar sem alterações (lógica genérica)

[ ] 5. Fluxo de assinatura (empresas.service.ts → adaptar)
       - método assinar() — lógica cartão + pix
       - método confirmarPagamentoPix()
       - método registrarCobrancasAssinatura()

[ ] 6. Cron (assinatura-cobranca-cron.service.ts)
       - Copiar e adaptar getNomeCliente() para modelo do projeto
       - Adaptar cancelarCobrancasAbertas() se precisar de cleanup adicional

[ ] 7. Webhooks (webhooks.service.ts + webhooks.controller.ts)
       - Copiar sem alterações significativas
       - Registrar URLs no painel Safe2Pay:
         POST {dominio}/api/webhooks/pix/autorizacao
         POST {dominio}/api/webhooks/pix/agendamento
         POST {dominio}/api/webhooks/link-cobranca

[ ] 8. Guard (assinatura-ativa.guard.ts)
       - Copiar e adaptar campo JWT (empresaId → tenantId, etc.)
       - Marcar rotas públicas com @SkipTrialCheck()
       - Registrar como APP_GUARD no AppModule

[ ] 9. Variáveis de ambiente
       - SAFE2PAY_API_KEY, SAFE2PAY_SANDBOX
       - DB_TOKEN_ENCRYPT_KEY (gerar novo para cada projeto!)
       - RSA_PRIVATE_KEY, RSA_PUBLIC_KEY (gerar novo par para cada projeto!)
       - CRON_API_KEY
```

### Pontos de adaptação obrigatórios

| Ponto | O que adaptar |
|-------|--------------|
| FK `empresa_id` | Renomear para `user_id`, `org_id`, etc. conforme modelo do projeto |
| JWT payload | Campo `empresaId` → nome correto para o tenant |
| `getNomeCliente()` | Adaptar para buscar nome do pagador no modelo do projeto |
| `criarLinkCobranca.CallbackUrl` | Substituir domínio |
| Strings "Converzas" | Substituir por nome do projeto em todos os payloads Safe2Pay |
| `cancelarCobrancasAbertas` | Adicionar cleanup específico (ex: desativar canais, remover usuários) |
| Plano "anual = 10x" | Ajustar fórmula de desconto anual conforme política do projeto |

### Pontos que **não mudam**

- Toda a lógica de criptografia (AES-256-GCM + RSA-OAEP)
- Todos os endpoints Safe2Pay e seus payloads
- Lógica de inadimplência (10 dias → blocked, 20 dias → cancelado)
- Estrutura das tabelas `assinaturas` e `assinatura_cobranca`
- Sequência de webhooks e seus campos
- Guard de assinatura ativa

---

## Apêndice — Diagrama de Estados da Assinatura

```
                    [criar empresa]
                         │
                         ▼
                      [trial]
                    trialTerminaEm
                         │
              ┌──────────┴──────────┐
              │                     │
         [expirou]             [assinou]
              │                     │
              ▼                     ▼
     ForbiddenException          [active]
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
              [10 dias sem      [pagou         [cancelou
               pagamento]       ontime]      voluntário]
                    │               │               │
                    ▼               │               ▼
                [blocked]           │       cancelaNoFimPeriodo=true
              ForbiddenEx.          │       (fica active até fim período)
                    │               │               │
              [10 dias mais]    [volta ao]    [cron detecta
                    │            active]      fim período]
                    ▼                               │
                [cancelado] ◄───────────────────────┘
              ForbiddenEx.
```

---

## Apêndice — Mapa de Arquivos (referência `converzas-api`)

| Arquivo | Descrição |
|---------|-----------|
| `src/entities/assinatura.entity.ts` | Entidade ORM da assinatura |
| `src/entities/assinatura-cobranca.entity.ts` | Entidade ORM da cobrança |
| `src/entities/plano.entity.ts` | Entidade ORM do plano |
| `src/entities/webhook-log.entity.ts` | Entidade ORM do log de webhook |
| `src/modules/pagamentos/safe2pay.service.ts` | Cliente completo Safe2Pay |
| `src/modules/pagamentos/assinatura-cobranca-cron.service.ts` | Cron diário de cobrança |
| `src/modules/pagamentos/pagamentos.controller.ts` | Endpoint do cron |
| `src/modules/webhooks/webhooks.service.ts` | Processamento de webhooks |
| `src/modules/webhooks/webhooks.controller.ts` | Rotas de webhook |
| `src/modules/empresas/empresas.service.ts` | Lógica de ativação/migração |
| `src/common/guards/assinatura-ativa.guard.ts` | Guard global de acesso |
| `src/common/utils/assinatura-status.util.ts` | Cálculo de inadimplência |
| `src/common/utils/crypto.util.ts` | AES-256-GCM + RSA-OAEP |
