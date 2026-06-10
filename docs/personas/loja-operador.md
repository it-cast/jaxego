# Persona — Loja (operador)

**Fonte:** `projeto/regras-negocio/visao-geral.md:32`, `entidades.md:20`

Funcionário do balcão. Cria e acompanha entregas. **Não vê** financeiro nem gere plano (testes de autorização — REQ-007).

## Momentos críticos de UX
- Mesmo fluxo de "Nova entrega" do dono, sem as seções de plano/fatura
- Se a loja atingiu limite do plano ou tem fatura vencida, o operador vê o bloqueio mas a ação de resolver (upgrade/pagar) é do dono — mensagem deve orientar "fale com o responsável da loja"
