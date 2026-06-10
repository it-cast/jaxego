# backend/app/core/audit.py
# NOTA: fixture intencionalmente incompleta.
# PLAN.md diz que T1-T4 estão [x] done, mas o código abaixo só tem T2.
# reconcile deve detectar que T1 (migration), T3 (middleware) e T4 (endpoint) não existem.

def log_audit_event(action: str, user_id: str, details: dict) -> None:
    """Stub de audit log — não escreve em lugar nenhum ainda."""
    print(f"AUDIT: {action} by {user_id}")
    # TODO: escrever em banco (audit_log table) — migration não criada
