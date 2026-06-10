# UX Copywriting pt-BR — tom, vocabulário e microcopy para UI brasileira

> Skill obrigatória para qualquer UI em pt-BR (locale `pt-BR` em `specs/project.yaml`).

## Princípio central

Boa microcopy é invisível — o usuário age sem atrito e não lembra do texto. Má microcopy é atrito. O objetivo não é "ser criativo", é **reduzir fricção cognitiva**.

Três testes para cada string da UI:
1. **Claro?** — usuário entende na primeira leitura
2. **Humano?** — soa como pessoa, não como manual
3. **Útil?** — ajuda a tomar decisão ou executar ação

Se falha em qualquer um, reescrever.

## Tom

### Direto, não corporativo

- ❌ "Nós agradecemos por sua preferência e esperamos que sua experiência seja incrível!"
- ✅ "Tudo pronto. Vamos começar."

### Assume usuário inteligente

- ❌ "Por favor, digite seu nome completo no campo abaixo."
- ✅ "Nome completo"

### Reconhece erro sem se desculpar excessivamente

- ❌ "Pedimos desculpas! Infelizmente algo terrível aconteceu e não conseguimos..."
- ✅ "Não conseguimos carregar seus pedidos. Tente de novo."

### Celebra sem exagero

- ❌ "PARABÉNS! 🎉🎉🎉 Você é INCRÍVEL!"
- ✅ "Pedido enviado."

### Nunca paternalista

- ❌ "Parece que você teve um probleminha. Fica tranquilo!"
- ✅ "Senha incorreta. Tente de novo."

## Regras invioláveis

### 1. "Você" sempre

Não "tu" (regional), nunca "o senhor/a senhora" (distante), nunca ambos na mesma tela.

### 2. Acentuação correta sempre

- "não", "você", "está", "também", "após", "através"
- Nunca "nao", "voce", "esta" (esses são variantes de outras palavras)

### 3. Nenhum anglicismo desnecessário em UI de usuário final

| ❌ Inglês | ✅ Português |
|-----------|--------------|
| Login | Entrar |
| Logout | Sair |
| Sign up / Sign in | Criar conta / Entrar |
| Submit | Enviar |
| Cancel | Cancelar |
| Save | Salvar |
| Delete | Remover (não "deletar") |
| Edit | Editar |
| Search | Buscar |
| Upload | Enviar (arquivo) |
| Download | Baixar |
| File | Arquivo |
| Folder | Pasta |
| Link | Link (tolerado) ou "endereço" |
| Password | Senha |
| Email | Email ou "e-mail" (sem acento) |
| Post (verbo) | Publicar |

Exceções aceitas: termos consagrados ou nomes de produto ("PDF", "PIX", "iPhone").

### 4. Verbo de ação em CTA

- ❌ "Pedido"
- ❌ "Clique aqui"
- ❌ "OK"
- ✅ "Criar pedido"
- ✅ "Ver detalhes"
- ✅ "Baixar relatório"

Exceção: botão "OK" em confirmação binária simples onde ação não precisa explicação ("Desfazer exclusão? [Desfazer] [OK]").

### 5. Label acima, placeholder como exemplo

```html
<!-- ❌ placeholder como label -->
<input placeholder="Seu CPF" />

<!-- ✅ -->
<label for="cpf">CPF</label>
<input id="cpf" placeholder="Ex: 000.000.000-00" />
```

Placeholder = exemplo de formato, nunca instrução.

### 6. Erro específico, com ação

- ❌ "Campo inválido"
- ❌ "Algo deu errado"
- ❌ "Erro ao processar"
- ✅ "CPF deve ter 11 dígitos"
- ✅ "Não conseguimos enviar. Verifique sua conexão e tente de novo."
- ✅ "Pedido não encontrado. Pode ter sido removido."

### 7. Empty state com CTA

- ❌ "Nenhum dado disponível"
- ❌ "Lista vazia"
- ✅ "Nenhum pedido ainda. Quando você criar um, ele aparece aqui." + botão `[Criar pedido]`

### 8. Confirmação destrutiva com consequência

- ❌ "Tem certeza?" [OK] [Cancelar]
- ✅ "Remover este pedido? Essa ação não pode ser desfeita." [Remover] [Cancelar]

CTA primário diz o que vai acontecer — não "OK".

## Padrões por contexto

### Onboarding

- ❌ "Bem-vindo! Estamos muito felizes de ter você aqui conosco!"
- ✅ "Tudo pronto. Vamos começar."

- ❌ "Seu cadastro foi realizado com sucesso!"
- ✅ "Conta criada."

### Loading

Prefira skeleton do layout real a texto.

Quando precisa texto:
- ❌ "Aguarde..."
- ❌ "Carregando, por favor aguarde..."
- ✅ "Carregando"
- ✅ "Buscando seus pedidos" (se leva > 2s)

### Sucesso (toast)

- Máximo 3-5 palavras
- Verbo no passado
- Sem "sucesso"

- ❌ "Sua ação foi realizada com sucesso!"
- ✅ "Pedido criado"
- ✅ "Arquivo enviado"
- ✅ "Alterações salvas"

### Erro (toast vs modal)

Toast para erros recuperáveis:
- "Não conseguimos salvar. Tentando de novo..."

