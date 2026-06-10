# Templates de Workflows CI/CD — GSD v0.8

Templates de **steps** (não workflows completos) que evitam bugs descobertos em campo no diagnóstico v0.7.x.

## Como usar

Estes templates **não são drop-in**. São catálogos de steps que você deve copiar para o seu workflow real (`.github/workflows/release.yml`, `ci.yml`, etc.) ajustando paths e nomes para o seu projeto.

## Arquivos

### `release-validation.yml`

Steps que evitam **3 bugs latentes** observados no Rota Certa v1.0:

1. **`validate-placeholders` job** — bloqueia build quando `REPLACE_WITH_*`, `FIXME_*`, `<PLACEHOLDER>` etc. ainda existem em paths críticos. Um step de 30 segundos previne o caso clássico de "tag push falhou em xcodebuild com erro críptico que era apenas placeholder não substituído".

2. **`generate-changelog` job** — usa pattern `^(feat|fix)(\(.*\))?!?:` que aceita tanto `feat:` quanto `feat(scope):` (Conventional Commits com escopo). O pattern simples `^feat:` retorna 0 linhas em projetos que usam `feat(api):`, `feat(mobile):` etc. — bug observado em Rota Certa onde changelog ficaria vazio apesar de 77 feat commits.

3. **`android-version-check` job** — bloqueia se `versionCode` está hardcoded em `build.gradle`. versionCode hardcoded = rejeição garantida no segundo upload Play Console.

## Padrão de Conventional Commits aceito

```
feat: descrição                  ← aceito
feat(api): descrição             ← aceito
fix: descrição                   ← aceito
fix(mobile): descrição           ← aceito
feat!: breaking change           ← aceito (vai pro Features)
fix(api)!: breaking fix          ← aceito (vai pro Fixes)
```

NÃO entram no changelog (intencionalmente):
```
docs: ...
chore: ...
style: ...
refactor: ...
test: ...
```

Se quiser que `refactor` apareça no changelog, ajuste o pattern do grep:
```bash
PATTERN='^(feat|fix|refactor|perf)(\(.*\))?!?:'
```

## Outros padrões úteis

### Categorização de fix commits (item 10 do diagnóstico)

Para diferenciar tipos de fix em métricas, adote convenção:

```
fix(review): foo bar           ← fix por code-review (esperado, framework funcionou)
fix(integration): foo bar      ← fix por integration-checker (esperado)
fix(escape): foo bar           ← fix por bug que escapou do executor (problemático)
fix: foo bar                   ← fix genérico (cai em "outros")
```

Métrica de saúde do framework:

```bash
# Taxa de fix-por-bug-escapado / total fix
ESCAPED=$(git log --grep="^fix(escape)" --oneline | wc -l)
TOTAL_FIX=$(git log --grep="^fix" --oneline | wc -l)
echo "scale=2; $ESCAPED * 100 / $TOTAL_FIX" | bc
# Healthy: < 10%
# Concerning: 10-25%
# Bad: > 25%
```

`bin/categorize-fixes.sh` (se existir no projeto) automatiza essa análise.
