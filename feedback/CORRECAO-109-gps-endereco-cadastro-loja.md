# CORRECAO-109 — Preenchimento automático de endereço via GPS no cadastro da loja

## O que mudou

### Frontend (apps/web)
- **cadastro.page.html**: Adicionado botão "Usar minha localização" com ícone `faLocationCrosshairs` no step de endereço, antes do campo CEP. Exibe warning se GPS falhar.
- **cadastro.page.ts**: Método `fillFromGps()` usa Geolocation API do navegador + geocodificação reversa via Nominatim (OpenStreetMap, gratuito) para preencher automaticamente: CEP, rua, número, bairro, cidade e UF. Mensagens de erro para: permissão negada, timeout, navegador sem suporte.
- **cadastro.page.scss**: Estilo do botão GPS (borda dashed brand, hover com wash).

## Arquivos alterados
- apps/web/src/features/loja/cadastro/cadastro.page.html
- apps/web/src/features/loja/cadastro/cadastro.page.ts
- apps/web/src/features/loja/cadastro/cadastro.page.scss
