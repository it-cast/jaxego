# CORRECAO-229 — Signup não cria mais courier_zonas; preço vem da equipe

## Data
2026-07-10

## Problema
O signup do entregador criava um registro em `courier_zonas` para cada zona da
área com `preco_cents=0` e `ativo=1`. No dispatch, esse registro age como
**override** de preço do entregador — ou seja, entregador recém-cadastrado
ofertava corrida por R$0,00 em vez de usar o `preco_minimo_cents` da equipe.
Além disso, o app exibia o banner "Configure suas zonas de entrega e preços
para ficar online." e bloqueava o toggle de ficar online enquanto não houvesse
cobertura configurada — desnecessário, já que as zonas vêm da equipe.

## Mudanças

### Backend — `apps/api/app/couriers/service.py`
- Removido o bloco que criava `CourierZona` (preco 0) para todas as zonas da
  área no signup. Sem registros, o entregador herda zonas e preços da equipe
  (fallback já existente no dispatch: `cascade.py` usa `TeamZona.preco_minimo_cents`
  quando não há linha em `courier_zonas`; ausência de linha = ativo na zona).
- Imports `Zona` e `CourierZona` removidos (não usados mais).

### App — `apps/app/src/features/entregador/inicio.page.ts`
- Removido o banner "Configure suas zonas de entrega e preços para ficar online."
- `toggleDisabled` agora depende só de `kycPending()` (antes também de `noCoverage()`)
- Removidos: signal `noCoverage`, chamada `coverageCount()` no ngOnInit e `goCobertura()`

### Dados
- Limpeza no banco: `DELETE FROM courier_zonas WHERE preco_cents = 0 AND ativo = 1`
  (5 linhas — artefatos dos signups antigos que causavam preço R$0,00).
  Linhas com `ativo=0` foram mantidas: são opt-outs explícitos de zona e o
  preço delas não é lido.

## Comportamento resultante
- Cadastro novo: nenhum registro em `courier_zonas`; entregador já pode ficar
  online e é despachado com o preço mínimo da equipe.
- Registros em `courier_zonas` só passam a existir quando o entregador
  personalizar preço/cobertura na tela de zonas.
