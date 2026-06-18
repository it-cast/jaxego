# Correção 005 — Tela de enrollment TOTP não implementada no frontend

> **Classe:** COD · **Data:** 2026-06-15 · **Status:** PENDENTE → resolvido pela Correção 018

---

## Problema

O backend exige que `admin_plataforma` configure TOTP antes de acessar qualquer endpoint protegido. Os endpoints de enrollment existem no backend (`POST /v1/auth/totp/enroll` e `POST /v1/auth/totp/verify`), mas a tela de QR code e configuração do autenticador não foi implementada no frontend.

## Contorno (dev)

`totp_enrolled = 1` setado diretamente no banco para o admin de desenvolvimento.

## Resolução

Ver Correção 018 — tela completa de enrollment TOTP implementada.
