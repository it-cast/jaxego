/**
 * Configurações de ambiente — desenvolvimento.
 * Valores de produção vêm de environment.prod.ts (fileReplacements no angular.json).
 *
 * apiUrl vazio = requisições relativas (/v1/...), resolvidas pelo proxy.conf.json
 * do dev server (ng serve/ionic serve). Só faz sentido ter valor em produção —
 * o APK empacotado pelo Capacitor não tem dev server nem proxy.
 */
export const environment = {
  production: false,
  apiUrl: '',
};
