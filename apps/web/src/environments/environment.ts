/**
 * Configurações de ambiente — desenvolvimento.
 * Valores de produção vêm de environment.prod.ts (fileReplacements no angular.json).
 *
 * MAPBOX_TOKEN: pk.* é chave pública, projetada para uso no cliente.
 * Valor mantido em .env na raiz do projeto como MAPBOX_TOKEN.
 */
export const environment = {
  production: false,
  mapboxToken: '',
};
