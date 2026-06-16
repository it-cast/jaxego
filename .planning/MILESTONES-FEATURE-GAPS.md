# Milestones de Gaps Funcionais (paridade competitiva)

> Gaps reais descobertos na comparação com Lalamove/Bee/Loggi. Desenvolvidos
> end-to-end: backend (+migration) + frontend loja + app entregador + admin, com UX.
> Safe2Pay continua fora (MR-6, final).

## MG-1 — Pacote com peso e dimensões  ✅ CONCLUÍDA (dev/test)

Hoje a entrega só tem `items_description` (texto) + quantidade + valor declarado.
Plataformas multi-veículo precisam de **peso + dimensões** (escolha de veículo, preço).

- [x] **F-MG1.1 Backend**: migration `0014` (`weight_g`, `length_cm`, `width_cm`,
      `height_cm` em `deliveries`, todos nullable) + model + `CreateDeliveryBody` +
      `DeliveryOut` + `CourierDeliveryOut` + persistência no `create_delivery` + testes.
- [x] **F-MG1.2 Loja (web)**: campos peso(kg)+dimensões(cm) no formulário + linha
      "Pacote" no detalhe da entrega.
- [x] **F-MG1.3 Entregador (app)**: tamanho do pacote (📦) na entrega ativa.
- **Aceite:** lojista cadastra pacote com peso/medidas; entregador vê na oferta;
  admin vê no detalhe. ng build + testes verdes.

## MG-2 — Painel admin com profundidade operacional (data-tables-ux)

Listas hoje são tabelas básicas. Elevar para o padrão `data-tables-ux`.

- [x] **F-MG2.1/2.2 (parcial)**: **busca** client-side + filtro de status nas listas
      de entregadores e lojas. `jx-data-table` já tem ordenação por coluna (sortable).
- [ ] **F-MG2.3**: migrar listas para `jx-data-table` (ordenação/paginação completas)
      + KPIs/analytics no painel. _Pendente — profundidade extra._
- **Aceite parcial:** listas com busca + filtro. Falta paginação/sort completos + analytics.
