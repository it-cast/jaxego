# docs-externos/

**Documentação de APIs, integrações e fornecedores externos.**

## O que jogar aqui

- Docs de APIs que você vai integrar
- Manuais de fornecedores / parceiros
- Especificações técnicas de terceiros
- Postman collections
- OpenAPI specs
- Tabelas de erros de gateways de pagamento, KYC, etc.

## Formatos aceitos

`.md`, `.pdf`, `.html`, `.json` (OpenAPI), `.yaml`, `.docx`

## Exemplos

```
safe2pay-api-v2.pdf
idwall-webhook-spec.md
twilio-messaging-quickstart.md
pagarme-postman.json
asaas-rate-limits.txt
b2-backblaze-storage.pdf
```

## Por que isso importa

Quando Claude gera `REQUIREMENTS.md`, ele cita evidência. Se você integra Safe2Pay, ter o PDF da API aqui faz Claude gerar requirements precisos como:

> REQ-042: Split de pagamento via Safe2Pay
> Evidência: `projeto/docs-externos/safe2pay-api-v2.pdf` páginas 23-31
> Critério de aceite: campo `split_id` obrigatório, %integer, soma=100

Em vez de inventar.

## O que NÃO jogar aqui

- Sua própria stack (vai em `stacks/`)
- ADRs internos sobre como você decidiu usar (vai em `decisoes-existentes/`)
