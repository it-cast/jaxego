---
name: data-visualization
category: ux-advanced
description: Visualização de dados clara e acessível — escolha de gráfico por intent, princípios Tufte, color encoding, anti-engano (eixos, escalas), bibliotecas testadas (Recharts, Chart.js, ngx-charts), exemplos de implementação React/Angular, mobile considerations e WCAG. Resolve "gráfico errado pior que tabela" e exclusão de daltônicos.
---

# Data Visualization — Visualização de Dados

> Gráfico errado = pior que tabela. Gráfico certo = insight em 3 segundos.

Esta skill define qual gráfico usar para qual intent, princípios visuais, e implementação concreta.

---

## 1. Quando esta skill é obrigatória

| Momento | Por quê |
|---|---|
| `/gsd-ui-phase` em dashboards, admin panels | Dashboards SÃO visualizações |
| Phases de relatórios e analytics | KPIs precisam de visual |
| Áugure: relatórios pós-simulação | Core do produto |
| Phase de admin com métricas | Decisões dependem de visualização clara |

## 2. Quando NÃO usar

- Phase backend pura
- Phase com dados puramente textuais
- Phase de configuração/forms

---

## 3. Decisão de gráfico por intent

### 3.1 Matriz de decisão

```
Quero mostrar...                          → Use...

Comparação entre categorias              → Bar chart (horizontal se >5 categorias)
Mudança ao longo do tempo (1 série)      → Line chart
Mudança ao longo do tempo (cumulativo)   → Area chart
Composição (todo / partes)               → Stacked bar OU pie (≤5 fatias)
Distribuição                              → Histogram OU box plot
Correlação entre 2 variáveis             → Scatter plot
Hierarquia                                → Treemap OU sunburst
Fluxo entre estados                      → Sankey diagram
Geográfico                                → Choropleth ou heatmap mapa
Status simples (1 número)                → Big number + delta
Múltiplas dimensões em 1 view            → Radar chart (com cuidado)
Frequência de eventos no tempo            → Heatmap calendar (GitHub style)
Funil de conversão                        → Funnel chart
Distribuição com mediana                 → Box plot
```

### 3.2 Decisão visual rápida

```
                 Categórico ──── Bar
                       │
         Compare ──────┤
                       │ Numérico ──── Box plot / Histogram
                       │
                       │
         Tempo ────── 1 série ──── Line
                       │
Quero mostrar          │ Múltiplas ──── Multi-line OR Small multiples
                       │
                       │ Cumulativo ──── Area
                       │
                       │
         Composição ─── Pie (≤5)
                       │
                       │ Stacked bar (>5)
                       │
                       │ Treemap (hierarquia)
                       │
                       │
         Correlação ─── Scatter
```

### 3.3 Quando NÃO usar pie chart

- **Mais de 5 fatias** — vira ilegível, use bar
- **Fatias muito próximas** — olho não distingue
- **Comparar entre múltiplos pies** — bar groups é melhor

**Regra:** pie só se ≤5 fatias com diferenças óbvias. Donut (com furo) é ok — pode mostrar total no centro.

---

## 4. Princípios fundamentais

### 4.1 Data-ink ratio (Tufte)

> Maximize a quantidade de "tinta de dado" e minimize "tinta de decoração".

```
❌ ERRADO:
- Gráfico 3D (perspectiva distorce dado)
- Gradient em barras
- Sombras
- Grid muito visível
- Bordas grossas
- Background colorido
- Título com cor brand

✅ CORRETO:
- Linhas finas
- Cor sutil (cinza para grid, brand para destaque)
- Sem decoração
- Foco no dado
```

### 4.2 Pre-attentive attributes

Cérebro processa em <250ms (sem pensar):

| Atributo | Percepção |
|---|---|
| **Cor** (saturada vs sutil) | Forte |
| **Tamanho** | Forte |
| **Posição** | Forte |
| **Forma** | Média |
| **Movimento** | Forte (use com cuidado) |
| **Orientação** | Média |

Use **1-2 atributos** para destacar o ponto crítico.

```
Exemplo: 10 barras, 1 destacada como "este mês"
- Cor: 9 cinzas + 1 brand color → destaca
- Tamanho: igual (não distorce)
- Posição: cronológica (mantém)
```

### 4.3 Anchored axes

