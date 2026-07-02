# CORRECAO-185 — Zonas e preços no app do entregador

## Arquivos criados
- `apps/api/alembic/versions/0033_courier_zona.py`: migration criando tabela `courier_zonas` (courier_id, zona_id, preco_cents, UniqueConstraint)
- `apps/api/app/couriers/models.py`: modelo `CourierZona` adicionado ao final do arquivo

## Arquivos modificados
- `apps/api/app/couriers/router.py`: endpoints `GET /{courier_id}/zonas` e `PUT /{courier_id}/zonas/{zona_id}` adicionados — retorna zonas da área com `team_preco_cents` e `courier_preco_cents`; PUT faz upsert do override do entregador
- `apps/app/src/features/entregador/cobertura-precos/cobertura-precos.service.ts`: interface `ZonaItem` adicionada; métodos `listZonas()` e `setZonaPreco()` adicionados
- `apps/app/src/features/entregador/cobertura-precos/cobertura-precos.page.ts`: reescrito como página "Zonas e preços" — lista zonas com preço da equipe e badge de override do courier; edição inline por zona
- `apps/app/src/features/entregador/cobertura-precos/cobertura-precos.page.html`: template completamente reescrito
- `apps/app/src/features/entregador/cobertura-precos/cobertura-precos.page.scss`: estilos completamente reescritos para o novo layout
- `apps/app/src/layouts/entregador-shell.component.ts`: tab "Bairros" → "Zonas"
- `apps/app/src/features/entregador/inicio.page.ts`: texto e botão do card KYC atualizados para "zonas"

## Comportamento
- Entregador vê todas as zonas da área com o preço padrão da equipe
- Badge verde "Meu preço" aparece quando o entregador tem override ativo
- Botão "Personalizar" abre edição inline com campo numérico
- Salvar faz PUT em `/v1/couriers/{id}/zonas/{zona_id}` com `preco_cents`
- Override do courier sempre prevalece sobre o padrão da equipe (na lógica de despacho)
