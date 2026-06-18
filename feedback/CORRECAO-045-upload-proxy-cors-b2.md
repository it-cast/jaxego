# Correção 045 — Upload direto para B2 bloqueado por CORS: migrado para proxy via API

> **Classe:** INFRA/COD · **Data:** 2026-06-18 · **Relacionada:** Correções 038, 039

---

## Arquivos afetados

- `apps/api/app/dev_upload.py` (renomeado para upload proxy genérico)
- `apps/api/app/main.py`
- `apps/api/app/integrations/storage.py`
- `apps/api/app/integrations/storage_stub.py`

## Problema

O browser fazia PUT direto para `https://s3.us-west-004.backblazeb2.com/...` (presigned URL do B2). O B2 não respondia ao preflight OPTIONS com CORS headers, bloqueando o upload: `No 'Access-Control-Allow-Origin' header`. Configurar CORS rules no bucket B2 para PUT com S3-compatible API não funcionou.

## Correção

Abordagem alterada: o frontend nunca mais faz upload direto para o B2. O fluxo agora é:

1. Frontend recebe presigned URL relativa: `/v1/upload/{key}`
2. Frontend faz `PUT /v1/upload/{key}` (passa pelo proxy do dev server → chega na API)
3. API recebe o arquivo e chama `storage.put_bytes()` (B2 em prod, filesystem em dev)

Mudanças:
- `StorageB2Adapter.presign_put()` retorna URL relativa `/v1/upload/{key}` em vez da URL absoluta do B2
- `StorageStubAdapter.presign_put()` também usa `/v1/upload/{key}` (consistência)
- Endpoint `/v1/upload/{key:path}` registrado sempre (não só em dev)
- Sem CORS envolvido — tudo passa pelo mesmo domínio

## Trade-off

O arquivo transita pelo backend (upload proxy), o que consome bandwidth da API. Em produção com volume alto, pode ser migrado para upload direto com CORS configurado no CDN/Cloudflare R2, mas para o MVP o proxy é suficiente e evita o problema de CORS do B2.
