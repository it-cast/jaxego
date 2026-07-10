# CORRECAO-228 — Wizard de cadastro do entregador: seletor de banco, header e fix do signup 422

## Data
2026-07-10

## Mudanças

### 1. Seletor de banco (modal com busca)
Campo "Código do banco" (texto livre) substituído por mostrador + botão "Selecionar"
que abre modal com busca. Lista de bancos vem da BrasilAPI
(`https://brasilapi.com.br/api/banks/v1`), ordenada por nome, filtrável por nome
ou código. Enquanto a requisição carrega, exibe "Buscando bancos…". Ao confirmar,
o `bank_code` do form recebe o código do banco selecionado.

### 2. Header e navegação entre passos
- Removido link "← Voltar ao login" do topo; entrou `<jx-page-header>`
  (componente compartilhado) com título "Cadastro de entregador" e backLink="/"
- Botão "Voltar" (estilo secundário) no rodapé abaixo de "Continuar",
  visível a partir do passo 2, volta um passo e limpa `stepError`
- `RouterLink` removido dos imports do componente (não é mais usado no template)

### 3. Fix: signup retornava 422 validation_error
Dois problemas independentes no mesmo erro:

**a) `extra_forbidden` para birth_date/endereço/banco** — os arquivos dentro do
container `jaxego-api-1` já estavam atualizados (copiados via `docker cp`), mas o
processo uvicorn roda sem `--reload` e ainda validava com o schema antigo.
Fix: `docker restart jaxego-api-1`. (Mesma causa raiz da CORRECAO-223.)

**b) `string_too_short` em password (enviada vazia)** — `restoreDraft()` devolvia
o usuário ao passo salvo no draft, mas a senha nunca é persistida (segurança).
Após reload da página, o usuário chegava ao submit com `password: ''`.
Fixes em `cadastro.page.ts`:
- `restoreDraft()`: se a senha está vazia, restaura os dados mas volta ao passo 0
  para o usuário redigitá-la
- `submitAll()`: rede de segurança — se a senha está inválida/divergente, não envia;
  volta ao passo 0 com mensagem "Digite sua senha novamente para concluir o cadastro."

## Arquivos alterados
- `apps/app/src/features/entregador/cadastro/cadastro.page.ts`
- `apps/app/src/features/entregador/cadastro/cadastro.page.html`
- `apps/app/src/features/entregador/cadastro/cadastro.page.scss`

## Lição operacional
API roda uvicorn **sem** `--reload`: qualquer mudança em Python no container
(mount ou `docker cp`) exige `docker restart jaxego-api-1` para valer.
