# CORRECAO-253 — Entregador vira offline automaticamente ao deslogar

## Data
2026-07-14

## Pedido
"Tem um ponto que verifiquei agora. Se o entregador deslogar, precisa setar
ele como offline."

## Onde coloquei a correção
No backend, dentro de `POST /v1/auth/logout` (`app/auth/service.py::logout`),
não no botão de logout do app. Motivo: `AuthService.logout()` (Angular) é
compartilhado entre todos os tipos de conta (loja, entregador, equipe, admin)
— não é o lugar certo pra lógica específica de entregador. Além disso, o
logout pode acontecer sem o app "avisar direito" (app fechado à força,
crash, sem internet na hora de sair) — colocando a regra no endpoint de
logout do servidor, ela vale sempre, não só quando o app se comporta bem.

## O que mudou
`logout()` já revogava o refresh token; agora, se o token pertence a um
`courier` (`token.actor_type == "courier"`), também chama
`couriers/availability.py::set_availability(online=False)` — a mesma função
usada pelo toggle manual "ficar offline" na tela inicial do entregador
(`is_online=False`, `online_until=None`). Falha ao setar offline (ex.:
entregador não encontrado) não derruba o logout em si — é best-effort, a
revogação do token já aconteceu antes.

## Frontend (complementar)
`perfil.page.ts::logout()` agora também chama `CourierLocationService.stop()`
antes de deslogar — parava de existir um ponto que zerasse o timer do ping
de posição (5 em 5 min) usado pro ranking de despacho; ele só era parado no
toggle manual "ficar offline" em `inicio.page.ts`, nunca no logout. Isso é
só higiene do cliente (evita requisição periódica fadada a dar 401 depois
do token limpo) — a correção que realmente importa (is_online=False no
banco) já está garantida pelo backend, independente do cliente.

## Validado
Testei o fluxo completo direto contra o banco (sem precisar de HTTP real):
1. Forcei o entregador de teste (id 15) online via `set_availability`.
2. Emiti um refresh token de verdade pra ele (`issue_token_pair`).
3. Chamei `auth_service.logout()` com esse token.
4. Log confirmou o disparo automático: `courier.availability.update
   online=false` logo após o `logout`.
5. Consulta direta no banco: `is_online = 0`.

API reiniciada, `ng build app` verde.

## Tech debt / pontos em aberto
- Não criei um teste automatizado pra isso (suíte de testes do backend está
  com a coleta quebrada desde o refactor de auth anterior à CORRECAO-235 —
  já registrado como TD na CORRECAO-250).
