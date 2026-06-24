# CORRECAO-110 — Remover campos Cidade/UF, reposicionar GPS e renomear label

## O que mudou

### Frontend (apps/web)
- **cadastro.page.html**:
  - Botão "Usar minha localização" movido para acima do select de área
  - Label "Cidade atendida" alterado para "Cidade/Área de atuação"
  - Campos "Cidade" e "UF" removidos do formulário (cidade já é definida pela área selecionada)
- **cadastro.page.ts**:
  - Campos `cidade` e `uf` removidos do FormGroup
  - Referências a `cidade` e `uf` removidas de todos os `patchValue` (lookupCep, fillFromGps, onAreaChange)

## Arquivos alterados
- apps/web/src/features/loja/cadastro/cadastro.page.html
- apps/web/src/features/loja/cadastro/cadastro.page.ts