```
✅ Eixo Y começa em 0 para barras
✅ Eixo Y truncado OK em line chart se range é pequeno relativo
❌ Eixo Y truncado em barras (manipula percepção, exagera diferenças)
```

**Exemplo enganoso (não fazer):**

```
Barras com Y começando em 95:
Mês 1: 96
Mês 2: 97
Mês 3: 98
→ Visualmente parece DOBRO, mas é 2% de diferença
```

**Exemplo correto:**

```
Barras com Y começando em 0:
Mês 1: 96
Mês 2: 97
Mês 3: 98
→ Visualmente parece IGUAL (que é a verdade)
```

Para line chart de longo prazo, truncar Y pode ser ok (range relevante).

### 4.4 Color encoding

| Tipo de dado | Tipo de paleta | Quando |
|---|---|---|
| **Categórico** (categorias distintas) | Paleta qualitativa, 6 cores max | Bar chart com 5 produtos |
| **Sequencial** (low → high) | Gradiente de mesma matiz | Heatmap de intensidade |
| **Divergente** (extremos com neutro) | Diverging (red-neutral-blue) | Sentiment, correlação |
| **Bivariate** (2 variáveis) | Combinação | Mapas demográficos |

**Paletas testadas (ColorBrewer + custom):**

```
Categórico (6 cores distinguíveis):
#3b82f6 (blue)
#10b981 (emerald)
#f59e0b (amber)
#ef4444 (red)
#8b5cf6 (violet)
#06b6d4 (cyan)

Sequencial (gradient):
['#eff6ff', '#dbeafe', '#bfdbfe', '#93c5fd', '#60a5fa', '#3b82f6', '#2563eb', '#1d4ed8']

Divergente (red-neutral-blue):
['#dc2626', '#fca5a5', '#fee2e2', '#f5f5f5', '#dbeafe', '#93c5fd', '#2563eb']

Daltônico-safe:
#0173b2 (blue), #de8f05 (orange), #029e73 (green), #cc78bc (pink),
#ca9161 (brown), #fbafe4 (light pink), #949494 (gray)
```

### 4.5 Acessibilidade

#### Contraste

```
Lines / borders: 3:1 mínimo
Texto / labels: 4.5:1 mínimo
```

#### Não confiar só em cor

```
✅ Status com cor + ícone + label direto
❌ Status só com cor (excluí daltônicos)

✅ Múltiplas séries: cor + linha tracejada/sólida + label inline
❌ Múltiplas séries só com cor
```

#### Daltonismo (8% homens)

Combinações safe:
- Azul + Laranja (não verde + vermelho)
- Roxo + Amarelo
- Azul-claro + Vermelho-escuro

Sempre testar com simulador (Sim Daltonism, Stark plugin).

#### Alt text

```jsx
<img alt="Gráfico de barras: Vendas mensais 2026, com pico em julho (R$ 50k)
          e queda em outubro (R$ 25k)" />
```

#### View as data

Sempre oferecer "exportar como tabela" ou "ver dados".

---

## 5. Implementação

### 5.1 Bibliotecas recomendadas

| Lib | Uso | Stack |
|---|---|---|
| **Recharts** | Gráficos comuns | React |
| **Chart.js** | All-purpose | Vanilla JS |
| **D3.js** | Visualizações customizadas | Qualquer |
| **Visx (Airbnb)** | React + D3 híbrido | React |
| **Plotly** | Interativos científicos | React/Vue/etc |
| **Apache ECharts** | Dashboards grandes | Qualquer |
| **Tremor** | Dashboards prontos | React |
| **Nivo** | React themed | React |
| **ngx-charts** | Angular (D3-based) | Angular |
| **Apex Charts** | Angular alternativa | Angular |

**Recomendação por contexto:**

```
React simples → Recharts
React + custom → Visx
Angular → ngx-charts
Mobile (Ionic) → Chart.js
Dashboard grande → ECharts ou Tremor
Custom complexo → D3 puro
```

### 5.2 Recharts (React) — Bar chart

