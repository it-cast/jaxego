# Correção 056 — Cadastro de loja usa área explícita

> **Classe:** COD/UX · **Data:** 2026-06-19

---

## Arquivos afetados

- `apps/api/app/merchants/schemas.py`
- `apps/api/app/merchants/service.py`
- `apps/web/src/features/loja/cadastro/cadastro.page.ts`
- `apps/web/src/features/loja/cadastro/cadastro.page.html`
- `apps/web/src/features/loja/cadastro/merchant.models.ts`
- `apps/web/src/features/loja/cadastro/merchant.service.ts`
- `apps/api/tests/merchants/test_signup.py`
- `apps/api/tests/merchants/test_uniqueness.py`
- `apps/api/tests/workers/test_revalidate_receita.py`

## Problema

O cadastro de restaurante podia exibir "Ainda não chegamos na sua cidade" mesmo para
cidades cadastradas em `areas`.

O backend tentava descobrir a área geocodificando `trade_name` (nome da loja) e depois
comparando o ponto com `area.config["bbox"]`. Além disso, existia um fallback hardcoded
para o codename `padua`, que não atendia áreas reais cadastradas com outros codenames,
como `santo-antonio-padua`.

## Correção

- O cadastro de loja agora carrega `GET /v1/areas/public`
- O passo de endereço exibe um select de "Cidade atendida"
- O frontend envia `area_id` no `POST /v1/merchants/signup`
- O backend valida diretamente se a área existe e está ativa
- O fluxo de cadastro deixou de depender de geocoding por nome da loja e de fallback
  hardcoded de bbox para decidir cobertura
- Testes diretos do contrato de signup foram atualizados para incluir `area_id`

## Resultado esperado

Ao cadastrar uma loja em uma área ativa, como Santo Antônio de Pádua ou Aperibé, o
cadastro vincula a loja ao `area_id` escolhido e não exibe o estado de cidade sem
cobertura por falha de geocodificação/hardcode.
