# CORRECAO-188 — 500 no cancel + window.confirm → modal

## Bug 1 — 500 em POST /deliveries/{id}/cancel
Causa: `docker compose up -d` recriou o container da imagem original, apagando o fix de `areas/models.py` (campo `boundary` removido). Toda operação que carrega `Area` explodia com `Unknown column 'areas.boundary'`.
Fix: re-copiado `areas/models.py` corrigido ao container.

Nota estrutural: toda vez que o container for recriado (`up -d`, não só `restart`), os arquivos copiados via `docker compose cp` são perdidos — a imagem não tem os patches.

## Bug 2 — window.confirm no cancelamento
Substituído por modal inline na `EntregasListPage`:

- `cancelTarget = signal<DeliveryListItem | null>(null)` — controla visibilidade
- `cancelling = signal(false)` — desabilita botões durante o request
- `onCancel(item)` → só seta o signal (sem confirm)
- `dismissCancel()` → limpa o signal
- `confirmCancel()` → chama service.cancel, limpa signal, recarrega lista

Modal com: ícone ⚠, título, mensagem com token, botões "Voltar" e "Sim, cancelar".
Backdrop clicável fecha o modal. Botões desabilitados durante o cancelamento.
