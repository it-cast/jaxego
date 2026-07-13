# CORRECAO-236 — Fix perfil do entregador (dados/documentos sumidos) + loading no cadastro

## Data
2026-07-13

## Parte 1 — Bug: nome/dados/documentos não apareciam no app

### Sintoma
Após logar, o entregador não via o nome no perfil, os dados em "Editar dados"
nem os documentos em "Documentação".

### Causa raiz
Outra sobra da CORRECAO-230 (remoção da tabela `users`), no mesmo estilo do
bug da CORRECAO-235. Em `app/couriers/router.py`:
- `get_courier_profile` (GET /v1/couriers/{id}/profile): `mask_cpf_display(user.cpf ...)`
  — `user` é o `Actor` autenticado (token), que não tem campo `cpf` (só existe em
  `courier.cpf`, já carregado na função). `AttributeError` → 500 → app cai no
  catch e o profile fica `null`, escondendo nome, dados e documentos.
- `update_courier_profile` (PATCH .../profile), troca de senha: mesma raiz —
  `verify_password(user.password_hash, ...)` e `user.password_hash = ...`
  quebravam a troca de senha do perfil (não reportado ainda, mas mesmo bug).

### Fix
Trocado `user.cpf` → `courier.cpf` e `user.password_hash` → `courier.password_hash`
(a variável `courier` já vinha carregada por `_own_courier` na mesma função).

### Varredura
Confirmado por grep (`\buser\.(cpf|password_hash|document|...)\b`) que não há
mais nenhuma ocorrência desse padrão em nenhum outro router (merchants, teams,
areas, platform_admin).

### Validado
E2E com courier de teste: signup → login → GET /profile → 200 com nome,
cpf_masked, team_name e documents corretos (antes: 500).

## Parte 2 — Loading "Salvando dados" no wizard de cadastro

Substituído o texto simples (`<p>{{ submitProgress() }}</p>`, sem bloquear a
tela) por um overlay de tela cheia com spinner, cobrindo todo o wizard durante
signup → envio do MEI → upload de cada foto:
- `cadastro.page.html`: `.jx-cad__overlay` fixed full-screen com spinner +
  texto (`submitProgress()`), e um mini-spinner dentro do botão "Enviar para
  análise" enquanto `submitting()`.
- `cadastro.page.ts`: mensagens de progresso cobrindo todas as fases —
  "Criando sua conta…" → "Salvando dados do MEI…" (nova, antes não existia
  feedback nessa etapa) → "Enviando {doc} (i/n)…" → "Finalizando…".
- `cadastro.page.scss`: `.jx-cad__overlay`, `.jx-cad__overlay-spinner`,
  `.jx-cad__cta-spinner`, animação `jx-cad-spin`.

## Arquivos alterados
- `apps/api/app/couriers/router.py`
- `apps/app/src/features/entregador/cadastro/cadastro.page.html`
- `apps/app/src/features/entregador/cadastro/cadastro.page.ts`
- `apps/app/src/features/entregador/cadastro/cadastro.page.scss`
