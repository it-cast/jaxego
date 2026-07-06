---
classe: ux
data: 2026-07-06
arquivos_afetados:
  - apps/web/src/features/loja/cadastro/cadastro.page.ts
  - apps/web/src/features/loja/cadastro/cadastro.page.html
  - apps/web/src/features/loja/cadastro/cadastro.page.scss
---

## Problema
Ao tentar finalizar o cadastro sem aceitar os Termos e a Política de Privacidade, o botão bloqueava o envio mas não exibia nenhuma mensagem visível — o `stepError` era renderizado no topo da página, fora do campo de visão do usuário que estava rolado até o passo final.

## Implementação
- `submit()`: adicionado `form.controls.consent.markAsTouched()` antes de retornar, para ativar a validação visual do campo
- HTML: adicionado `<p class="jx-cadastro__consent-error" role="alert">` inline abaixo do checkbox, visível quando `consent.touched && !consent.value`
- SCSS: adicionado `.jx-cadastro__consent-error` com `color: var(--error)` e `font-weight: 500`
- O erro no topo (`stepError`) permanece como fallback acessível
