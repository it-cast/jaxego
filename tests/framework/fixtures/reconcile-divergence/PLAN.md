# PLAN.md — Phase 1 (reconcile-divergence fixture)

## Objetivo
Adicionar módulo de auditoria com tabela `audit_log` e helper `log_audit_event()`.

## Skills Consultadas

- `quality/observability-production` — logs estruturados

## Tasks

- [x] T1: Criar migration `create_audit_log_table`
- [x] T2: Função `log_audit_event(action, user_id, details)`
- [x] T3: Middleware que registra todas as mutations em audit_log
- [x] T4: Endpoint GET /api/v1/admin/audit-log com paginação

## Critérios de aceite

- Tabela audit_log existe com colunas id, action, user_id, details, created_at
- Função log_audit_event documentada
- Middleware registra em audit_log em todo POST/PATCH/DELETE
- Endpoint admin retorna log paginado
