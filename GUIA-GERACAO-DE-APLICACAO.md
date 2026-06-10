# Guia de Geração de Aplicação — do zero ao deploy (v0.9.7)

> O caminho completo em ordem de execução: escolha de modelos → documentação →
> ingest → bootstrap → autopilot → deploy. Cada passo diz O QUE fazer, ONDE e
> POR QUÊ. Tempo de leitura: 10 min. Tempo de setup de um projeto novo: ~1h
> (sendo ~50min de documentação — que é onde o resultado é decidido).

---

## Passo 0 — Instalação (uma vez por máquina/projeto)

```bash
# Pré-requisitos: Node 18+, Python 3.10+, Git
# 1. Descompacte o framework na RAIZ do projeto
# 2. Sanidade:
bash tests/framework/run-all.sh                          # esperado: 11/11
node .claude/get-shit-done/bin/gsd-tools.cjs --help      # mostra usage
```

## Passo 1 — Escolha do perfil de modelos (1 comando, vale para o projeto todo)

O framework resolve o modelo **por papel de agente**, não global. Você escolhe
o perfil uma vez; daí em diante cada agente é disparado no modelo certo
automaticamente (planner forte, executor econômico, checkers baratos).

```bash
node .claude/get-shit-done/bin/gsd-tools.cjs config-set-model-profile balanced
```

| Perfil | Quando usar |
|---|---|
| `balanced` ← **recomendado para começar** | Opus só no planner; Sonnet em execução/research/verificação. Melhor custo-benefício para field test. |
| `adaptive` | Igual ao balanced + Opus no debugger + Haiku nos checkers de volume. Para quem otimiza custo em API paga. |
| `quality` | Opus em tudo que decide. Phases de arquitetura crítica, quota sobrando. |
| `budget` | Sonnet escreve, Haiku checa. Phases de baixo risco / alto volume. |
| `inherit` | Segue o modelo da sessão. Obrigatório com providers não-Anthropic. |

Para escalar pontualmente: `/gsd:debug` (no perfil adaptive resolve para Opus
— escalada implícita quando algo empaca). Não existe escalada automática em
falha de gate — se Sonnet falhar verificação repetidamente, suba o perfil da
phase ou debugue com `/gsd:debug`.

## Passo 2 — Documentação: onde, o quê, em que formato

**Esta é a etapa que decide a qualidade de tudo.** Regra de ouro: 5 documentos
densos > 30 rasos. Tudo vai em **`projeto/`** (só entrada — nunca código nem
output):

```
projeto/
├── regras-negocio/       ← 60% do resultado vem daqui
│   ├── fluxo-principal.md       (passo a passo COM exceções e estados de erro)
│   ├── regras.md                (RN-001, RN-002... numeradas, com condição→ação)
│   ├── glossario.md             (vocabulário do domínio — evita Claude inventar termos)
│   └── casos-de-uso.md
├── decisoes-existentes/  ← o mais negligenciado; o 2º mais valioso
│   └── adrs.md                  (CADA restrição já decidida: stack, o que foi
│                                 rejeitado e POR QUÊ. O que não estiver aqui
│                                 será re-discutido, queimando tokens)
├── wireframes/           ← fonte de verdade visual (ver Passo 2.1)
│   ├── 01-login.html            (numere na ordem do fluxo)
│   ├── 02-dashboard.html
│   └── 03-detalhe.png           (imagem também vale — fidelidade menor)
├── identidade-visual/
│   ├── tokens.json              (cores/espaçamento/tipografia — Gate 2 valida contra ele)
│   ├── brand.md                 (tom de voz, do's & don'ts)
│   └── logo.svg
├── stacks/
│   └── stack.md                 (escolhida OU em consideração, com restrições)
├── docs-externos/               (PDFs/MDs de APIs que vai integrar: Pagar.me, etc.)
└── referencias/                 (prints de concorrentes, inspirações)
```

**Formatos aceitos:** `.md .txt .pdf .png .jpg .svg .yaml .json .csv .docx .xlsx`
— e em `wireframes/`: `.html .htm .jsx .tsx .vue .svelte` (com tratamento especial).
Prefira `.md` para texto (zero conversão, máxima extração).

**Não quer escrever isso à mão?** Use o `GERADOR-DE-DOCUMENTACAO.md` (na raiz
do framework): cole o prompt numa conversa com Claude, discuta o projeto, e ele
gera todos esses arquivos prontos nas pastas certas. Ver seção própria abaixo.

