# CORRECAO-142 — Botão único "Coletar e cobrar entrega"

## O que mudou

### Frontend (apps/app)
- **entrega-ativa.page.ts**: Quando ACEITA, exibe um único botão "Coletar e cobrar entrega" que:
  1. Faz POST para marcar como COLETADA
  2. Recarrega a entrega
  3. Abre o modal de cobrança automaticamente
- Botão "Coletei" removido (não existe mais etapa separada de coleta)
- Método `advance` simplificado — só navega para comprovação de entrega (COLETADA)

## Arquivos alterados
- apps/app/src/features/entregador/entrega-ativa/entrega-ativa.page.ts
