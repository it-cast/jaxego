# Skill: data-tables-ux

> Tabelas de dados que não envergonham: densidade, paginação, ordenação, seleção em massa, responsividade, estados vazios/erro, performance com milhares de linhas. Angular Material table + Ionic.
> Categoria: `ux-advanced` · v0.9.5 · 2026-06-09

## Propósito

Todo painel admin e SaaS B2B é, no fundo, uma coleção de tabelas. É o componente mais usado e o mais maltratado por código gerado: tabela sem paginação, sem estado vazio, que quebra no mobile e trava com 5 mil linhas. Esta skill define a tabela canônica.

## Quando usar (triggers)

- Phase com painel admin, listagem, relatório tabular, dashboard com grid
- Qualquer `mat-table`, lista com colunas, export CSV

---

## 1. Decisão: tabela ou cards?

| Contexto | Use |
|---|---|
| Desktop admin, comparação entre linhas, >4 colunas | Tabela |
| Mobile, conteúdo heterogêneo, ação primária por item | Cards/lista |
| Responsivo com ambos | Tabela no desktop → cards no breakpoint `md` para baixo (não tabela espremida com scroll horizontal de 8 colunas) |

Scroll horizontal só é aceitável com: primeira coluna fixa (sticky) + indicação visual de overflow + máximo de colunas secundárias.

## 2. Anatomia obrigatória

Toda tabela do projeto tem, sem exceção:

1. **Header sticky** ao rolar
2. **Paginação** — server-side a partir de 100 registros possíveis; page sizes 10/25/50; default 25
3. **Ordenação** server-side nas colunas que o usuário realmente ordena (data, valor, status) — não em todas por reflexo
4. **Estado vazio** com 3 variantes distintas (ver `empty-states-polish`): primeira vez (CTA de criação), busca sem resultado (CTA limpar filtros), erro de carregamento (CTA tentar de novo)
5. **Loading**: skeleton rows (5 linhas) na carga inicial; overlay sutil + dados antigos visíveis em refetch (nunca tela branca entre páginas)
6. **Densidade**: linha 44–52px admin denso, 56–64px conteúdo confortável; alinhamento — texto à esquerda, números à direita, datas formato pt-BR consistente

## 3. Colunas — regras

- Máximo 7 colunas visíveis por default; resto atrás de "colunas" configurável (persistir escolha por usuário)
- Dinheiro: alinhado à direita, `R$ 1.234,56`, tabular figures (`font-variant-numeric: tabular-nums`)
- Status: badge com cor de token semântico (`--color-success` etc.), nunca hex solto — texto sempre junto da cor (acessibilidade)
- Truncar com ellipsis + tooltip no hover; nunca quebrar layout
- Coluna de ações: à direita, ícones com `aria-label`, máximo 2 visíveis + menu kebab para o resto

## 4. Seleção em massa

- Checkbox por linha + "selecionar página" no header; "selecionar todos os N resultados" como ação explícita separada (padrão Gmail)
- Barra de ações em massa substitui o header da tabela quando há seleção: `N selecionados — [Ação] [Ação] [Cancelar]`
- Ação destrutiva em massa: confirmação com o número exato ("Excluir 37 pedidos?")

## 5. Performance

- Server-side pagination + filtros: a regra. Client-side só com garantia de <1.000 registros para sempre
- Virtual scroll (`cdk-virtual-scroll`) apenas para listas contínuas sem paginação (feeds); não misturar com paginação
- `trackBy` obrigatório em `@for` — sem isso Angular recria DOM da tabela inteira a cada refetch
- Debounce 300ms em filtro de texto; cancelar request anterior (switchMap)

## 6. Mobile (Ionic)

- Breakpoint `< md`: cards com hierarquia — título (campo principal), 2–3 campos secundários, badge de status, swipe actions (`ion-item-sliding`) para as 2 ações principais
- Pull-to-refresh no lugar do botão refresh
- Filtros viram bottom sheet/modal, não toolbar espremida

## 7. Export

- Export CSV/Excel exporta **o resultado filtrado completo** (server-side), não a página visível — usuário sempre assume isso
- 1.000 linhas: job assíncrono + notificação/download quando pronto, com feedback imediato ("estamos preparando seu arquivo")

## Checklist de review

- [ ] Paginação server-side (ou justificativa <1k escrita no PLAN)
- [ ] 3 estados vazios distintos implementados
- [ ] Skeleton na carga inicial, refetch sem tela branca
- [ ] `trackBy` presente
- [ ] Mobile: cards ou padrão justificado, nunca tabela espremida
- [ ] Status com cor de token + texto
- [ ] Ações com `aria-label`

## Relação com outras skills

- `ux-advanced/saas-dashboard-patterns` — onde a tabela vive
- `ux-advanced/search-filter-ux` — filtros acima da tabela
- `ux-advanced/empty-states-polish` — os 3 vazios
- `quality/accessibility-pro` — navegação por teclado, roles ARIA de grid
- `domain/fastapi-production-patterns` — endpoint de lista paginado que alimenta tudo isso
