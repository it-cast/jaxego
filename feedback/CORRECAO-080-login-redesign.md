# Correção 080 — Redesign da tela de login inspirado no mockup

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `packages/shared/src/shared/features/auth/login.page.html`
- `packages/shared/src/shared/features/auth/login.page.scss`

## Problema

A tela de login tinha um layout simples sem hierarquia visual clara, sem área para branding/imagem.

## Correção

Redesign seguindo o mockup de referência (login.png):
- **Hero area** no topo com fundo `brand-wash` e cantos arredondados inferiores — espaço reservado para imagem/logo (será adicionada depois)
- **"Bem-vindo!"** como título principal em destaque, subtítulo "Jaxegô. Chegou *rapidinho.*"
- **Inputs pill-shaped** (border-radius full) com placeholder inline em vez de labels acima
- **Botão "Entrar"** pill-shaped com brand color
- **CTA** centralizado: "Ainda não tem conta? Cadastrar minha loja" / "Quer entregar? Cadastre-se"
- **Footer** fixado no fundo com margin-top auto
- Layout full-height (100dvh) para ocupar a tela inteira
- Labels removidos dos inputs (informação no placeholder, como no mockup)
- Campo TOTP mantido com aparição condicional
