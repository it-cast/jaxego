# Correção 003 — Frontend rodando com Angular CLI em vez de Ionic CLI

> **Classe:** INFRA · **Data:** 2026-06-15

---

## Arquivo afetado

- `apps/web/package.json`

## Problema

O script `start` usava `ng serve` (Angular CLI, porta 4200). O projeto é Ionic + Angular Standalone com Capacitor e deve rodar com `ionic serve` na porta 8100.

## Correção

Alterado o script `start` de `ng serve` para `ionic serve`. Ambos passam `--proxy-config proxy.conf.json` para rotear `/v1/*` para a API em `localhost:8000`.
