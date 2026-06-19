# Correção 055 — Cadastro do entregador com KYC simples

> **Classe:** COD/UI · **Data:** 2026-06-19

---

## Arquivos afetados

- `apps/api/app/areas/router.py`
- `apps/api/tools/seed.py`
- `apps/app/src/features/entregador/cadastro/cadastro.page.ts`

## Problema

O cadastro do entregador podia entrar em estado inconsistente ao selecionar uma cidade
com validação simplificada.

Havia dois pontos frágeis:

- A lista pública `GET /v1/areas/public` devolvia o `kyc_level` cru da configuração da área. O seed de dev ainda usava o valor legado `basico`, enquanto o contrato atual aceita apenas `simples` ou `completa`.
- O wizard inicializava a lista de documentos apenas uma vez. Se o nível de KYC mudasse ao trocar de cidade, os documentos exibidos/enviados podiam ficar presos ao nível anterior.

## Correção

- `GET /v1/areas/public` agora normaliza qualquer valor diferente de `completa` para `simples`
- Seed de dev atualizado de `basico` para `simples`
- App do entregador normaliza defensivamente o `kyc_level` recebido da API
- Wizard recria a lista de documentos quando a cidade/nível muda, preservando arquivos já escolhidos para documentos que continuam válidos, como a selfie

## Resultado esperado

Ao escolher uma cidade com `kyc_level` simples, o cadastro solicita apenas a selfie como
documento obrigatório de imagem e finaliza sem carregar estado legado ou documentos de
validação completa.
