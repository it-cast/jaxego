---
name: stack-advisor
description: Conselheiro de stack para novos projetos brasileiros. Recomenda tecnologias baseado no tipo de produto. NÃO aplicável ao {PROJETO} (stack já definida).
type: meta
---

# Skill: Stack Advisor

> Apenas para NOVOS projetos. {PROJETO} tem stack fixa — não usar aqui.

---

## Matriz de decisão de stack

| Produto | Frontend Mobile | Frontend Web/Admin | Backend | Banco | Pagamento BR |
|---|---|---|---|---|---|
| Marketplace de serviços | Ionic 8 + Angular 19 | Angular 19 + Material | FastAPI + SQLAlchemy | MySQL 8 | {gateway-pagamento} |
| App B2C simples | Ionic 8 + Angular 19 | — | FastAPI | MySQL 8 | {gateway-pagamento} ou Pagar.me |
| SaaS admin-heavy | — | Angular 19 + Material | FastAPI | MySQL 8 | Stripe (se global) |
| E-commerce BR | Ionic 8 ou React Native | Next.js | FastAPI ou NestJS | MySQL 8 | {gateway-pagamento} / Pagar.me |
| App de saúde/fitness | Ionic 8 + Angular 19 | Angular 19 | FastAPI | PostgreSQL | — |
| Dashboard analítico | — | Angular 19 + Material | FastAPI | PostgreSQL + Redis | — |

---

## Regras para mercado brasileiro

**Sempre:**
- Gateway de pagamento BR-native: {gateway-pagamento}, Pagar.me, ou Gerencianet (não Stripe como principal)
- CPF/CNPJ validation: `@brazilian-utils` (npm)
- CEP lookup: ViaCEP API (gratuita)
- Charset: UTF-8 com suporte a acentos desde o primeiro dia
- LGPD: modelar consentimento desde o schema inicial

**Evitar:**
- Stripe como gateway principal (sem Pix nativo)
- AWS Cognito como auth (caro, complexo para startups BR)
- MongoDB para dados relacionais com muitos joins
- GraphQL para MVP (over-engineering)

---

## Stack {PROJETO} (referência — não alterar)

```
Mobile:  Ionic 8 + Angular 19 + Capacitor
Admin:   Angular 19 standalone + Material 3
API:     FastAPI + SQLAlchemy 2.0 async + Alembic
Banco:   MySQL 8 + Redis 7
Storage: Backblaze B2 (S3-compatible)
Payment: {gateway-pagamento} (escrow, Pix, Cartão)
Infra:   Docker Compose + Nginx + VPS Hostinger
```