Modal para erros que bloqueiam ação:
- Título: "Não foi possível enviar o pagamento"
- Corpo: "O cartão foi recusado pelo banco. Tente outro método ou entre em contato com seu banco."
- Ações: [Tentar outro cartão] [Falar com suporte]

### Formulários

| Elemento | Padrão |
|----------|--------|
| Label obrigatório | `CPF *` (asterisco no fim, sem texto "obrigatório") |
| Label opcional | `Complemento (opcional)` |
| Grupo de campos | Título da seção acima, em peso semibold |
| Erro no campo | Abaixo do input, vermelho, específico |
| Erro de submit | Banner no topo do form com lista dos campos com erro |

### Confirmação de exclusão

```
[Modal]
Título: "Remover pedido #A-1042?"
Corpo: "Essa ação não pode ser desfeita. O pedido e todo o histórico serão removidos permanentemente."
Ações: [Remover] (destructive) [Cancelar] (secondary)
```

### Timeouts e bloqueios temporários

- ❌ "Acesso negado"
- ✅ "Muitas tentativas. Espere 2 minutos antes de tentar de novo."

## Vocabulário canônico do projeto

Definido em `docs/identidade-visual/brand.md`. Consistência entre features.

| Conceito | Termo canônico | Variações evitadas |
|----------|----------------|---------------------|
| (varia por projeto) | "usuário" OU "cliente" OU "membro" — escolher um | — |
| Pedido/ordem | "pedido" | "ordem", "order" |
| Pagamento | "pagamento" | "payment", "cobrança" |
| Notificação | "notificação" OU "aviso" | alternar sem razão |
| Configuração | "configurações" | "settings", "ajustes" |

**Uma vez escolhido, não alternar.** Sem exceções.

## Números, datas e moeda

### Datas

- ❌ "2026-04-22"
- ❌ "04/22/2026" (formato US)
- ✅ "22/04/2026"
- ✅ "22 de abril de 2026" (formal)
- ✅ "há 2 horas" (relativo, quando útil)

### Moeda

- ❌ "$450" ou "R$ 450.00"
- ✅ "R$ 450,00"
- Sem centavos se valor redondo? Controverso — a maioria dos apps financeiros mostra centavos sempre para consistência

### Plural

- "0 pedidos" (não "0 pedido")
- "1 pedido"
- "2 pedidos"
- Se genérico, "pedido(s)" em construções como "CPF do(s) cliente(s)" — pesado mas correto

### Porcentagem

- ❌ "15 porcento"
- ✅ "15%"

## Status de negócio

Definir labels consistentes:

```json
{
  "status": {
    "pending": "Aguardando",
    "processing": "Em processamento",
    "confirmed": "Confirmado",
    "in_transit": "A caminho",
    "delivered": "Entregue",
    "cancelled": "Cancelado",
    "refunded": "Reembolsado",
    "failed": "Falhou"
  }
}
```

Consistente em toda UI — user aprende uma vez.

## Inclusivo sem ser desajeitado

### Gênero neutro quando prático

- ❌ "O usuário deve confirmar seu email"
- ✅ "Confirme seu email"

### Evitar suposições

- ❌ "Olá, senhor/senhora" (pede gênero)
- ✅ "Olá, {nome}"

### Não assumir capacidade

- ❌ "Use seu celular"
- ✅ "Use seu telefone" (quando se refere a equipamento, não só smartphone)

### Cor não é único canal

- ❌ "Campos em vermelho precisam de correção"
- ✅ "Campos com ⚠️ precisam de correção" (ícone + cor)

## Abreviações

Limitar a casos óbvios: "CPF", "CEP", "CNPJ", "CNH", "RG", "PIX", "NF" (nota fiscal em apps B2B).

- ❌ "Dt. Nasc." (data de nascimento)
- ✅ "Data de nascimento"

- ❌ "Qtd." (em contexto de compra)
- ✅ "Quantidade"

Exceção: células de tabela com espaço apertado podem abreviar com tooltip explicativo no header.

## Microcopy de acessibilidade

```html
<button aria-label="Remover item do carrinho">
  <icon-trash />
</button>

<button aria-label="Ver detalhes do pedido #A-1042">
  Ver
</button>
```

Label descritivo, não genérico como "botão" ou "clique aqui".

## Revisão em 3 passadas

Antes de publicar qualquer string nova:

1. **Sentido** — está claro o que faz/significa?
2. **Tom** — coerente com brand.md?
3. **Acentuação** — toda palavra escrita corretamente?

Ferramenta útil: LanguageTool / Vale (linter de prosa).

## Checklist para PLAN.md (fases com UI)

- [ ] Zero "Ops!", "Algo deu errado", "Oops", "Uhul!"
- [ ] Zero anglicismos desnecessários (login/submit/settings) em UI visível
- [ ] Todo CTA com verbo + substantivo (ou verbo contextual)
- [ ] Toda mensagem de erro específica + com ação
- [ ] Todo empty state com CTA
- [ ] Toda confirmação destrutiva com consequência explícita
- [ ] Labels acima de inputs; placeholder apenas como exemplo
- [ ] Status de negócio usando vocabulário canônico
- [ ] Datas em `dd/mm/aaaa` ou relativo; moeda em `R$ X,XX`
- [ ] Acentuação correta em 100% das strings
- [ ] `aria-label` descritivo em botões só-ícone
- [ ] Strings externalizadas em `src/assets/i18n/pt-BR.json`