```jsx
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const data = [
  { month: 'Jan', revenue: 32000, costs: 18000 },
  { month: 'Fev', revenue: 38000, costs: 22000 },
  { month: 'Mar', revenue: 45000, costs: 26000 },
  { month: 'Abr', revenue: 42000, costs: 25000 },
];

function RevenueChart() {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <XAxis
          dataKey="month"
          stroke="var(--color-text-secondary)"
        />
        <YAxis
          stroke="var(--color-text-secondary)"
          tickFormatter={(value) => `R$ ${(value / 1000).toFixed(0)}k`}
        />
        <Tooltip
          contentStyle={{
            background: 'var(--color-surface-raised)',
            border: '1px solid var(--color-border-default)',
            borderRadius: '8px'
          }}
          formatter={(value) => `R$ ${value.toLocaleString('pt-BR')}`}
        />
        <Legend />
        <Bar dataKey="revenue" fill="#3b82f6" name="Receita" />
        <Bar dataKey="costs" fill="#94a3b8" name="Custos" />
      </BarChart>
    </ResponsiveContainer>
  );
}
```

### 5.3 ngx-charts (Angular) — Line chart

```typescript
import { Component, signal } from '@angular/core';
import { LineChartModule } from '@swimlane/ngx-charts';

@Component({
  selector: 'revenue-line-chart',
  standalone: true,
  imports: [LineChartModule],
  template: `
    <ngx-charts-line-chart
      [view]="view"
      [results]="data()"
      [scheme]="colorScheme"
      [xAxis]="true"
      [yAxis]="true"
      [legend]="true"
      [showXAxisLabel]="true"
      [showYAxisLabel]="true"
      xAxisLabel="Mês"
      yAxisLabel="Receita (R$)"
      [yAxisTickFormatting]="formatYAxis">
    </ngx-charts-line-chart>
  `
})
export class RevenueLineChartComponent {
  view: [number, number] = [700, 400];

  data = signal([
    {
      name: 'Receita',
      series: [
        { name: 'Jan', value: 32000 },
        { name: 'Fev', value: 38000 },
        { name: 'Mar', value: 45000 },
        { name: 'Abr', value: 42000 }
      ]
    }
  ]);

  colorScheme = {
    domain: ['#3b82f6']
  } as any;

  formatYAxis(value: number): string {
    return `R$ ${(value / 1000).toFixed(0)}k`;
  }
}
```

### 5.4 KPI card (big number + delta)

```jsx
function KPICard({ label, value, previousValue, format = 'number' }) {
  const delta = ((value - previousValue) / previousValue) * 100;
  const positive = delta > 0;

  const formatValue = (v) => {
    if (format === 'currency') return `R$ ${v.toLocaleString('pt-BR')}`;
    if (format === 'percent') return `${v.toFixed(1)}%`;
    return v.toLocaleString('pt-BR');
  };

  return (
    <div className="kpi-card">
      <p className="kpi-label">{label}</p>
      <p className="kpi-value">{formatValue(value)}</p>
      <p className={`kpi-delta ${positive ? 'positive' : 'negative'}`}>
        {positive ? '↑' : '↓'} {Math.abs(delta).toFixed(1)}% vs mês anterior
      </p>
    </div>
  );
}

// CSS
.kpi-card {
  padding: var(--space-6);
  background: var(--color-surface-raised);
  border-radius: 12px;
  border: 1px solid var(--color-border-default);
}

.kpi-label {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
}

.kpi-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
}

.kpi-delta.positive {
  color: var(--color-feedback-success);
  font-size: 13px;
}

.kpi-delta.negative {
  color: var(--color-feedback-danger);
  font-size: 13px;
}
```

---

## 6. Mobile considerations

### 6.1 Adaptações em telas pequenas

```
Desktop:
- 7 dados visíveis em line chart
- Labels horizontais
- Tooltip on hover

Mobile:
- 5 dados visíveis (zoom em range específico)
- Labels rotacionados (45deg) ou abreviados
- Tooltip on tap
- Pinch-to-zoom em gráficos densos
```

### 6.2 Touch ≠ hover

```javascript
// ❌ ERRADO — só hover
<rect onMouseOver={showTooltip} />

// ✅ CORRETO — touch e mouse
<rect
  onMouseOver={showTooltip}
  onTouchStart={showTooltip}
  onClick={toggleTooltip}
/>
```

### 6.3 Orientação

Para gráficos amplos (timeline, comparison), incentivar landscape:

```jsx
<div className="chart-container">
  <ChartComponent />
  {window.innerHeight > window.innerWidth && window.innerWidth < 768 && (
    <div className="rotate-hint">
      Gire o celular para ver completo
    </div>
  )}
</div>
```

