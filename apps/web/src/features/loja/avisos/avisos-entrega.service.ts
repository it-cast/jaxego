import { Injectable, inject, signal } from '@angular/core';
import type { DeliveryListItem } from '@jaxego/shared/models/delivery.models';
import { DeliveryService } from '../entregas/delivery.service';

/** Mudanças que avisam a loja (som + aviso na tela). */
const MENSAGEM: Record<string, (ref: string) => string> = {
  ACEITA: (ref) => `Um entregador aceitou a entrega ${ref}.`,
  COLETADA: (ref) => `A entrega ${ref} foi coletada e está a caminho.`,
  ENTREGUE: (ref) => `A entrega ${ref} foi entregue.`,
};

const INTERVALO_MS = 10_000;
/** Entregas mais recentes acompanhadas (as ativas estão sempre entre elas). */
const LIMITE = 50;
const DURACAO_AVISO_MS = 8_000;
const SOM = 'sons/notificacao-jaxego.mp3';

export interface AvisoEntrega {
  id: number;
  deliveryId: number;
  estado: string;
  texto: string;
}

/**
 * Avisa a loja quando o entregador aceita, coleta ou entrega: toca o som e mostra um
 * aviso na tela. Consulta as entregas da loja a cada 10 s enquanto o painel está aberto
 * (com a aba em segundo plano o navegador espaça as consultas, mas o aviso chega).
 *
 * A primeira consulta só guarda os estados (não toca nada pelo que já tinha acontecido).
 * O navegador só deixa tocar som depois de a pessoa clicar em algo na página; se ainda não
 * clicou (ex.: logo após um F5), o aviso aparece sem som.
 */
@Injectable({ providedIn: 'root' })
export class AvisosEntregaService {
  private readonly deliveries = inject(DeliveryService);

  readonly avisos = signal<AvisoEntrega[]>([]);
  /** Sobe a cada mudança de estado de qualquer entrega: as telas abertas recarregam. */
  readonly versao = signal(0);

  private estados = new Map<number, string>();
  private timer: ReturnType<typeof setInterval> | null = null;
  private iniciadoEm = 0;
  private carregado = false;
  private consultando = false;
  private proximoId = 1;
  private audio: HTMLAudioElement | null = null;
  private readonly liberarSom = () => this.desbloquearAudio();

  start(): void {
    if (this.timer) return;
    this.iniciadoEm = Date.now();
    this.carregado = false;
    this.estados.clear();
    this.audio = new Audio(SOM);
    this.audio.preload = 'auto';
    // Safari só libera o som se ele tocar uma vez durante um clique/tecla.
    document.addEventListener('pointerdown', this.liberarSom, { once: true, capture: true });
    document.addEventListener('keydown', this.liberarSom, { once: true, capture: true });
    void this.consultar();
    this.timer = setInterval(() => void this.consultar(), INTERVALO_MS);
  }

  stop(): void {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
    document.removeEventListener('pointerdown', this.liberarSom, { capture: true });
    document.removeEventListener('keydown', this.liberarSom, { capture: true });
    this.audio?.pause();
    this.audio = null;
    this.estados.clear();
    this.avisos.set([]);
  }

  fechar(id: number): void {
    this.avisos.update((lista) => lista.filter((a) => a.id !== id));
  }

  private async consultar(): Promise<void> {
    if (this.consultando) return;
    this.consultando = true;
    try {
      const { items } = await this.deliveries.list({ limit: LIMITE });
      const novos: AvisoEntrega[] = [];
      let mudou = false;
      for (const d of items) {
        const antes = this.estados.get(d.id);
        this.estados.set(d.id, d.state);
        if (this.carregado && antes !== d.state) mudou = true;
        if (!this.carregado || !(d.state in MENSAGEM) || antes === d.state) continue;
        // Entrega que ainda não conhecíamos só avisa se foi criada depois de abrir o painel
        // (criada e aceita entre duas consultas).
        if (antes === undefined && !this.criadaDepoisDoInicio(d)) continue;
        novos.push(this.montarAviso(d));
      }
      this.carregado = true;
      if (mudou) this.versao.update((v) => v + 1);
      if (novos.length) {
        this.avisos.update((lista) => [...lista, ...novos].slice(-4));
        for (const a of novos) setTimeout(() => this.fechar(a.id), DURACAO_AVISO_MS);
        this.tocar();
      }
    } catch {
      /* sem conexão ou sessão expirando: tenta de novo na próxima volta */
    } finally {
      this.consultando = false;
    }
  }

  private criadaDepoisDoInicio(d: DeliveryListItem): boolean {
    const criada = d.created_at ? Date.parse(d.created_at) : NaN;
    return Number.isFinite(criada) && criada >= this.iniciadoEm - INTERVALO_MS;
  }

  private montarAviso(d: DeliveryListItem): AvisoEntrega {
    const ref = `#${d.id}` + (d.recipient_name ? ` (${d.recipient_name})` : '');
    return { id: this.proximoId++, deliveryId: d.id, estado: d.state, texto: MENSAGEM[d.state](ref) };
  }

  private tocar(): void {
    if (!this.audio) return;
    this.audio.currentTime = 0;
    this.audio.play().catch(() => {
      /* bloqueado até a pessoa interagir com a página: fica só o aviso visual */
    });
  }

  private desbloquearAudio(): void {
    const a = this.audio;
    if (!a || !a.paused) return;
    a.muted = true;
    a.play()
      .then(() => {
        a.pause();
        a.currentTime = 0;
      })
      .catch(() => undefined)
      .finally(() => (a.muted = false));
  }
}
