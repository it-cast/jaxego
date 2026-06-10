# projeto/ — Pasta de entrada do seu projeto

> **Onboarding zero-fricção.** Jogue aqui tudo que você tem do projeto em qualquer formato. Rode `/gsd:ingest`. O Claude lê, organiza, e gera toda a documentação inicial (`.planning/`, `docs/`, `design-system/`).
>
> **Você não precisa preencher tudo.** Quanto mais informação, melhor o resultado — mas o framework funciona mesmo com pouco (vai perguntar o que falta).

---

## Como usar

### 1. Jogue arquivos nas subpastas certas (ou em qualquer subpasta — `/gsd:ingest` organiza)

| Subpasta | O que vai aqui | Exemplos |
|---|---|---|
| `regras-negocio/` | RNs, fluxos, processos, glossário, casos de uso | `rn-cobrancas.md`, `glossario.txt`, `casos-uso.pdf`, qualquer doc que descreva COMO o negócio funciona |
| `wireframes/` | Telas, mockups, esboços, fluxos visuais | `dashboard.png`, `checkout.fig.pdf`, `wireframe-onboarding.jpg` |
| `identidade-visual/` | Logo, paleta, tipografia, manual de marca, tokens | `logo.svg`, `paleta.png`, `manual-marca.pdf`, `tokens.json` |
| `stacks/` | Stack escolhida ou opções em consideração | `stack-frontend.md` ("Angular 19 + Ionic 8"), `stack-backend.yaml`, `infra.txt` |
| `docs-externos/` | Documentação de APIs, integrações, fornecedores, parceiros | `safe2pay-docs.pdf`, `idwall-api.md`, `manual-erp.pdf` |
| `referencias/` | Concorrentes, inspirações, padrões a seguir | `concorrente-x-print.png`, `referencias-ui.md`, `dribbble-saves.pdf` |
| `decisoes-existentes/` | ADRs já feitas, decisões já tomadas, restrições | `adr-001-mysql-nao-postgres.md`, `restricoes-juridicas.txt` |

### 2. Rode o comando

```
/gsd:ingest
```

Isso aciona o agent `gsd-project-ingestor` que:

1. **Escaneia** `projeto/` recursivamente (todos os formatos: .md, .txt, .pdf, .png, .jpg, .svg, .yaml, .json, .csv, .docx, .xlsx)
2. **Extrai informação estruturada** — entidades, fluxos, regras, decisões, identidade
3. **Classifica e cruza** — detecta conflitos, gaps, suposições não-validadas
4. **Pergunta o que falta** — apenas o essencial, em uma sessão de discovery
5. **Gera** `.planning/` completo:
   - `PROJECT.md` (visão geral)
   - `REQUIREMENTS.md` (REQs numerados, prioridade, critérios de aceite)
   - `MILESTONES.md` (releases sequenciais)
   - `ROADMAP.md` (phases dentro de cada milestone)
   - `STATE.md` (snapshot inicial)
   - `DECISIONS.md` (ADRs detectadas + decisões implícitas)
   - `TECH-DEBT.md` (vazio, mas pronto)
   - `SUGGESTIONS.md` (vazio, mas pronto)
6. **Gera** `docs/`:
   - `docs/glossario.md`
   - `docs/identidade-visual/brand.md` + `tokens.json`
   - `docs/integracoes/` (uma pasta por integração externa detectada)
   - `docs/regras-negocio/` (RNs categorizadas)
7. **Gera** `design-system/MASTER.md` (se houver identidade visual ou wireframes)

### 3. Revise e ajuste

O agent vai produzir um **DISCOVERY-REPORT.md** na raiz mostrando:
- O que foi extraído
- O que foi assumido (e por quê)
- O que ainda precisa decisão humana
- Próximos passos sugeridos

Você revisa, ajusta, e segue para `/gsd:bootstrap` ou `/gsd:autopilot`.

---

## Filosofia

- **Você nunca deveria precisar manualmente preencher `.planning/`**. Documento de bootstrap = bootstrap, não trabalho.
- **Formatos não importam**. Claude lê PDF, imagem, markdown, YAML. Você não converte nada.
- **Iterativo**. Pode rodar `/gsd:ingest` várias vezes adicionando mais arquivos. O agent é idempotente.

---

## O que NÃO vai aqui

- ❌ Código-fonte do projeto (vai em `apps/`, `src/`, etc.)
- ❌ Arquivos do framework (`.claude/`, `.planning/`)
- ❌ Output gerado (`docs/`, `design-system/`)
- ❌ Dependências (`node_modules/`, `.venv/`)

Pasta `projeto/` é **só entrada**, não saída.
