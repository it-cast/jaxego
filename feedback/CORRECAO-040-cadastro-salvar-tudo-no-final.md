# Correção 040 — Cadastro do entregador refatorado: salva tudo no final, não a cada step

> **Classe:** COD/UX · **Data:** 2026-06-18

---

## Arquivos afetados

- `apps/app/src/features/entregador/cadastro/cadastro.page.ts` (reescrito)
- `apps/app/src/features/entregador/cadastro/cadastro.page.html` (reescrito)
- `apps/app/src/features/entregador/cadastro/cadastro.page.scss`

## Problema

O wizard de cadastro chamava `POST /v1/couriers/signup` logo no passo 1 ("Continuar" nos Dados). Se o entregador voltasse para os dados e tentasse continuar de novo, recebia "Você já tem cadastro nessa cidade. Recupere o acesso." — porque o courier já existia no banco. Além disso, o fluxo F-02 documenta que todos os dados devem ser submetidos no final (passo 7: "Submete → status pending_kyc"), não a cada step.

## Correção

Refatoração completa do fluxo:

1. **Dados em memória**: todos os steps coletam dados sem chamar a API. Fotos selecionadas são guardadas como `File` em memória (não fazem upload imediato)
2. **Validação por step**: passo 1 valida formulário (CPF, senhas, consentimento); passo 2 exige selfie selecionada; passo 3 coleta veículo
3. **Submit único no final**: ao clicar "Enviar para análise" no último step:
   - `POST /v1/couriers/signup` → recebe `courier_id`
   - MEI (se preenchido) → `POST /v1/couriers/{id}/mei`
   - Upload sequencial das fotos: presign → PUT → complete, com progresso ("Enviando Selfie 1/2…")
   - Se upload falhar, courier já existe com `pending_kyc` — pode reenviar depois
   - Redireciona para "Em análise"
4. **Draft sem courierId**: o sessionStorage não salva mais `courierId` (não existe até o final). Salva step, level e dados do form (sem senha)
5. **Feedback visual**: `submitting` signal + `submitProgress` mostra ao usuário o que está acontecendo durante o envio
