# Sprint Slicing — duas ordens documentadas

> Referência normativa para `/gsd-sprint-plan`. Define como quebrar um milestone em sprints testáveis.
> A escolha entre as duas ordens é gravada em `.planning/config.json > slicing_strategy` durante o `bootstrap` e vale para todo o projeto.

## Princípio central

Um milestone é grande demais para ser unidade de trabalho. Um sprint é:

- **Curto:** 3-10 dias úteis de trabalho real (não calendário — inclui revisões, reconcile, QA)
- **Testável por humano:** em < 30 minutos, alguém que nunca viu o sprint consegue confirmar se ele funciona ou não abrindo o app/API
- **Fiel à identidade visual:** se toca UI, cita tokens específicos de `docs/identidade-visual/tokens.json`
- **Coerente:** uma narrativa só — sprint não é "conjunto aleatório de tickets que couberam na semana"

Dois sprints bem feitos em cadeia produzem muito mais valor do que dez tickets soltos. A unidade certa é o **fluxo**, não a tarefa.

## A. Vertical Value Slicing (default)

### Quando usar

Produto com **usuário externo** (B2C, B2B-SaaS, marketplace, app mobile de consumidor). Qualquer projeto onde a definição de sucesso envolve alguém **fora da empresa** usando o produto.

### Como funciona

Cada sprint atravessa todas as camadas técnicas (UI + API + banco + regra) para entregar **um caminho do usuário principal, ponta a ponta**, na versão mais magra possível.

**Ordem típica:**

- **Sprint 0 (preparação, não é sprint de valor):** auth + design tokens instanciados + 3-5 componentes primitivos do design system + schema das 2-3 tabelas principais do domínio (só colunas óbvias; outras entram conforme precisar). Admin neste ponto: **apenas** um CRUD de usuários, e só se auth exigir.
- **Sprint 1:** usuário consegue fazer a ação principal do produto (criar X, enviar Y) na versão mais simples possível, com **1 regra crítica mínima** (ex: usuário só vê recurso próprio). Demonstrável: "abro o app, me cadastro, crio, vejo na lista."
- **Sprint 2:** segunda ação do fluxo — tipicamente mutação de estado (confirmar, cancelar, concluir) com regra de transição + histórico. Admin ganha poder de intervenção manual **aqui**, quando alguém já poderia pedir por ele.
- **Sprint 3-N:** expande o fluxo (pagamento, notificação, colaboração, etc.). Cada sprint inclui a regra crítica daquela etapa, não só o CRUD.
- **Sprint N+1 em diante:** filtros, busca, relatórios — depois que há dados reais para filtrar e relatar.

### Princípios

1. **Primeira ação de valor no sprint 1.** Se o sprint 1 é "login + design system + seed de categorias", não é value slice — é Sprint 0 disfarçado.
2. **Regras críticas junto com a feature, não depois.** "Criar pedido" e "usuário só vê pedido próprio" vão juntos. Não faz sentido ter criação sem a regra — alguém vai ver pedido alheio em demo e o sprint volta.
3. **Admin cresce puxado pela demanda real.** Dashboard de admin entra quando o time de atendimento pede pela primeira vez, não antes. Isso evita admin elaborado que nunca foi usado.
4. **Infra cresce puxada também.** Observabilidade entra no Sprint 1 porque Gate 4 exige (endpoints precisam de log + métricas). Mas dashboard de observabilidade elaborado só entra quando você estiver debugando produção de verdade.

### Exemplo (marketplace de serviços)

| Sprint | Entregável testável |
|--------|----------------------|
| 0 | Cadastro + login funcionam. Design tokens instanciados. Button, Input, Card no Storybook. |
| 1 | Prestador cria um anúncio. Cliente busca e vê anúncio. (Regra: só dono edita o próprio.) |
| 2 | Cliente envia mensagem ao prestador. Prestador responde. Status "lida/não-lida". |
| 3 | Cliente solicita serviço. Prestador aceita/recusa. Transição de estado + histórico. |
| 4 | Pagamento do serviço (pode ser mock em sandbox). Confirmação pós-pagamento. |
| 5 | Admin tem tela para ver/intervir em casos problemáticos (denúncia, estorno). |
| 6 | Filtros + busca avançada no anúncio. Relatórios básicos. |

Note que o "admin" só aparece no Sprint 5, quando existe dor real de operação. Antes disso, o admin do Sprint 0 (CRUD de usuários) era suficiente.

## B. Admin-First Slicing (para backoffice/ERP)

### Quando usar

Produto onde o **admin é o produto**: ERP interno, backoffice de operadora, sistema de gestão empresarial, ferramenta operacional. O "usuário externo" é o operador da empresa contratante.

### Como funciona

A ordem que você [usuário do framework] propôs inicialmente, e que **faz sentido aqui** porque o fluxo principal de valor é, de fato, o CRUD administrativo.

**Ordem típica:**

- **Sprint 0:** auth + design tokens + componentes primitivos + layout base do admin (sidebar, topbar, breadcrumb).
- **Sprint 1-3: Cadastros de admin** — CRUDs das entidades mestras (usuários, permissões, categorias, tenants, configurações). Cada sprint entrega 1-2 CRUDs completos com listagem + form + validação + regra de permissão.
- **Sprint 4-7: CRUDs de negócio** — entidades do domínio (clientes, produtos, pedidos, contratos). Cada CRUD entrega criação + edição + listagem + regras de propriedade básicas.
- **Sprint 8+: Regras críticas, filtros, junções** — transições de estado, workflows, relatórios com joins complexos, dashboards, automações.

