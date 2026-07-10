# CORRECAO-221 — Save direto e merge de config na área

## Data
2026-07-09

## Problemas corrigidos

### 1. Backend — config sendo apagado no save (`areas/service.py`)
`update_area` substituía todo `area.config` pelo resultado de `AreaConfig.model_dump()`,
apagando campos legados (`piso_km`, `geofence_m`, etc.) que existiam em áreas antigas.

**Fix:** merge em vez de substituição:
```python
# Antes
new_config = validated.model_dump(mode="json")
area.config = new_config

# Depois
new_config = {**before_config, **validated.model_dump(mode="json")}
area.config = new_config
```
Campos desconhecidos são preservados; campos do `AreaConfig` são sobrescritos.

### 2. Frontend — remoção do modal de confirmação (`area-config.page.ts` / `.html`)
- Removidos: `confirming`, `sensitiveDiff`, `SensitiveDiffRow`, `computeDiff`,
  `requestSave`, `cancelConfirm`, `confirmSave`
- Adicionado: método único `save()` — valida form → monta JSON → envia PATCH → re-patcha form
- HTML: modal inteiro removido; `(ngSubmit)="save()"` direto no form
- Botão: texto `'Salvar configurações'` (sem "(auditado)")
- Error state: retry chama `save()` diretamente
