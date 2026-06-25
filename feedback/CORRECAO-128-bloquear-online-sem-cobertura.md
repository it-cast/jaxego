# CORRECAO-128 — Bloquear toggle online sem bairros de cobertura cadastrados

## O que mudou

### Frontend (apps/app)
- **entregador.service.ts**: Novo método `coverageCount(courierId)` que busca GET `/v1/couriers/{id}/coverage` e retorna a quantidade de bairros cadastrados
- **inicio.page.ts**:
  - Signal `noCoverage` indica se o entregador não tem nenhum bairro cadastrado
  - Computed `toggleDisabled` combina `kycPending || noCoverage` para desabilitar o toggle
  - `ngOnInit` carrega a coverage count junto com os outros dados
  - Banner de aviso "Cadastre pelo menos um bairro de entrega para ficar online" exibido quando não há cobertura (e documentos estão ok)
  - Toggle online desabilitado enquanto `noCoverage` for true

## Arquivos alterados
- apps/app/src/features/entregador/entregador.service.ts
- apps/app/src/features/entregador/inicio.page.ts