### Princípios

1. **Cada sprint de CRUD entrega também a tela.** Não é "banco sprint 1, API sprint 2, tela sprint 3". Vertical mesmo, só que a ordem dos CRUDs segue dependência funcional, não usuário externo.
2. **Regras de propriedade e permissão no sprint do CRUD, não depois.** "CRUD de pedido" inclui "só manager vê pedidos do seu tenant".
3. **Regras de negócio complexas podem vir depois** (essa é a diferença do Value Slice). Transições de estado de pedido, por exemplo, podem ser Sprint 9 enquanto Sprint 4 só tem status como enum simples.
4. **Testabilidade de cada sprint:** humano logado como admin consegue abrir o sistema e fazer o fluxo do CRUD em < 30 min.

### Exemplo (ERP interno de distribuidora)

| Sprint | Entregável testável |
|--------|----------------------|
| 0 | Login admin. Layout base com sidebar + áreas. Design tokens aplicados. |
| 1 | CRUD de usuários + permissões. |
| 2 | CRUD de empresas/tenants + configurações por tenant. |
| 3 | CRUD de categorias de produto + unidades de medida. |
| 4 | CRUD de produtos (campos básicos: nome, categoria, preço, estoque atual). |
| 5 | CRUD de clientes + endereços. |
| 6 | CRUD de pedidos (criação manual com itens, status como enum). |
| 7 | CRUD de notas fiscais emitidas (só leitura + filtros). |
| 8 | Regra: pedido → nota fiscal (transição de estado + validação) |
| 9 | Regra: estoque decrementa ao faturar, conciliação mensal |
| 10 | Filtros avançados + relatórios (vendas por período/cliente/produto) |

### Por que aqui "admin primeiro" funciona

Porque o operador do backoffice **é** o usuário. Ele entra às 8h, fica 8h usando o admin. CRUD de produto não é telinha sem valor — é a ferramenta principal de trabalho. Entregar CRUD de cliente no Sprint 5 já é colocar o operador usando.

Isso não vale quando o usuário principal é o consumidor externo que nunca abre admin.

## Critério de decisão rápido

Pergunta única: **quem é a pessoa cuja vida fica melhor ao final do Sprint 1?**

- Se é **um usuário externo** (cliente, consumidor, prestador, paciente, aluno) → **A (Vertical Value)**
- Se é **um operador interno da empresa** (atendente, gerente, financeiro, logística) → **B (Admin-First)**

Se você hesitar, default para A. B é a exceção.

## Projetos híbridos

Alguns projetos têm ambos — produto para consumidor externo **e** painel pesado de operação interna (ex: marketplace com backoffice de moderação; app de delivery com painel de restaurante).

Estratégia: **A para o fluxo principal, B como trilha paralela de complexidade menor**, começando apenas quando o operacional dói de verdade. Não tente avançar os dois em sprints alternados — dispersa foco e dilui testabilidade.

## Invariantes de todo sprint (qualquer ordem)

Independente de ser Value Slice ou Admin-First, todo sprint tem:

1. **Critério de aceite testável em 30 min** — descrito em `SPRINT.md > ## Definition of Done` em linguagem de usuário final, não técnica
2. **Visual Contract** (se toca UI) — tokens citados de `docs/identidade-visual/tokens.json`
3. **Skills de UX obrigatórias citadas** (se toca UI) — ver `skills-enforcement.md > sprint_matrix`
4. **1-3 regras críticas** junto com a feature (não "regras depois")
5. **Observability** desde o primeiro endpoint (Gate 4)
6. **Retrospectiva preenchida** ao fechar — alimenta `.planning/METRICS.md`

Sprints que falham em qualquer invariante não fecham — retornam ao backlog com motivo registrado.

## Anti-patterns

- Sprints de "infraestrutura": 2 semanas configurando CI + Docker + monitoramento sem entregar nada de usuário. Faça em Sprint 0 ou puxe pela demanda real.
- Sprints de "backend primeiro, front depois": um sprint entrega endpoint, outro entrega tela. Cada um sozinho não é testável por humano.
- Sprint "design system completo antes de features": você não sabe quais componentes precisa até construir a primeira tela real. Comece com 3-5 primitivos e cresça puxado.
- Sprint "todas as regras de negócio depois dos CRUDs": a regra muda o CRUD. Descobre tarde = retrabalho concentrado.
- Sprint sem Definition of Done escrita — todo sprint sem critério testável vira bike shed interminável.
- Sprint com 12 critérios de aceite — se precisa de tantos, são dois sprints.

## Related

- Template: `.claude/get-shit-done/templates/SPRINT.md`
- Workflow: `.claude/get-shit-done/workflows/gsd-sprint-plan.md`
- Enforcement: `.claude/get-shit-done/references/visual-fidelity.md`
- Skills UX obrigatórias: `.claude/get-shit-done/references/skills-enforcement.md > sprint_ui_matrix`
