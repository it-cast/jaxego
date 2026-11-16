/**
 * Configurações de ambiente — produção (build empacotado no APK via Capacitor).
 *
 * apiUrl PRECISA ser uma URL absoluta — o app rodando dentro do WebView do
 * Capacitor não tem dev server nem proxy.conf.json pra resolver caminhos
 * relativos. Toda chamada HTTP sai prefixada com esse valor (ver
 * apiBaseUrlInterceptor em packages/shared/src/core/http/api-base-url.interceptor.ts).
 *
 * TEMPORÁRIO: valor abaixo é o túnel ngrok atual (mesmo usado em
 * SAFE2PAY_CALLBACK_URL no .env) — muda toda vez que o ngrok reinicia. Troque
 * por um domínio fixo (seu servidor real) antes de gerar um build definitivo.
 */
export const environment = {
  production: true,
  apiUrl: 'https://145f-2804-99c-8747-b00-5f08-c448-f241-bcfc.ngrok-free.app',
};
