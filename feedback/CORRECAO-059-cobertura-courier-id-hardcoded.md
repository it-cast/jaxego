# Correção 059 — Tela de Bairros & Preços usava courierId=1 hardcoded

> **Classe:** COD · **Data:** 2026-06-19

---

## Arquivo afetado

- `apps/app/src/features/entregador/cobertura-precos/cobertura-precos.page.ts`

## Problema

A tela de "Bairros e preços" usava `courierId = 1` hardcoded (placeholder do M1). O courier logado (ex: id=14) fazia PUT em `/v1/couriers/1/coverage` e `/v1/couriers/1/pricing`, resultando em 404 ou salvando para o courier errado.

Erro visível: "Não conseguimos salvar. Tente de novo em instantes."

## Correção

`courierId` agora vem de `AuthService.me()?.courier_id` (resolvido do JWT/session). Cada entregador salva nos seus próprios endpoints.