### 6.4 Skeleton enquanto carrega

```jsx
{isLoading ? (
  <div className="chart-skeleton">
    <div className="bar-skeleton" style={{ height: '60%' }} />
    <div className="bar-skeleton" style={{ height: '40%' }} />
    <div className="bar-skeleton" style={{ height: '80%' }} />
    <div className="bar-skeleton" style={{ height: '50%' }} />
  </div>
) : (
  <Chart data={data} />
)}
```

---

## 7. Casos práticos por contexto

### 7.1 Dashboard SaaS (KPIs + gráficos)

```
Layout: 4 KPI cards no topo + 2 gráficos médios + 1 tabela

KPIs (big numbers):
- MRR atual + delta vs mês anterior
- Active users + delta
- Churn rate + delta
- LTV + delta

Gráficos:
- Line: receita por mês (12 meses) - identificar tendência
- Bar: top 5 features por uso - priorizar dev

Tabela:
- Lista de usuários com filtros
```

### 7.2 Relatório Áugure (pós-simulação)

```
Estrutura do relatório (70 páginas):

Página 1: Sumário executivo
- KPI: Probabilidade de viabilidade (gauge 0-100%)
- Big number: Capital recomendado
- Big number: Tempo até break-even

Páginas 2-3: Mercado
- Bar chart: TAM/SAM/SOM
- Line chart: Tendência do nicho 5 anos

Páginas 4-7: Concorrência
- Treemap: market share por competidor
- Scatter: posicionamento (preço x qualidade)

Páginas 8-15: Cenários
- Multi-line: 3 cenários (otimista/base/pessimista)
- Stacked area: estrutura de custos por mês

Páginas 16-25: Sensibilidade
- Tornado chart: variáveis de maior impacto

[...]
```

### 7.3 Mobile health app

```
Daily summary (1 tela):
- Big number: passos hoje
- Progress ring: % da meta
- Mini line: últimos 7 dias

Weekly view:
- Bar chart simplificado (7 barras)
- Highlight do recorde

Monthly view:
- Heatmap calendar (GitHub style)
- Cor saturada = mais ativo
```

### 7.4 E-commerce admin

```
Vendas (dashboard principal):
- KPI: revenue hoje + delta
- Line: revenue últimos 30 dias
- Bar: top 10 produtos
- Funnel: views → cart → checkout → paid

Geográfico:
- Choropleth Brasil: vendas por estado
- Drill-down para cidade
```

---

## 8. Anti-patterns com correção

### Anti-pattern 1: Pie com 10 fatias

```
❌ ERRADO:
Pie chart com 10 categorias de produto
→ ilegível, fatias muito pequenas

✅ CORRETO:
Bar chart horizontal com 10 categorias
→ comparação clara, espaço para labels
```

### Anti-pattern 2: Gráfico 3D

```
❌ ERRADO:
3D bar / 3D pie
→ perspectiva distorce dado

✅ CORRETO:
2D limpo
→ valores legíveis precisamente
```

### Anti-pattern 3: Eixo Y truncado em barras

```
❌ ERRADO (engana):
Y começa em 95
Mês 1: 96 (1 unidade visível)
Mês 2: 99 (4 unidades visíveis)
→ Parece 4x maior, mas é 3% diferença

✅ CORRETO:
Y começa em 0
→ Diferença visualizada honestamente
```

### Anti-pattern 4: Cor random

```
❌ ERRADO:
10 séries com 10 cores aleatórias
→ olho perde categorias

✅ CORRETO:
- Destaque: 1-2 séries em brand color
- Apoio: cinzas
- Categórico: paleta qualitativa testada (max 6)
```

### Anti-pattern 5: Tooltip não funciona em mobile

```
❌ ERRADO:
Tooltip on hover (mouse-only)
→ usuário mobile não vê

✅ CORRETO:
Tooltip on tap + hover
→ funciona em todas as plataformas
```

### Anti-pattern 6: Gráfico sem contexto

```
❌ ERRADO:
"Vendas: 234"
(sem comparação, sem unidade clara)

✅ CORRETO:
"Vendas: 234 (↑ 12% vs mês anterior)"
"Meta: 300"
[barra com progress até 78% da meta]
```

### Anti-pattern 7: Decimais demais

