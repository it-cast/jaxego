# /gsd-docs-index — manter os INDEX.md de docs/ sincronizados

> Workflow invocado quando novos arquivos são adicionados em `docs/` ou quando a estrutura mudou. Mantém os `INDEX.md` atualizados para que Claude (e você daqui a 6 meses) saiba o que é cada arquivo.

## Quando invocar

- Depois de adicionar arquivos em `docs/` ou subpastas
- Depois de adicionar pasta nova
- Depois de rodar `bin/convert-docs.sh` (que gera espelhos `.md`)
- Como parte do bootstrap inicial (chamado automaticamente)
- Periodicamente (mensal) para limpeza

## Inputs

- Nenhum argumento obrigatório
- Opcional: `--path docs/<subpasta>` para escanear só um lugar
- Opcional: `--dry-run` para só reportar sem modificar

## O que faz

### 1. Escaneia

```
docs/
docs/identidade-visual/
docs/identidade-visual/wireframes/
docs/identidade-visual/mockups/
docs/identidade-visual/references/
docs/business/ (se existir)
docs/research/ (se existir)
docs/adrs/
```

Para cada pasta:
- Lista arquivos presentes (exceto `INDEX.md` em si)
- Lê `INDEX.md` se existir
- Detecta arquivos **não mencionados** no INDEX
- Detecta arquivos **mencionados no INDEX mas não presentes no disco** (lixo)

### 2. Reporta

Output conversacional:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 /gsd-docs-index — varredura
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

docs/
  ✓ INDEX.md presente e atualizado
  ⚠ novo arquivo sem descrição: pesquisa-2026.pdf
  ✗ INDEX menciona concorrentes.xlsx mas arquivo não existe

docs/identidade-visual/
  ✓ INDEX.md presente
  ✓ tokens.json canônico presente
  ✓ brand.md canônico presente
  ⚠ design-system.md ausente (canônico esperado)

docs/identidade-visual/wireframes/
  ✗ INDEX.md ausente
  ? 3 arquivos presentes sem descrição:
      - create-listing-mobile.html
      - checkout-flow.pdf
      - profile-settings.jsx

docs/research/
  ✓ INDEX.md presente
  ⚠ concorrentes.xlsx sem espelho .md (rodar bin/convert-docs.sh)

Total:
  3 INDEX.md precisam atualização
  1 INDEX.md precisa ser criado
  1 arquivo precisa conversão (.xlsx → .md)
  1 referência quebrada (arquivo removido mas INDEX ainda cita)

Prosseguir com atualizações interativas? [s/N]
```

### 3. Se humano confirma, para cada divergência:

**Arquivo novo sem descrição:**
```
docs/research/pesquisa-2026.pdf (3.2 MB, PDF, 24 páginas)

Descreva em 1-2 linhas:
> [humano preenche]

Relevância:
  [1] Canônico (sempre lido)
  [2] Alta (relevante em planejamento de milestones)
  [3] Referência (consultar sob demanda)
  [4] Histórico (não usar normalmente)
> [humano escolhe]

[Se PDF grande >30 pág] Gostaria que eu gere um resumo automático do PDF
agora para incluir no INDEX? Isso evita Claude ler 24 páginas toda vez. [s/N]
```

**INDEX ausente:**
```
docs/identidade-visual/wireframes/ não tem INDEX.md.

Gerar template automaticamente? [s/N]
  (cria a partir de .claude/get-shit-done/templates/INDEX-subpasta.md)
```

**Referência quebrada:**
```
docs/research/INDEX.md menciona "concorrentes.xlsx" mas arquivo não existe.

Opções:
  [1] Remover a entrada do INDEX
  [2] O arquivo foi renomeado — aponte o novo path
  [3] Deixar assim (não recomendado)
> [humano escolhe]
```

**Binário sem espelho:**
```
docs/research/concorrentes.xlsx sem .xlsx.md espelho.

Rodar bin/convert-docs.sh agora? [s/N]
```

### 4. Commita mudanças

Ao fim:
```
git add docs/
git commit -m "docs: atualiza INDEX.md de 3 pastas via /gsd-docs-index"
```

## Template gerado para INDEX ausente

Baseado em `.claude/get-shit-done/templates/INDEX-subpasta.md` (criar se não existir). Template genérico:

```markdown
# docs/{caminho}/ — INDEX

> {descrever propósito da pasta}

## Arquivos

<!-- Preencher conforme adicionar. Veja outras pastas para exemplos. -->

## Última revisão: {data}
```

## Integração com bootstrap

Passo novo no `workflows/bootstrap.md` (após leitura dos canônicos):

```
Detectei N arquivos em docs/ e subpastas sem descrição em INDEX.md.
Rodar /gsd-docs-index para organizar agora? [s/N]
```

Se humano recusa, prossegue mas avisa que alguns arquivos podem ficar sub-utilizados por falta de metadata.

## Integração com /gsd-sprint-plan

Ao quebrar milestone em sprints, workflow consulta INDEX.md das pastas relevantes:
- Se sprint tem UI → lê `docs/identidade-visual/INDEX.md` + todos canônicos
- Se há wireframe listado para a feature → lê o wireframe
- Se há mockup listado → inclui na Visual Contract

Arquivos não listados no INDEX são **ignorados** — dá autonomia para você guardar rascunhos/backups em docs/ sem bagunçar o contexto do Claude.

## Anti-patterns

- Rodar `/gsd-docs-index` e marcar todo arquivo como "canônico" — perde hierarquia, Claude lê tudo toda vez
- Deixar INDEX desatualizado por meses — arquivos novos ficam invisíveis
- Descrição genérica ("documento importante") — não ajuda Claude decidir quando usar
- Não rodar `bin/convert-docs.sh` após adicionar xlsx/docx — Claude ignora o arquivo
- Ignorar avisos de "referência quebrada" — INDEX fica mentiroso

## Checklist

- [ ] Escaneou todas as pastas em `docs/`
- [ ] Cada pasta tem `INDEX.md`
- [ ] Cada arquivo em cada pasta está listado no INDEX dessa pasta
- [ ] Binários (.xlsx, .docx, .pptx) têm espelho .md
- [ ] Descrições são concretas, não genéricas
- [ ] Relevância marcada (canônico/alta/referência/histórico)
- [ ] "Última revisão" atualizada
- [ ] Referências quebradas resolvidas

## Related

- Reference: `references/docs-organization.md` (convenções de estrutura)
- Script: `bin/convert-docs.sh` (gera espelhos de binários)
- Templates: `templates/INDEX-subpasta.md` (para pastas novas)
