# Correção 068 — Worker com imagem desatualizada causava falha no dispatch

> **Classe:** INF · **Data:** 2026-06-22

---

## Arquivos afetados

- Nenhum arquivo de código alterado — problema era imagem Docker desatualizada

## Problema

Ao criar uma entrega pela loja, a oferta nunca chegava ao app do entregador. O worker falhava com:

```
OperationalError: (1054, "Unknown column 'couriers.cpf' in 'field list'")
```

A coluna `cpf` foi migrada de `couriers` para `users` na correção 053/056, mas o container `jaxego-worker-1` estava rodando com a imagem antiga que ainda tinha `cpf` no model SQLAlchemy. O `SELECT` gerado incluía `couriers.cpf` que não existia mais no banco.

## Correção

- Rebuild da imagem do worker: `docker compose build worker`
- Recriação do container: `docker compose up -d worker`
- Re-enfileiramento do dispatch para a entrega presa: `enqueue_dispatch(1)`

## Observação

Ao rebuildar a API (`docker compose up -d --build api`), o worker precisa ser rebuildado junto. Recomendado usar `docker compose up -d --build api worker` para manter ambos sincronizados.
