import { EnvironmentProviders, inject, provideEnvironmentInitializer } from '@angular/core';
import { NavigationEnd, NavigationStart, Router } from '@angular/router';

/** Áreas com rolagem própria que também voltam ao topo (o miolo do shell do app). */
const AREAS_ROLAVEIS = '.jx-shell__content';

function rolar(top: number): void {
  // `instant`: o CSS global usa `scroll-behavior: smooth`, que animaria a volta ao topo.
  window.scrollTo({ top, left: 0, behavior: 'instant' });
  if (top === 0) {
    document
      .querySelectorAll<HTMLElement>(AREAS_ROLAVEIS)
      .forEach((el) => el.scrollTo({ top: 0, left: 0, behavior: 'instant' }));
  }
}

/**
 * Rolagem ao trocar de página. Sem isso o router mantém a rolagem da tela anterior
 * (ex.: um link no rodapé abria a próxima página já no final).
 *
 * - página nova → topo;
 * - voltar/avançar do navegador → a posição em que a pessoa estava naquela página;
 * - só query params mudando (filtros, paginação) ou link com #âncora → não mexe.
 *
 * Feito à mão em vez de `withInMemoryScrolling` porque aquele usa `window.scrollTo(x, y)`,
 * que anima com o `scroll-behavior: smooth` global, e não conhece a área rolável do app.
 */
export function provideScrollToTop(): EnvironmentProviders {
  return provideEnvironmentInitializer(() => {
    if (typeof window === 'undefined') return;
    const router = inject(Router);
    const posicoes = new Map<number, number>();
    let idAtual = 0;
    let caminhoAtual: string | null = null;
    let voltandoPara: number | null = null;

    router.events.subscribe((e) => {
      if (e instanceof NavigationStart) {
        posicoes.set(idAtual, window.scrollY);
        voltandoPara =
          e.navigationTrigger === 'popstate' ? (e.restoredState?.navigationId ?? null) : null;
        return;
      }
      if (!(e instanceof NavigationEnd)) return;

      idAtual = e.id;
      const caminho = e.urlAfterRedirects.split(/[?#]/)[0];
      const mudouCaminho = caminho !== caminhoAtual;
      caminhoAtual = caminho;

      if (router.parseUrl(e.urlAfterRedirects).fragment) return;
      if (voltandoPara !== null && posicoes.has(voltandoPara)) {
        const y = posicoes.get(voltandoPara)!;
        // espera a tela nova desenhar para a altura da página permitir a posição
        setTimeout(() => rolar(y));
        return;
      }
      if (mudouCaminho) rolar(0);
    });
  });
}
