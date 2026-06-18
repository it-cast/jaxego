# Correção 001 — Porta do MySQL: conflito com MySQL local

> **Classe:** INFRA · **Data:** 2026-06-15

---

## Arquivo afetado

- `infra/docker-compose.yml`

## Problema

O MySQL do Docker tentava bindar a porta `3306`, que já estava ocupada por um MySQL local instalado na máquina. O container subia sem expor nenhuma porta, tornando impossível conectar pelo Workbench.

## Correção

Alterada a porta exposta de `3306:3306` para `3309:3306`.
