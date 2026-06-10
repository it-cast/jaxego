# Document Organization — suporte a múltiplos formatos em docs/

> Referência normativa. Define como o framework lê diferentes formatos de documentação (PDFs, planilhas, wireframes HTML/JSX, imagens) e como você estrutura `docs/` e `docs/identidade-visual/` para ambos humano e Claude encontrarem o que precisam.

## Princípio central

Documentação de projeto real não é só `.md`. Vem em:
- **Pitches de negócio** em PDF/PPTX
- **Pesquisas de mercado** em planilha ou PDF
- **Wireframes** em HTML/JSX/SVG/PDF/PNG
- **Mockups** do Figma exportados como PDF/PNG
- **Contratos e ADRs** mix de DOCX e MD

O framework deve **ler todos** — mas precisa saber **o que é cada um** e **quanto peso dar**. Sem isso, Claude lê 40MB de inspiração aleatória e ignora o brief de 2 páginas que define tudo.

Solução: **INDEX.md em cada pasta** descrevendo o que há, quanto peso, quando ler.

## Formatos suportados

| Formato | Leitura | Quando usar | Observações |
|---------|---------|-------------|-------------|
| `.md` | Nativa, direta | Documentação canônica, ADRs, briefs | Preferido para texto estruturado |
| `.txt` | Nativa | Notas soltas, logs | |
| `.pdf` | Nativa (Claude lê PDFs) | Pitches, pesquisas, contratos, relatórios | Ideal quando veio de cliente/designer externo |
| `.html`, `.jsx`, `.tsx` | Como texto | **Wireframes**, protótipos visuais | Perfeito para passar wireframe gerado por IA |
| `.svg` | Como texto | Logos, ícones, wireframes vetoriais | Vê estrutura |
| `.png`, `.jpg`, `.webp` | Nativa (visão) | Mockups, screenshots, fotos | Claude vê a imagem |
| `.json`, `.yaml` | Direta | tokens, schemas, specs estruturados | Canônico para dados |
| `.csv` | Direta | Dados tabulares simples | |
| `.xlsx`, `.xls` | **Conversão necessária** | Planilhas de negócio | Ver "Conversão automática" |
| `.docx`, `.doc` | **Conversão necessária** | Documentos Word legados | Ver "Conversão automática" |
| `.pptx` | **Conversão necessária** | Apresentações | Converte para PDF |

## Conversão automática (xlsx/docx/pptx)

Esses formatos são binários — Claude não lê diretamente. O framework oferece `bin/convert-docs.sh` que gera **espelho `.md`** ao lado de cada arquivo:

```bash
bin/convert-docs.sh
# Escaneia docs/ e docs/identidade-visual/
# Para cada .xlsx: gera .xlsx.md com tabela Markdown
# Para cada .docx: gera .docx.md com texto extraído
# Para cada .pptx: gera .pptx.pdf + .pptx.md com notas
```

Resultado:
```
docs/research/
├── INDEX.md
├── concorrentes.xlsx       ← original (mantido)
├── concorrentes.xlsx.md    ← gerado (o que Claude lê)
├── pesquisa-fundador.docx
└── pesquisa-fundador.docx.md
```

Claude lê a versão `.md`. Original fica como evidência. **Re-rodar** quando o arquivo original muda.

Dependências: `pandoc` (para .docx/.pptx), `python + openpyxl` (para .xlsx). Script detecta o que tem disponível e avisa o que falta.

## Estrutura proposta de `docs/`

