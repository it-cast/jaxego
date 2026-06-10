# Skill: search-filter-ux

> Busca e filtros que funcionam: hierarquia busca vs filtro, chips de filtro ativo, URL como estado, debounce/cancelamento, zero-results inteligente, FULLTEXT MySQL no backend.
> Categoria: `ux-advanced` · v0.9.5 · 2026-06-09

## Propósito

Busca e filtragem são a segunda interação mais comum em SaaS depois de tabelas — e a primeira a ser feita errado: filtro que não mostra o que está ativo, busca que não cancela request, estado perdido no F5. Esta skill fecha o trio com `data-tables-ux`.

## Quando usar (triggers)

- Qualquer listagem com busca por texto ou filtros
- Telas de catálogo, histórico, relatórios com período

---

## 1. Busca vs filtro — hierarquia

- **Busca** (texto livre): quando usuário sabe O QUE procura. Campo único, proeminente, placeholder específico ("Buscar por nome, e-mail ou CPF…" — listar os campos reais que a busca cobre, nunca "Buscar…" genérico).
- **Filtro** (atributos): quando usuário quer REDUZIR o conjunto. Dropdowns/chips ao lado ou abaixo da busca.
- Os dois se combinam com AND. Nunca esconder a busca dentro do painel de filtros.

## 2. Estado visível — regra de ouro

**Todo filtro ativo é visível e removível individualmente:**

```
[Busca: "joão"] ×   [Status: Pendente] ×   [Período: últimos 30 dias] ×   Limpar tudo
```

- Chips abaixo da barra; contador no botão de filtros ("Filtros (3)")
- "Limpar tudo" aparece com 2+ filtros ativos
- Resultado sempre informa contexto: "37 resultados para 'joão' com 2 filtros"

## 3. URL como fonte de verdade

Filtros e busca vivem na query string (`?q=joão&status=pendente&page=2`):

- F5 mantém estado; link é compartilhável; voltar do detalhe preserva tudo
- Angular: sincronizar via `Router` + `queryParams`, não estado solto em service
- Exceção: filtros transientes em modal mobile podem aplicar em lote ("Aplicar (3)")

## 4. Comportamento de digitação

- Debounce 300ms; mínimo 2 caracteres para disparar (ou Enter explícito)
- `switchMap` — request anterior **cancelado**, nunca race condition de resultado velho chegando depois
- Loading inline no campo (spinner discreto), resultados antigos visíveis até os novos chegarem
- Esc limpa o campo

## 5. Zero resultados — nunca beco sem saída

Em ordem de preferência:

1. Dizer exatamente o que não retornou: "Nenhum pedido para 'joao silva' com status Cancelado"
2. Oferecer relaxamento: "Remover filtro de status" / "Buscar em todos os períodos"
3. Sugerir correção quando houver fuzzy match disponível ("Você quis dizer 'João da Silva'?")

## 6. Backend (MySQL 8 + FastAPI)

- Texto curto e prefixo: `LIKE 'termo%'` com index — nunca `LIKE '%termo%'` em coluna sem FULLTEXT em tabela grande
- Busca real em texto: `FULLTEXT ... IN NATURAL LANGUAGE MODE` (ver `mysql-schema-design` §FULLTEXT); acentos: collation `utf8mb4_0900_ai_ci` já é accent-insensitive — não normalizar na mão
- Filtros: parâmetros tipados no endpoint (Pydantic), whitelist de campos ordenáveis/filtráveis — **nunca** interpolar nome de coluna vindo do cliente (SQL injection por coluna)
- Resposta de lista sempre inclui `total` para o contador de resultados

## 7. Filtros de período (caso especial pt-BR)

- Presets primeiro: Hoje / 7 dias / 30 dias / Este mês / Personalizado
- Personalizado: dois campos dd/mm/aaaa com máscara (ver `br/brazilian-forms`), validar início ≤ fim
- Timezone: gravar UTC, filtrar convertendo o range do timezone do usuário — "hoje" do usuário ≠ "hoje" UTC

## Checklist de review

- [ ] Placeholder lista os campos cobertos pela busca
- [ ] Chips de filtros ativos com remoção individual
- [ ] Estado na URL, F5 preserva
- [ ] Debounce + cancelamento de request
- [ ] Zero-results com ação de saída
- [ ] Whitelist de campos no backend
- [ ] `total` no response

## Relação com outras skills

- `ux-advanced/data-tables-ux` — a tabela que exibe o resultado
- `br/brazilian-forms` — máscaras de período/CPF na busca
- `domain/mysql-schema-design` — FULLTEXT e indexes
- `domain/fastapi-production-patterns` — endpoint de lista parametrizado
