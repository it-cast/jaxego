---
description: Otimizar performance de um modulo
---
Otimize performance de: $ARGUMENTS

Analise:
1. Queries SQL: N+1? Falta indice? selectinload/joinedload?
2. Serializacao: Pydantic model_validate vs dict?
3. Cache: Redis para dados que nao mudam frequentemente?
4. WebSocket: broadcast eficiente? Backpressure?
5. Frontend: OnPush? Signals? Lazy loading? Tree shaking?
6. Imagens: compressao client-side? CDN/cache Backblaze?
7. Concorrencia: async correto? Pool de conexoes?

Forneca antes/depois com estimativa de ganho.
