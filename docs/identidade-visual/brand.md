# Brand — Jaxegô

> Marca: **Jaxegô** (com acento em toda peça visual e copy). Domínio: jaxego.com.br (sem acento). Pronúncia: "já-chegô". O nome é a promessa: rapidez com sotaque do interior.

## Voz

**É:** direta, prática, brasileira do interior (sem caricatura), confiável, editorial-técnica — informação manda, mas com calor tipográfico.

**NÃO é:** corporativa engessada, hype de startup ("revolucionando o last-mile"), mística ("sua jornada"), infantil (emoji em transacional), paternalista.

O usuário-padrão é dono de pizzaria em pico de sexta e motoboy com capacete na mão. Copy que não cabe num grito de balcão está errada.

## Assinatura tipográfica — a regra do italic

**Inter Tight** carrega tudo (display, body, UI). **Fraunces italic** entra em UMA palavra-chave por título/hero, na cor brand — é o sotaque visual da marca. **JetBrains Mono** em todo dado: valores, IDs, timestamps, métricas.

```
Jaxegô. Chegou [rapidinho].        ← rapidinho em Fraunces italic brand-500
Backup [quando] o motoboy não dá conta.
faltam [7,6 pts] para prata
```

Onde aplicar o italic: títulos de seção/hero (1 palavra), números com peso narrativo, quotes. Onde NUNCA aplicar: botões, labels, tabelas, mensagens de erro, dados em mono.

## Tom por contexto

| Contexto | Tom | Bom | Ruim |
|---|---|---|---|
| Hero | Promessa concreta + 1 italic | "Entregador [rapidinho], na sua cidade." | "A revolução do delivery chegou" |
| CTA | Verbo + objeto, ≤4 palavras | "Chamar entregador" | "Clique aqui para começar" |
| Confirmação | Fato, sem festa | "Entrega criada. João está indo coletar." | "🎉 Sucesso! Parabéns!" |
| Erro recuperável | O que houve + o que fazer | "Endereço fora da área. Confira o bairro ou avise interesse." | "Algo deu errado." |
| Erro de pagamento | Impacto + saída | "Cartão recusado. A entrega não foi criada. Tente outro cartão ou pague direto ao entregador." | "Erro 402" |
| Score | Delta + causa, sem moralismo | "Caiu 2,1 pts: 3 cancelamentos após aceite." | "Melhore seu desempenho!" |
| Notificação destinatário | Curta + link | "Sua entrega tá chegando! Acompanhe: jaxego.com.br/r/abc" | parágrafo de saudação |
| Suspensão | Motivo verificável + recurso | "Conta suspensa: 3 comprovações rejeitadas em 7 dias. Você pode recorrer em até 5 dias úteis." | "Violação dos termos" |
| Empty state | Por que está vazio + ação | "Nenhuma entrega ainda. Crie a primeira no botão acima." | "Lista vazia" |

## Vocabulário

Usar / evitar — fonte canônica completa em `regras-negocio/glossario.md`. Resumo do que mais erra:
- **entregador** (nunca motoboy/courier/parceiro)
- **loja** (nunca merchant/lojista)
- **corrida** no app do entregador; **frete** na UI da loja
- **pagamento direto** (nunca "por fora" — é modalidade oficial)
- **validação simples/completa** em UI (KYC só em tela de admin)
- **destinatário** (nunca cliente final)

## Números e formatos

- Dinheiro: "R$ 1.234,56" · Percentual: "82%" · Distância: "2,5 km" · Tempo: "5 min", "1h 30min"
- Data em UI: "25/04/2026", relativo quando hoje/ontem ("hoje, 14:30") · Log: ISO 8601
- CPF/CNPJ formatados em tela, só dígitos no banco; mascarar quando o dado completo não for necessário ("123.***.***-09")
- Telefone: "(22) 99999-1234" · Score: uma casa decimal "87,4"

## Gramática

"Você" sempre. Voz ativa. Sentence case (nunca Title Case). Sem ponto final em CTA/label/badge. CTA ≤ 4 palavras. Primeira frase de alerta ≤ 12 palavras. Siglas mantidas: CNPJ, CPF, CEP, PIX, MEI.

## Referências citadas

Tracking sem app do Mercado Livre; validação de foto da Amazon; heatmap do Uber Driver; densidade do Stripe Dashboard; hierarquia do Linear. Corrigir: opacidade de score do iFood, laranja neon do Rappi, suspensão sem recurso de iFood/Uber, preço tabelado pela plataforma da Lalamove.

> *"O melhor que já existe, melhorado."*