```
❌ ERRADO:
R$ 1.234,5678 (excesso de precisão)
2.456789 unidades

✅ CORRETO:
R$ 1.234,57 (precisão financeira padrão)
2.456 unidades (sem decimais quando irrelevante)
```

### Anti-pattern 8: Status só por cor

```
❌ ERRADO:
Linhas em vermelho = ruim, verde = ok
→ daltônicos confundem

✅ CORRETO:
Vermelho com X icon = ruim
Verde com check = ok
+ label "ruim/ok" inline
```

---

## 9. Checklist de validação

```
ESCOLHA:
□ Gráfico match com intent (compare/temporal/composition)?
□ Tipo de chart certo para tipo de dado?
□ Pie chart só se ≤5 fatias?
□ Eixo Y começa em 0 para barras?

DESIGN:
□ Data-ink ratio alto (sem decoração)?
□ Cor brand restrita ao destaque?
□ Tipografia coerente com sistema?
□ Spacing usa tokens?

ACESSIBILIDADE:
□ Contraste 3:1 mínimo?
□ Status NÃO só por cor (cor + ícone + label)?
□ Alt text descritivo?
□ Daltônico testado (Sim Daltonism)?
□ Tabela equivalente disponível?

INTERATIVIDADE:
□ Tooltip on tap (mobile) e hover (desktop)?
□ Drill-down se aplicável?
□ Pinch-to-zoom em mobile?
□ Skeleton durante load?

CONTEÚDO:
□ Título descritivo do gráfico?
□ Eixos labelados?
□ Unidades claras?
□ Legend posicionada (não escondida)?
□ Decimais apropriados (não excesso)?

PERFORMANCE:
□ Lazy load se off-screen?
□ Throttle em real-time charts?
□ Aggregation server-side se >1000 pontos?
```

Se <17 checks, gráfico precisa revisão.

---

## 10. Como integra com outras skills

### 10.1 → `quality/color-system`
Cores de chart vêm de tokens (categórico/sequencial/divergente).

### 10.2 → `quality/typography-scale`
Labels, eixos, legend usam tokens tipográficos.

### 10.3 → `quality/spacing-system`
Margins, paddings em containers de chart.

### 10.4 → `quality/accessibility-pro`
WCAG, alt text, daltonismo, view as data.

### 10.5 → `ux-advanced/saas-dashboard-patterns`
Layout dos charts em dashboards.

### 10.6 → `ux-advanced/loading-states`
Skeleton de chart enquanto carrega.

### 10.7 → PLAN.md de phase

```markdown
## Phase 6 — Dashboard de relatórios

### Skills Consultadas
- `ux-advanced/data-visualization` — escolha de gráfico, paleta
- `ux-advanced/saas-dashboard-patterns` — layout
- `ux-advanced/loading-states` — skeleton de chart
- `quality/color-system` — paleta categórica safe
- `quality/accessibility-pro` — WCAG e daltonismo
```

---

## 11. Erros comuns

### Erro 1: "Bonito > correto"
Gráfico bonito que distorce dado é pior que tabela honesta.
**Fix:** clareza > estética. Tufte over Tableau.

### Erro 2: Pular daltonismo
Excluí 8% dos homens.
**Fix:** sempre testar com simulador.

### Erro 3: Sem alt text
Quebra para screen readers.
**Fix:** alt text descritivo + tabela equivalente.

### Erro 4: Real-time sem throttle
Performance ruim, browser trava.
**Fix:** throttle 1Hz mínimo, aggregate server-side.

### Erro 5: Mobile pensado depois
Gráficos densos em telas pequenas = ilegíveis.
**Fix:** mobile-first em design de chart.

---

## 12. Referências

- **Edward Tufte** — "The Visual Display of Quantitative Information" (canônico)
- **Stephen Few** — "Now You See It" (dashboards)
- **Cole Knaflic** — "Storytelling with Data" (acessível, prático)
- **D3.js examples** — d3js.org/examples
- **Observable** — observablehq.com (notebooks de data viz)
- **ColorBrewer** — colorbrewer2.org (paletas testadas)

---

**Última atualização:** v0.7.1 (densificação batch 2)
**Densidade:** 12 seções, matriz de decisão completa, princípios Tufte, snippets React/Angular, paletas testadas, mobile considerations, 4 contextos práticos, anti-patterns com correção, checklist de 18 itens
