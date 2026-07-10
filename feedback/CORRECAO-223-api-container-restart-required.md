# CORRECAO-223 — Save não funcionava: uvicorn sem --reload, mudanças Python ignoradas

## Data
2026-07-09

## Causa raiz
O container `jaxego-api-1` roda uvicorn **sem** `--reload`:
```
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```
As mudanças feitas nos arquivos Python bind-montados (service.py, config_schema.py,
admin_router.py, etc.) NÃO são recarregadas automaticamente. O uvicorn carregou os
módulos uma vez no startup (12:14 de hoje) e continuou usando a versão antiga.

**Consequência:** o código rodando era o ANTERIOR às correções desta sessão:
- `AreaConfig` sem `max_entregas_simultaneas` → campo ignorado via `extra="ignore"`
- `update_area` sem o merge fix → `area.config = validated.model_dump()` substituía
  o config inteiro pelos 3 campos antigos, apagando qualquer campo adicional
- O PATCH retornava 200 mas salvava config errado

**Por que o frontend continuava mostrando 1 após save:**
O backend retornava `AreaRead` com config sem `max_entregas_simultaneas`. O frontend
normalizava com default 1. O form ficava em 1.

## Solução
`docker restart jaxego-api-1` — recarregou todos os módulos Python com o código novo.

## Verificação pós-restart
```python
from app.areas.config_schema import AreaConfig
AreaConfig().model_dump()
# → {'kyc_level': 'simples', 'timeout_oferta_s': 20, 'timeout_favoritos_s': 60,
#    'max_entregas_simultaneas': 1}
```
Teste direto de save para área 2 com max=4 → commitou e retornou config correto.

## Lição
**Sempre reiniciar o container da API após mudanças em arquivos Python.**
O bind-mount serve para edição, mas o Python process precisa reimportar os módulos.
Alternativa de longo prazo: adicionar `--reload` ao comando uvicorn no docker-compose
(apenas para dev — NÃO fazer em produção).
