# Skill: parallel-orchestration

> Quando e como paralelizar execução de tasks: partição por fronteira de arquivos, classes de task que nunca paralelizam, protocolo do wave-dispatcher, custo real vs ganho real.
> Categoria: `meta` · v0.9.5 · 2026-06-09

## Propósito

`orchestration-decision-tree` decide quando usar agentes para **pesquisa e auditoria** (squads). Esta skill cobre o caso mais perigoso: paralelizar **execução de código**. Dois executores escrevendo no mesmo arquivo = corrupção silenciosa. Esta skill é a base de segurança do agent `gsd-wave-dispatcher` (v0.9.5) e da config `parallelization.task_level`.

## Quando usar (triggers)

- `parallelization.task_level: true` em config.json
- Planner montando waves de um PLAN.md
- Decidir se uma phase comporta executores paralelos

---

## 1. A única regra que importa

**Duas tasks só rodam em paralelo se os conjuntos de arquivos que tocam são DISJUNTOS — incluindo arquivos compartilhados implícitos.**

Implícitos que derrubam paralelismo (a parte que todo mundo esquece):

| Task declara tocar | Mas implicitamente toca |
|---|---|
| Endpoint novo | `api/v1/router.py` (registro), `conftest.py` (fixture nova) |
| Model novo | `alembic/versions/` (migration), `models/__init__.py` |
| Componente Angular | `app.routes.ts`, barrel `index.ts`, tokens SCSS compartilhados |
| Dependência nova | `pyproject.toml`/`package.json` + lockfile |

Se o PLAN não declara os implícitos, o dispatcher deve inferi-los — em dúvida, **serializar**. Falso negativo (serializar à toa) custa minutos; falso positivo (paralelizar conflito) custa uma tarde de debug.

## 2. Classes de task que NUNCA paralelizam entre si

1. **Migrations** — Alembic é uma corrente linear (down_revision). Duas migrations paralelas = head bifurcada. Sempre seriais, sempre primeiro na wave.
2. **Mudanças em lockfile** (`uv.lock`, `package-lock.json`) — merge de lockfile é loteria.
3. **Arquivos de registro central** (router raiz, routes, providers, barrel exports) — alternativa: cada task cria seu módulo isolado em paralelo; uma task serial final faz os registros.
4. **Config global** (settings, environment, CI yaml).
5. **Refactors largos** (rename atravessando camadas) — são exclusivos da wave.

## 3. Padrão que MAXIMIZA paralelismo seguro

O planner deve estruturar waves para criar disjunção, não esperar que ela exista:

```
Wave 1 (serial):    migrations + scaffolds + registros vazios
Wave 2 (paralelo):  feature A (arquivos próprios) ∥ feature B ∥ feature C
Wave 3 (serial):    registro/wiring de A+B+C + integration check
```

Backend ∥ frontend da mesma feature é o paralelismo mais seguro e mais valioso: repositórios de arquivos completamente disjuntos, contrato definido no PLAN (`api-design-contracts`) antes da wave.

## 4. Limites operacionais

- **Máximo 3 executores simultâneos** (`max_concurrent_agents: 3`). Acima disso, síntese e review viram gargalo e o custo de tokens cresce linear sem ganho de wall-clock equivalente.
- Cada executor paralelo: commit atômico próprio por task (rastreável), **sem** `git push`.
- Fim da wave: `make test && make lint` no conjunto integrado — falha aqui é da wave, não da task; quem diagnostica é o dispatcher, serial.
- Timeout por executor (default 10min); timeout → task volta para fila serial.

## 5. Quando NÃO vale a pena (honestidade de custo)

- Phase com <4 tasks ou tasks fortemente acopladas: overhead de partição + síntese > ganho.
- Tasks de 2–5 minutos cada: serial é mais rápido que coordenar.
- Custo de tokens: N executores ≈ N× tokens da execução. Paralelismo compra **tempo de parede**, não eficiência. Em phase exploratória/incerta, serial com contexto único produz código mais coerente.
- Regra prática: paralelize quando a phase tem ≥2 trilhas independentes óbvias (back ∥ front, módulo A ∥ módulo B) com ≥15min de trabalho cada.

## 6. Protocolo de conflito detectado em runtime

Se durante a execução um executor precisa tocar arquivo fora do seu conjunto declarado:

1. Executor **para** e reporta (não improvisa)
2. Dispatcher decide: arquivo livre → expande o lease; arquivo de outro executor → task vai para fila pós-wave
3. Registrado no EXECUTION-LOG.md (`conflict_detected`) — telemetria para calibrar o planner

## Checklist (dispatcher antes de disparar wave paralela)

- [ ] Conjuntos de arquivos por task, com implícitos inferidos
- [ ] Interseção vazia entre todos os pares
- [ ] Nenhuma task de classe proibida (§2) na partição paralela
- [ ] Contrato de integração definido no PLAN se back ∥ front
- [ ] ≤3 executores
- [ ] Plano de merge: ordem de commits + test/lint pós-wave

## Relação com outras skills

- `meta/orchestration-decision-tree` — squads de leitura (pesquisa/audit); esta cobre escrita
- `product/api-design-contracts` — pré-requisito do paralelismo back∥front
- `domain/monorepo-deploy-safety` — fronteiras de pacote que ajudam a partição
