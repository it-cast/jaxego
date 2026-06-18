# Correção 039 — Upload de selfie bloqueado por CORS: URL absoluta cruzava origens

> **Classe:** COD · **Data:** 2026-06-18 · **Relacionada:** Correção 038

---

## Arquivo afetado

- `apps/api/app/integrations/storage_stub.py`

## Problema

Após a Correção 038, o stub retornava URL absoluta `http://localhost:8000/v1/dev/upload/...`. O frontend em `localhost:8100` fazia PUT direto para `localhost:8000`, gerando erro CORS: `No 'Access-Control-Allow-Origin' header is present`.

## Correção

URL alterada de absoluta para relativa: `/v1/dev/upload/{key}`. O `HttpClient` do Angular resolve como `http://localhost:8100/v1/dev/upload/...`, que passa pelo proxy do Ionic dev server (`proxy.conf.json: /v1 → localhost:8000`). Sem cross-origin, sem CORS.