### Passo 2.1 — Wireframes: HTML é fonte de verdade ENFORCED (v0.9.7)

Se você colocar wireframe **HTML** (incluindo output de Lovable/v0/bolt, pasta
inteira ou arquivos), a fidelidade é garantida por uma cadeia de 4 elos, não
por boa vontade:

1. `gsd-tools wireframe-contract` extrai do DOM um **contrato verificável**:
   regiões, headings, botões e links (texto + destino), inputs por name,
   estados, cores
2. O `ui-phase` é **obrigado** a cobrir cada item do contrato no UI-SPEC — ou
   declarar a divergência em `deviations:` com razão. Omissão silenciosa não passa
3. O `ui-checker` (Dimension 7) **re-roda o contrato** e bloqueia se algo sumiu
4. O Gate 8 confere os elementos do contrato **no código construído**

Divergir é permitido (às vezes o wireframe está errado) — divergir **em
silêncio** não é. Cada mudança vira decisão registrada que você revisa.

Limites honestos: o contrato cobre o DOM **estático** (HTML montado por JS em
runtime não aparece — raro em wireframes). Wireframe-**imagem** (.png/.pdf) tem
fidelidade visual validada pelo researcher, sem contrato mecânico — se
fidelidade pixel-a-estrutura importa, use HTML.

## Passo 3 — Rodar (um comando)

```
/gsd:go
```

O que acontece e onde VOCÊ entra:

```
/gsd:go detecta "projeto novo com docs em projeto/"
  ├─ /gsd:ingest  → lê tudo, gera DISCOVERY-REPORT.md
  │   🛑 PAUSA 1 — revise COM CALMA (20 min aqui economizam dias):
  │        o que foi extraído, o que foi ASSUMIDO, o que falta decidir
  ├─ /gsd:bootstrap → gera .planning/ completo (PROJECT, REQUIREMENTS,
  │                   MILESTONES, ROADMAP, STATE, DECISIONS)
  │   🛑 PAUSA 2 — aprove o ROADMAP (ponto mais barato de corrigir rumo)
  └─ /gsd:autopilot M1 → executa o milestone phase a phase
      🛑 pausa só em: gate bloqueado, falha de verificação, ADR, fim de milestone
```

Por phase, automaticamente: discuss → ui-phase (se has_ui — com contrato de
wireframe) → research → plan (Gate 3 valida skills) → execute (paralelo se
`parallel-hint` e config ligado) → verify (Gate 8 por script).

**Nos 3 primeiros sprints, mantenha o ritual da Regra 5:** após cada plan,
exija no chat que Claude abra cada skill obrigatória, cite 3 regras literais
e declare o que vai aplicar — antes de codar.

## Passo 4 — Paralelismo (opcional, ligar quando confiar)

```json
// .planning/config.json
"parallelization": { "enabled": true, "task_level": true,
                     "max_concurrent_agents": 3, "wave_dispatcher": true }
```
A partição é calculada por `gsd-tools partition` (determinístico — migrations
e lockfiles nunca paralelizam; em dúvida, serial). Custo ~N× tokens por N
executores; o ganho de wall-clock é projeção até sua telemetria confirmar.

## Passo 5 — Fechamento e deploy

```
/gsd:verify-phase N          # Gate 8 — bloqueia FAIL-BLOCK por script
/gsd:complete-milestone
/gsd:ship                    # checklist de release
bin/deploy-atomic.sh         # ou deploy-docker.sh (backup pré-migração OBRIGATÓRIO)
```

## Passo 6 — O que fecha o ciclo (não pule)

```bash
bin/collect-framework-telemetry.sh --export
```
Preencha os `<FILL>` de `interpretacao_humana`. Sem isso o framework nunca
aprende com seu uso real — e toda iteração futura volta a ser especulação.

---

## Rotina semanal (10 min)

```
/gsd:td-review        # dívida envelhecendo
/gsd:suggestions      # triagem de sugestões acumuladas
/gsd:go --status      # onde estou
```

## Quando algo der errado

| Situação | Faça |
|---|---|
| Perdido | `/gsd:go --status` |
| STATE divergiu | `/gsd:reconcile-state` |
| Gate travou | leia a mensagem; corrija; ou override com `--reason` (vai pra DECISIONS) |
| Task empacada | `/gsd:debug` (escala para modelo forte no perfil adaptive) |
| Comando estranho | `docs/KNOWN-LIMITS.md` |
