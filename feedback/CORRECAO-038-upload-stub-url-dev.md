# Correção 038 — Upload de selfie falhava em dev: URL stub:// não é fetchável pelo browser

> **Classe:** INFRA/COD · **Data:** 2026-06-18

---

## Arquivos afetados

- `apps/api/app/integrations/storage_stub.py`
- `apps/api/app/integrations/factory.py`
- `apps/api/app/dev_upload.py` (criado)
- `apps/api/app/main.py`

## Problema

Ao anexar selfie no cadastro do entregador, o frontend recebia a presigned URL `stub://put/couriers/2/...` e tentava fazer `PUT` nela. O browser rejeitava: `URL scheme "stub" is not supported`. O erro era mascarado como "Sem conexão. Sua foto sobe sozinha quando a internet voltar."

## Causa raiz

O `StorageStubAdapter` (usado em `environment=dev`) retornava URLs com scheme `stub://` — útil para testes unitários (prova que sem presign não há acesso), mas impossível de usar num browser real.

## Correção

- `StorageStubAdapter` agora aceita `base_url` opcional; quando presente, presigned URLs apontam para `http://localhost:8000/v1/dev/upload/{key}` em vez de `stub://`
- `factory.py` passa `base_url="http://localhost:8000"` quando `environment == "dev"`; testes (sem base_url) continuam com `stub://`
- Criado `dev_upload.py`: endpoint `PUT /v1/dev/upload/{key:path}` que recebe o arquivo e salva via `storage.put_bytes()`. Só registrado quando `environment == "dev"`
- Flow completo funciona: presign → PUT HTTP real → arquivo salvo no temp filesystem
