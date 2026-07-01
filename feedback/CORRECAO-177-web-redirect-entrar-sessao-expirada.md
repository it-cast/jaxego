# CORRECAO-177 — Web: redireciona para /entrar quando sessão expira

## Problema
Após reset do Docker (ou expiração do refresh token), o web app ficava "preso"
na página atual sem redirecionar para `/entrar`. O interceptor já chamava
`void router.navigate(['/entrar'])` mas esse fire-and-forget era insuficiente.

## Causa
`LojaShellComponent` não tinha nenhuma reação à perda de autenticação mid-session.
O `authGuard` só corre na navegação inicial para a rota, nunca durante a sessão ativa.

## Solução
Adicionado `effect()` no constructor de `LojaShellComponent` que reage ao signal
`auth.isAuthenticated()`. Quando o interceptor zera `_accessToken` (refresh falhou),
o signal dispara → `router.navigate(['/entrar'])`.

## Arquivo modificado
- `apps/web/src/layouts/loja-shell.component.ts`

## Por que no shell e não nas páginas individuais
O `LojaShellComponent` é o ancestor de todas as rotas `/loja/*`. Um único `effect()`
aqui cobre dashboard, entregas, detalhe, config, faturas, plano — sem tocar
cada página individualmente.

## Segurança do effect()
Na primeira execução, `isAuthenticated()` é `true` (o `APP_INITIALIZER` já rodou
`tryRestoreSession()` antes do shell renderizar, e o `authGuard` teria bloqueado
navegação se fosse false). Portanto o effect só dispara o navigate quando o token
cai DURANTE a sessão ativa — sem falso positivo no boot.
