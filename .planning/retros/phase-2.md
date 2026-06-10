---
phase: 2
phase_name: Núcleo multi-área + autenticação + RBAC
milestone: MS-01
date: 2026-06-10
auto_generated: true
pending_review: true
---

# Retrospectiva — Phase 2: Núcleo multi-área + autenticação + RBAC

## Dados objetivos (capturados automaticamente)
- Tasks: 16/16 (T-01..T-16)
- Plan revisions: 0 (gate 3 PASS na 1ª iteração — planner aprendeu com a Phase 1)
- Verification retries: 1 ciclo de fix ao vivo (trigger privilege + teardown de teste)
- Gates bypassados: 0
- Tech debt adicionado: 0 de código (2 follow-ups operacionais rastreados no RECONCILIATION: smoke auth-flow com admin semeado; CI remoto com MySQL service)
- Skills citadas: 8 (orchestration-decision-tree, observability-production, owasp-security, lgpd-compliance, mysql-schema-design, fastapi-production-patterns, api-design-contracts, senior-quality-bar)
- Commits: 17 (0eabdca..b0ce439)
- Libs: argon2-cffi, pyjwt, pyotp, email-validator, aiosqlite(dev)

## Auto-observações
- Gate 4 (Security Baseline com 10 ameaças) funcionou bem como entrada do threat model do plano.
- Os 3 itens LOW confidence viraram tasks explícitas (Regra 12) e todos foram resolvidos: argon2id params explícitos, PyJWT alg pinado, trigger MySQL no CI.
- **Lição reforçada da Phase 1:** verificação ao vivo pega o que mock não pega. Aqui: a migration de trigger falhava em MySQL 8 real (privilege 1419) — bug de deploy que nenhum teste SQLite/mock pegaria. Corrigido na infra (compose + nota prod).
- Teste async em Windows exige dispose explícito da engine no mesmo event loop (flaky `Event loop is closed`).

## Qualitativo (preencher manualmente — edite este arquivo)

### 1. O que funcionou bem?
[AUTO: preencher depois] — Hipótese: gate 3 PASS de primeira; security baseline → threat model; isolamento em 3 camadas claro.

### 2. O que atrapalhou?
[AUTO: preencher depois] — Hipótese: privilege de trigger no MySQL 8; teardown asyncio no Windows; testes em SQLite não exercitam MySQL real.

### 3. O que faltou (skill, contexto, ferramenta)?
[AUTO: preencher depois] — Considerar: rodar a suíte de integração contra MySQL (não só SQLite) já no dev loop; seed de admin de plataforma para smoke de auth end-to-end.

### 4. Claude entendeu o que você queria? (1-5)
[AUTO: preencher depois]

### 5. Qualidade do código entregue? (1-5)
[AUTO: preencher depois]
