# CORRECAO-161 — Paginação padronizada em /equipe/entregadores

## O que mudou
A página já tinha paginação com PAGE_SIZE=10. Ajustado para 20 e padronizado
o visual para ficar igual às demais páginas da plataforma.

- **entregadores.page.ts**:
  - `PAGE_SIZE` alterado de 10 para 20
  - Importados `FaIconComponent`, `faChevronLeft`, `faChevronRight`
  - Adicionados `iconPrev` e `iconNext` na classe
  - Template do paginador atualizado com `<fa-icon>`, classes `pager-btn` e `pager-info`
  - Estilos do paginador padronizados (mesma aparência das páginas de plataforma)

## Arquivos alterados
- apps/web/src/features/equipe/entregadores.page.ts
