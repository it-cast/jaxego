# Correção 015 — Link "Esqueci a senha" apontando para rota inexistente

> **Classe:** COD · **Data:** 2026-06-15

---

## Arquivo afetado

- `apps/web/src/features/auth/login.page.html`

## Problema

O link `href="/auth/recuperar-senha"` na tela de login apontava para uma rota que não existe no roteador Angular e não tem página nem endpoint de backend implementados.

## Correção

Link removido. Funcionalidade de recuperação de senha é uma implementação futura.
