# Milestones de Gaps Funcionais (paridade competitiva)

> Gaps reais descobertos na comparação com Lalamove/Bee/Loggi. Desenvolvidos
> end-to-end: backend (+migration) + frontend loja + app entregador + admin, com UX.
> Safe2Pay continua fora (MR-6, final).

## MG-1 — Pacote com peso e dimensões  ⏳ em execução

Hoje a entrega só tem `items_description` (texto) + quantidade + valor declarado.
Plataformas multi-veículo precisam de **peso + dimensões** (escolha de veículo, preço).

- [ ] **F-MG1.1 Backend**: migration `0014` (`weight_g`, `length_cm`, `width_cm`,
      `height_cm` em `deliveries`, todos nullable) + model + `CreateDeliveryBody` +
      `DeliveryOut` + `CourierDeliveryOut` + persistência no `create_delivery` + testes.
- [ ] **F-MG1.2 Loja (web)**: campos no formulário de nova entrega (peso em kg,
      dimensões em cm) com máscara/validação + exibição no detalhe da entrega.
- [ ] **F-MG1.3 Entregador (app)**: peso/dimensões visíveis na oferta e na entrega
      ativa (o entregador precisa saber o tamanho antes de aceitar).
- **Aceite:** lojista cadastra pacote com peso/medidas; entregador vê na oferta;
  admin vê no detalhe. ng build + testes verdes.

## MG-2 — Painel admin com profundidade operacional (data-tables-ux)

Listas hoje são tabelas básicas. Elevar para o padrão `data-tables-ux`.

- [ ] **F-MG2.1**: tabela avançada reutilizável (ordenação, busca, filtro, paginação,
      densidade) sobre o `jx-data-table` primitivo.
- [ ] **F-MG2.2**: aplicar nas listas de entregadores, lojas, disputas.
- [ ] **F-MG2.3**: (opcional) KPIs/analytics no painel.
- **Aceite:** listas com ordenação/busca/filtro/paginação reais.
