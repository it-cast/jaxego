# CORRECAO-162 — Paginação padronizada em /equipe/entregas

## O que mudou
A página já tinha paginação com PAGE_SIZE=20 funcional mas com visual simples.
Atualizado para usar FA icons e o mesmo estilo padrão das demais páginas.

- **entregas.page.ts**:
  - Importados `FaIconComponent`, `faChevronLeft`, `faChevronRight`
  - Adicionados `iconPrev` e `iconNext` na classe
  - Template do paginador atualizado com `<fa-icon>`, classes `pager-btn` e `pager-info`
  - Estilos do paginador padronizados (mesma aparência das páginas de plataforma)

## Arquivos alterados
- apps/web/src/features/equipe/entregas.page.ts
