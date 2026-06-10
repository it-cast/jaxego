# Skill: senior-quality-bar

> A Definição de Pronto de uma equipe sênior, codificada como checklist verificável. Não é aspiração — é o que o Gate 8 bloqueia. Cobre desenvolvimento, segurança e deploy. Toda phase com código é medida contra esta barra.
> Categoria: `quality` · v0.9.5 · 2026-06-09

## Propósito

O framework tinha 7 gates, mas o último (test+lint verde) é o **piso**, não a barra sênior. "Compila e os testes passam" é o mínimo de um júnior competente — não o padrão de uma equipe sênior. Esta skill define o que separa output mediano de output sênior, em critérios **observáveis** (não "código limpo", e sim "função >50 linhas tem justificativa ou é refatorada"). O Gate 8 (`gsd-verifier` + `gsd-code-reviewer`) usa esta lista como veredito.

## Quando usar (triggers)

- Toda phase com código (automático via Gate 8)
- Code review, verify-work, secure-phase, pré-release

## Honestidade sobre o que isto entrega

Esta barra **eleva o piso** — torna improvável que código abaixo do padrão sênior passe sem ser sinalizado. Ela **não garante** que o output seja sênior: garantir exigiria julgamento humano sobre adequação ao domínio, que nenhum checklist substitui. O que ela garante é que os erros sênior-óbvios (sem teste de erro, segredo no código, deploy sem rollback, query N+1) sejam **bloqueados ou registrados como dívida consciente** — nunca passem despercebidos.

---

## BLOCO A — Desenvolvimento (o código em si)

### A1. Correção e contrato
- [ ] Cada caminho de erro tratado explicitamente (não só o happy path)
- [ ] Inputs validados na borda (schema na entrada, nunca confiar no cliente)
- [ ] Tipos honestos: sem `any`/`# type: ignore` sem comentário justificando
- [ ] Sem `TODO`/`FIXME` sem entry correspondente em TECH-DEBT.md com `urgency_class`

### A2. Estrutura
- [ ] Separação de camadas respeitada (router↔service↔repo no backend; component↔service no front)
- [ ] Função >50 linhas ou complexidade ciclomática >10: refatorada OU justificada por comentário
- [ ] Sem duplicação copy-paste de bloco >8 linhas (extrair)
- [ ] Nomes revelam intenção; sem abreviação obscura, sem `data2`/`tmp`/`handleStuff`

### A3. Testes (o diferencial sênior)
- [ ] Happy path testado
- [ ] **Pelo menos 1 caso de erro/borda por unidade nova** (não só sucesso)
- [ ] Teste verifica comportamento observável, não implementação interna
- [ ] Endpoint novo: teste de integração validando status + shape do response
- [ ] Cobertura não regride na phase (delta ≥ 0)

### A4. Performance consciente
- [ ] Listas/queries: sem N+1 (eager load explícito) — bloqueio se detectado
- [ ] Endpoint de lista: paginação obrigatória
- [ ] Loop sobre I/O: justificado ou batched
- [ ] Front: sem re-render desnecessário óbvio (trackBy, OnPush onde aplicável)

### A5. Observabilidade (não é opcional em produção)
- [ ] Erro não-esperado é logado com contexto (request_id), não engolido
- [ ] Operação crítica (pagamento, auth, deleção) tem log de auditoria
- [ ] Sem `console.log`/`print` de debug deixado no código

## BLOCO B — Segurança (consulta `owasp-security`; isto é o resumo enforced)

- [ ] **Zero segredo no código/repo** — tudo em env/secrets (bloqueio absoluto)
- [ ] AuthN/AuthZ: endpoint novo declarou explicitamente público ou protegido; default protegido
- [ ] Autorização verificada no servidor por recurso (não confiar que o front escondeu o botão)
- [ ] Input do usuário nunca interpolado em SQL/comando/HTML (queries parametrizadas, escape)
- [ ] PII: tratada conforme `lgpd-compliance`; sem PII em log
- [ ] Token de auth nunca em localStorage (web); httpOnly cookie ou storage seguro (app)
- [ ] Rate limit em endpoints de auth e de custo alto
- [ ] Dependências: sem CVE crítico conhecido (audit no CI)
- [ ] Erro não vaza stack trace / SQL / caminho interno ao cliente em produção

## BLOCO C — Deploy & operação (consulta `monorepo-deploy-safety`, `github-actions-ci`, `docker-production-ready`)

- [ ] Migration acompanha mudança de schema, é **reversível** (downgrade real testado)
- [ ] Deploy tem rollback (symlink atomic ou tag imutável) — nunca deploy irreversível
- [ ] **Backup pré-migração obrigatório** — deploy aborta se falhar (invariante v0.9.4)
- [ ] `.env.example` cobre toda env nova que o código lê (env-smoke-check passa)
- [ ] Health check pós-deploy no script
- [ ] CI verde antes do deploy; deploy só em tag + environment protection
- [ ] Build reproduzível (`npm ci`/`uv sync --frozen`, lockfile commitado)

## BLOCO D — Acessibilidade & UX (se has_ui; consulta `accessibility-pro` + matriz UI)

- [ ] Navegável por teclado; foco visível; ordem de tab lógica
- [ ] Contraste WCAG AA; cor nunca é o único portador de informação
- [ ] Estados: loading, vazio (os 3), erro com recuperação — nenhuma tela em branco
- [ ] Imagens/ícones de ação com texto alternativo/`aria-label`
- [ ] Sem AI-slop: usa tokens, não hex solto; espaçamento consistente (consulta `ui-ux-pro-max`)

---

## Como o veredito funciona (Gate 8)

Para cada bloco aplicável à phase, o verificador classifica cada item:
- **PASS** — atendido
- **FAIL-BLOCK** — itens marcados (bloqueio absoluto): qualquer segredo no código, deploy irreversível, backup pré-migração ausente, N+1 em lista, SQL injection possível, endpoint sem decisão de auth
- **FAIL-DEBT** — não atendido mas registrável como dívida consciente com `urgency_class` e aceite humano explícito
- **N/A** — bloco não se aplica à phase (justificar)

**A phase não fecha com nenhum FAIL-BLOCK aberto.** FAIL-DEBT exige linha em TECH-DEBT.md. A diferença entre FAIL-BLOCK e FAIL-DEBT é o que evita que a barra vire teatro: o que é perigoso bloqueia; o que é melhoria fica visível e contabilizado.

**Enforcement por código (v0.9.6):** o veredito não depende de disciplina do agente. `node .claude/get-shit-done/bin/gsd-tools.cjs verify quality-bar <N>` valida QUALITY-BAR.md (presença, FAIL-BLOCKs abertos, FAIL-DEBTs contabilizados em TECH-DEBT.md) e retorna `passed: false` em qualquer violação. O hook `gsd-phase-transition-guard.sh` roda esse check automaticamente antes de qualquer transição de phase — gate escrito mas não atendido bloqueia mecanicamente. FAIL-BLOCK corrigido se marca `[RESOLVIDO]` na própria linha, com a evidência da correção.

## Relação com outras skills

Esta skill é o **agregador de barra**. Ela não substitui as skills de domínio — aponta para elas:
- Desenvolvimento backend → `fastapi-production-patterns`
- Segurança → `owasp-security`, `lgpd-compliance`
- Deploy → `monorepo-deploy-safety`, `github-actions-ci`, `docker-production-ready`
- UX → `accessibility-pro`, `ui-ux-pro-max`, matriz `sprint_ui_matrix`
- Performance → `performance-web-vitals`, `observability-production`
