# Jaxegô — Visão geral

> Plataforma de entregas por área (cidade ou região de cidade) para o interior brasileiro. Família Grupo Itcast, integrada nativamente ao Menu Certo. Domínio: `jaxego.com.br`.

## Problema

Estabelecimentos de cidades de 30k–200k habitantes não têm para quem ligar quando o motoboy próprio não dá conta. iFood Entregadores é fechado ao iFood. Loggi e Lalamove não cobrem o interior ou cobram caro. White-labels (Larafood, Neemo) vendem o app mas não a malha de entregadores. Resultado: pizza fria na sexta à noite, venda perdida, cliente irritado.

Do outro lado, entregadores dessas cidades não têm plataforma estruturada: trabalham por WhatsApp, sem comprovação, sem score, sem proteção, recebendo "quando der".

## Visão

Uma aplicação única dividida por **áreas** — cada área é uma cidade ou região de cidade com regras próprias (nível de validação de entregador, piso de preço, catálogo de bairros, política de cancelamento). A loja assina um plano para ter acesso à malha de entregadores da sua área e paga cada entrega por cartão, PIX ou **diretamente ao entregador**. O pedido que entra no Menu Certo vira entrega despachada com 1 clique.

Em 6 meses: piloto em Pádua operando com malha líquida (oferta aceita em <60s no horário comercial), lojas pagantes e o nome Jaxegô virando verbo na boca da cidade ("jaxegou?").

## Métrica norte

**Entregas FINALIZADAS por mês** (proxy direto de tração, liquidez e receita).

Metas: M1+3 meses → 600 entregas/mês em Pádua. M1+6 meses → 2.000 entregas/mês em 2–3 áreas.

KPIs secundários: tempo mediano criação→aceite (<60s), % entregas no SLA (>90%), conversão free→pago (>15%), churn mensal de loja (<5%), % de entregas com pagamento direto (acompanhar, sem meta — é termômetro de confiança local).

## Papéis e permissões

| Papel | Quem é | Pode |
|---|---|---|
| **Admin plataforma** | Equipe Jaxegô central | Tudo: criar áreas, gerir planos globais, ver todas as áreas, auditar ações de admins de área, suspender qualquer conta. MFA obrigatório. |
| **Admin de área** | Sócio/gestor local da cidade | Gerir SUA área: aprovar/reprovar KYC de entregadores, curar catálogo de bairros, configurar regras locais (nível de KYC exigido, pisos), gerir API keys da área, ver financeiro da área, suspender entregador/loja da área (com motivo). Não vê outras áreas. |
| **Loja (dono)** | Dono do estabelecimento | Gerir a loja: assinar/trocar plano, criar entregas, gerir operadores, favoritos/bloqueados, ver cobranças e faturas. |
| **Loja (operador)** | Funcionário do balcão | Criar e acompanhar entregas. Não vê financeiro nem gere plano. |
| **Entregador** | Autônomo da área | Ficar online/offline, aceitar/recusar ofertas, executar entregas, comprovar, ver extrato, sacar (se elegível), configurar cobertura e tabela de preços. |
| **Destinatário** | Quem recebe | Sem login. Acompanha pelo link público de tracking, recebe notificações. |

Volume esperado M1 (Pádua): ~30 lojas, ~25 entregadores, ~600 entregas/mês. Arquitetura dimensionada para 50 áreas × 10k entregas/mês sem refator (ver stacks/stack.md).

## Modelo de receita

1. **Assinatura da loja** (mensal, via Safe2Pay): Free R$ 0 (2 entregas/mês) → planos pagos com limites maiores e taxa por entrega menor.
2. **Taxa de plataforma por entrega**: cobrada da loja em TODA entrega, inclusive no plano free e inclusive quando o pagamento da corrida é direto ao entregador. Nos pagamentos via plataforma (cartão/PIX), a taxa sai no split; no pagamento direto, acumula na fatura mensal da loja.
3. **Mensalidade opcional do entregador** (por área, desligada por padrão no M1).
4. **Revenue share do admin de área** (% das taxas da área — modelo de expansão tipo franquia, configurável por área).

### Planos da loja [ASSUMIDO — valores para validação]

| Plano | Mensalidade | Entregas/mês | Taxa de plataforma/entrega |
|---|---|---|---|
| Free | R$ 0 | 2 | R$ 2,00 |
| Início | R$ 49 | 40 | R$ 1,50 |
| Profissional | R$ 129 | 150 | R$ 1,00 |
| Sem Limite | R$ 299 | ilimitado | R$ 0,50 |

O valor da corrida (frete do entregador) é SEMPRE à parte, definido pela tabela do entregador, pago pela loja por cartão, PIX ou direto.

## O que NÃO é o Jaxegô

- Não é marketplace de food (Menu Certo já é).
- Não tem frota própria, centro de distribuição nem armazém.
- Não opera capitais/cidades >500k habitantes.
- Não é app de transporte de passageiros.
- Não define o preço do frete unilateralmente (entregador define a própria tabela; plataforma só impõe piso por área).

## Assumidos para sua revisão

- [ASSUMIDO] Valores e limites dos planos da tabela acima.
- [ASSUMIDO] Taxa de plataforma por entrega nos valores da tabela acima.
- [ASSUMIDO] Cobrança da fatura mensal de taxas (pagamento direto) via Safe2Pay com PIX/cartão/boleto; bloqueio de novas entregas com fatura vencida há mais de 7 dias.
- [ASSUMIDO] M1 entrega o app do entregador como web Ionic responsivo + APK Android via Capacitor (distribuição direta); publicação nas lojas oficiais (Play Store/App Store) fica no M2.
- [ASSUMIDO] Exceção "entregador aceita e some": após 2× o ETA de coleta sem chegada, loja pode cancelar sem custo e redespachar; conta como cancelamento-pós-aceite no histórico do entregador.
- [ASSUMIDO] Exceção "destinatário ausente": botão "ausente" → notificação + tentativa de contato → 10 min sem resposta → retorno ao estabelecimento com cobrança de retorno; estado RECUSADA_NO_DESTINO com reason_code `absent`.
- [ASSUMIDO] Exceção "pagamento falha na criação" (cartão/PIX): entrega não nasce; erro claro com retry e opção de trocar para pagamento direto.
- [ASSUMIDO] SMS apenas no momento "saiu para entrega" (com link de tracking); demais notificações por e-mail/push. Quota de SMS por plano.
- [DECIDIR] Percentual default de revenue share do admin de área (sugestão: 20% das taxas de plataforma da área).
- [DECIDIR] Valor da mensalidade opcional do entregador quando uma área decidir ativá-la.
