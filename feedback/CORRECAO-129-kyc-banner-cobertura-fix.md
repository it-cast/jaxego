# CORRECAO-129 — Fix banner KYC, separar aviso de cobertura, margin

## O que mudou

### Frontend (apps/app)

**availability-toggle.component.ts**:
- Adicionado `@Input() disabledReason` ('kyc' | 'coverage' | '') para diferenciar o motivo do bloqueio
- Banner de KYC agora só aparece quando `disabledReason === 'kyc'` (antes aparecia para qualquer `disabled`)
- Banner redesenhado como card warning (fundo amarelo, botão "Ver validação" integrado)
- Removido import de `WarnBannerComponent` (não usado mais)

**availability-toggle.component.scss**:
- Adicionado estilo `.jx-availability__kyc-card` (card warning com botão pill)
- Removido estilo antigo `.jx-availability__cta`

**inicio.page.ts**:
- `kycPending` agora exclui `mei_pending` (MEI pendente não é bloqueante para ficar online)
- Passa `disabledReason` ao toggle ('kyc', 'coverage' ou '')
- Banner de cobertura envolto em `.jx-home-warn-wrap` com padding lateral

## Arquivos alterados
- apps/app/src/features/entregador/disponibilidade/availability-toggle.component.ts
- apps/app/src/features/entregador/disponibilidade/availability-toggle.component.scss
- apps/app/src/features/entregador/inicio.page.ts