```
docs/
├── INDEX.md                          ← obrigatório
├── project-brief.md                  ← canônico, lido pelo bootstrap
├── business/                         ← opcional, livre
│   ├── INDEX.md
│   ├── pitch-investidores.pdf
│   ├── swot-atual.xlsx
│   ├── pesquisa-mercado-2026.pdf
│   ├── notas-fundador.md
│   └── modelo-negocio-canvas.pdf
├── research/                         ← opcional, livre
│   ├── INDEX.md
│   ├── entrevistas-usuarios.pdf
│   ├── concorrentes.xlsx
│   ├── benchmark-features.md
│   └── user-personas.pdf
├── adrs/                             ← existente, já canônico
│   ├── README.md
│   ├── ADR-template.md
│   ├── ADR-001-escolha-stack.md
│   └── ADR-002-multi-tenant.pdf     ← pode ser PDF se veio assim
└── identidade-visual/                ← canônico, ver abaixo
    └── ...
```

### Convenções

- Pasta raiz `docs/` — **INDEX.md obrigatório**, resto livre
- `project-brief.md` — **arquivo canônico**, sempre nesse path, sempre `.md`
- Subpastas temáticas (`business/`, `research/`, etc.) — livres, mas **cada uma tem INDEX.md**
- ADRs podem ser `.md` ou `.pdf` — framework lê ambos

## Estrutura proposta de `docs/identidade-visual/`

```
docs/identidade-visual/
├── INDEX.md                          ← obrigatório
├── tokens.json                       ← canônico (sprint com UI precisa)
├── design-system.md                  ← canônico (documentação humana dos tokens)
├── brand.md                          ← canônico (voz, tom, vocabulário — br/ux-copywriting)
├── logo.svg                          ← opcional
├── wireframes/
│   ├── INDEX.md                      ← obrigatório
│   ├── home.html                     ← protótipo navegável
│   ├── listing-detail.jsx            ← componente-esboço
│   ├── checkout-flow.pdf             ← fluxo exportado do Figma
│   └── mobile-nav.svg                ← wireframe vetorial
├── mockups/                          ← opcional
│   ├── INDEX.md
│   ├── figma-frames-aprovados.pdf
│   └── screens/
│       ├── home-desktop.png
│       └── home-mobile.png
└── references/                       ← opcional — inspiração externa
    ├── INDEX.md
    ├── linear-app-referencia.pdf
    └── notion-copy-patterns.md
```

### Sobre wireframes em HTML/JSX

Wireframes gerados por IA (v0, Claude, Bolt, Lovable) podem ser jogados direto em `wireframes/` como `.html` ou `.jsx`. O framework os lê como texto.

**Vantagem:** Claude "vê" o wireframe com estrutura real (hierarquia, classes, copy, comportamento). Muito mais rico que screenshot.

**Workflow típico:**
1. Pede wireframe ao v0/Lovable: "tela de criação de anúncio, mobile-first, paleta {brand tokens}, seguindo o brand.md"
2. Salva o código gerado em `docs/identidade-visual/wireframes/create-listing.html`
3. No INDEX.md da pasta, descreve: "Wireframe de referência para sprint 01. Usar como guia de layout e hierarquia; cores devem vir de tokens.json."
4. No SPRINT.md do sprint 01, Visual Contract referencia: `Baseado em docs/identidade-visual/wireframes/create-listing.html`
5. Execute-phase: Claude implementa olhando o wireframe + tokens

## Template de INDEX.md

```markdown
# docs/{pasta}/ — INDEX

> Descreva o que tem nesta pasta, para humano novo e para Claude entenderem em 30 segundos.

## Arquivos (em ordem de importância)

### Canônicos (ler sempre)
- `project-brief.md` — **fonte de verdade** sobre proposta do produto, usuário-alvo, KPIs. Atualizado em 2026-04-15.

### Alta relevância (ler ao planejar milestone/sprint relacionado)
- `business/pitch-investidores.pdf` (PDF, 24 slides) — visão de longo prazo, números de mercado. Útil para sprints de onboarding e pricing.
- `research/entrevistas-usuarios.pdf` (PDF, 40p) — síntese de 15 entrevistas. **Contradiz a hipótese inicial de onboarding curto** — ver p.12.

### Referência (ler se dúvida específica)
- `business/swot-atual.xlsx.md` — SWOT interno. Consultar em decisões de feature-priorização.
- `research/concorrentes.xlsx.md` — análise de 8 concorrentes. Consultar em sprints de feature nova.

### Histórico (geralmente não precisa)
- `business/notas-fundador-2025.md` — brainstorm inicial, parcialmente superado pelo brief atual.

## Não confiar em
- Qualquer arquivo com sufixo `-rascunho`, `-v1`, `-draft` — são versões antigas mantidas para histórico

## Última revisão deste INDEX: 2026-04-22
```

