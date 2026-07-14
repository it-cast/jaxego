# CORRECAO-257 — Plano Básico (Free) agora editável e removível

## Data
2026-07-14

## Pedido
"Na parte de /plataforma/planos por que não consigo editar o plano básico?
Retire essa tag de 'Free' juntamente com o nome dele e deixe que seja
possível editar e remover ele como qualquer outro plano."

## Causa
`is_free=True` (a flag que marca qual plano é o padrão/gratuito, usada por
`_pick_active_plan` em `merchants/service.py` pra decidir a assinatura ativa
de um novo cadastro) também bloqueava edição/remoção — tanto no backend
quanto no frontend:
- `app/plans/service.py::update_plan`/`delete_plan` — `raise
  ValidationAppError(...)` se `plan.is_free`.
- `planos.page.html` — badge "Free" ao lado do nome + botões de editar/
  desativar com `[disabled]="item.is_free"`.

## O que mudou
- Removidos os dois `if plan.is_free: raise ...` em
  `app/plans/service.py::update_plan` e `::delete_plan`.
- Removida a tag "Free" (`<span class="jx-planos__badge--free">`) e os
  `[disabled]="item.is_free"` dos botões de editar/desativar em
  `planos.page.html`. CSS morta removida (`.jx-planos__badge--free`).
- `is_free` continua existindo como campo (não é um input do formulário de
  criar/editar, então nenhuma edição muda esse valor) — só marca qual plano
  é o padrão/gratuito pra `_pick_active_plan`. Editar/desativar deixou de
  depender dele.
- Docstrings do model e do service atualizados (não falam mais em "imutável").

## Não mexido
`seed_plans_if_missing` (o mesmo arquivo) tem um `if not existing.is_free:`
que pula reaplicar price/deliveries/fee no plano free durante o seed — não
toquei porque essa função **não tem nenhum caller no código atual** (grep
confirmou, é código morto/órfão). Se algum dia for religada, essa lógica
sobrescreveria edições manuais do admin nesse plano especificamente — fica
registrado como TD caso a função volte a ser usada.

## Validado
- Import limpo do backend, API reiniciada.
- `ng build web` — verde.

## Tech debt / pontos em aberto
- `seed_plans_if_missing` órfã (sem caller) — mencionado acima, não é bug
  novo desta correção.
- Se o admin zerar/mudar o preço do plano Básico pra um valor não-zero, ele
  continua marcado `is_free=True` internamente (isso não é um form field) —
  comportamento aceito conforme pedido ("editar como qualquer outro plano"),
  mas pode gerar um estado logicamente estranho (plano "grátis" com preço) se
  não tomarem cuidado. Não adicionei validação extra pra isso — não foi pedido.