## Regras para o Claude ao ler docs

Ao iniciar um sprint ou fase:

1. **Sempre ler** `docs/INDEX.md` e `docs/project-brief.md` (canônicos)
2. **Sempre ler** `docs/identidade-visual/INDEX.md` + `brand.md` + `design-system.md` se sprint tem UI
3. **Ler sob demanda** outros arquivos conforme INDEX.md indica relevância para o sprint atual
4. **Ao ler PDF grande** (>30 páginas), fazer resumo explícito do que aprendeu antes de prosseguir — evita alucinação de "eu li, sei tudo"
5. **Se INDEX.md diz "contradiz X"**, tratar esse ponto como bloqueante — não deixar passar

## Regras para quando adicionar/atualizar doc

1. **Adicionar ao INDEX.md** na categoria correta
2. **Se substitui arquivo antigo:** mover antigo para subpasta `historico/` ou marcar com `-old`, atualizar INDEX
3. **Se é xlsx/docx/pptx:** rodar `bin/convert-docs.sh` para gerar espelho `.md`
4. **Atualizar "Última revisão"** no INDEX
5. **Commit explícito:** `docs: atualiza {arquivo} — {razão em 1 linha}`

## Bootstrap atualizado para docs multi-formato

`workflows/bootstrap.md` ganha novo passo que:

1. Escaneia `docs/` e subpastas
2. Verifica presença de `INDEX.md` em cada pasta não-vazia
3. Se faltam: oferece gerar esqueletos
4. Lista os arquivos encontrados e pergunta se confirmam

## Workflow `/gsd-docs-index`

Novo workflow que ajuda a manter os INDEX.md sincronizados. Roda quando novo arquivo foi adicionado ou estrutura mudou:

```
/gsd-docs-index
  → escaneia docs/ inteiro
  → detecta arquivos não listados em INDEX.md
  → pergunta ao humano: relevância, descrição, categoria
  → atualiza INDEX.md dos afetados
  → roda convert-docs.sh para binários sem espelho
```

## Anti-patterns

- `docs/` vira lixão com 50 arquivos e zero INDEX — Claude (e você) perde tempo
- Arquivo "definitivo" convivendo com 3 versões antigas sem marcação — Claude lê o errado
- Wireframe HTML com cores hardcoded diferentes de tokens.json — confunde implementação
- PDF de 80 páginas sem resumo em INDEX — Claude lê tudo, gasta contexto, retorna superficial
- Planilha .xlsx sem espelho .md gerado — Claude ignora
- INDEX dizendo "ler em caso de dúvida" em 40 arquivos — sem hierarquia = todo arquivo é ruído
- Pitch de 6 meses atrás tratado como autoridade atual — marcar como histórico

## Checklist ao adicionar pasta nova em `docs/`

- [ ] Criar `INDEX.md` na pasta
- [ ] Listar cada arquivo com descrição + categoria de relevância
- [ ] Se tem xlsx/docx/pptx: rodar `convert-docs.sh`
- [ ] Atualizar INDEX pai (docs/INDEX.md) mencionando a nova pasta
- [ ] Commit: `docs: adiciona pasta {nome} — {propósito}`

## Related

- Workflow: `workflows/bootstrap.md` (lê docs/ no setup)
- Workflow: `workflows/gsd-docs-index.md` (mantém INDEX atualizado)
- Script: `bin/convert-docs.sh` (gera espelhos .md de xlsx/docx/pptx)
- Reference: `references/visual-fidelity.md` (tokens.json canônico em identidade-visual)
