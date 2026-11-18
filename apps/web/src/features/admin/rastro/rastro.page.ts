import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, OnInit, WritableSignal, computed, inject, signal } from '@angular/core';
import { Trail, TrailMapComponent } from '@jaxego/shared/components/trail-map/trail-map.component';
import { firstValueFrom } from 'rxjs';

import { AdminKycService, CourierListItem } from '../kyc/kyc.service';

/** Contrato de GET /v1/admin/couriers/{id}/trail/deliveries */
interface TrailDelivery {
  id: number;
  state: string;
  merchant_name: string | null;
  accepted_at: string;
  ended_at: string | null;
}

const pad = (n: number) => String(n).padStart(2, '0');
const diaLocal = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
/** Para buscar sem acento e sem diferença de maiúscula */
const normalizar = (s: string) =>
  s
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .trim();

/**
 * Rastro dos entregadores (admin da área): busca o entregador pelo nome, o dia (últimos
 * 7) e o horário. Depois da busca aparece o filtro "Entrega" com as entregas que têm
 * pontos nesse período, já na mais recente; sem nenhuma, mostra o período inteiro. Cada
 * consulta vai para a auditoria do Jaxegô.
 */
@Component({
  selector: 'jx-admin-rastro',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TrailMapComponent],
  template: `
    <section class="jx-rastro">
      <header class="jx-rastro__head">
        <div>
          <h1 class="jx-rastro__title">Rastro dos entregadores</h1>
          <p class="jx-rastro__sub">
            Trajeto registrado enquanto o entregador está online (a cada 5 min, e a cada 1 min durante uma
            entrega). Os registros ficam guardados por 7 dias.
          </p>
        </div>
      </header>

      <form class="jx-rastro__filters" (submit)="$event.preventDefault(); buscar()">
        <div class="jx-rastro__field jx-rastro__field--busca">
          <label for="rastro-busca">Entregador</label>
          <div class="jx-rastro__combo">
            <input
              id="rastro-busca"
              type="search"
              autocomplete="off"
              placeholder="Buscar pelo nome…"
              role="combobox"
              aria-autocomplete="list"
              aria-controls="rastro-opcoes"
              [attr.aria-expanded]="aberto()"
              [attr.aria-activedescendant]="aberto() && sugestoes().length ? 'rastro-op-' + destaque() : null"
              [value]="busca()"
              (input)="digitar($any($event.target).value)"
              (focus)="abrir()"
              (blur)="fecharDepois()"
              (keydown)="teclar($event)"
              data-teste="rastro-entregador"
            />
            @if (aberto()) {
              <ul id="rastro-opcoes" class="jx-rastro__opcoes" role="listbox" aria-label="Entregadores">
                @for (c of sugestoes(); track c.id; let i = $index) {
                  <li
                    [id]="'rastro-op-' + i"
                    role="option"
                    [attr.aria-selected]="c.id === courierId()"
                    [class.jx-rastro__op--on]="i === destaque()"
                    (mousedown)="$event.preventDefault(); escolher(c)"
                    (mouseenter)="destaque.set(i)"
                  >
                    <span>{{ c.full_name }}</span>
                    <small>{{ c.cpf_masked }}</small>
                  </li>
                } @empty {
                  <li class="jx-rastro__op-vazio">Nenhum entregador com esse nome.</li>
                }
              </ul>
            }
          </div>
        </div>

        <label class="jx-rastro__field">
          <span>Dia</span>
          <input type="date" [min]="minDia" [max]="maxDia" [value]="dia()" (change)="mudarPeriodo(dia, $any($event.target).value)" />
        </label>
        <label class="jx-rastro__field jx-rastro__field--hora">
          <span>Das</span>
          <input type="time" [value]="das()" (change)="mudarPeriodo(das, $any($event.target).value)" />
        </label>
        <label class="jx-rastro__field jx-rastro__field--hora">
          <span>Até</span>
          <input type="time" [value]="ate()" (change)="mudarPeriodo(ate, $any($event.target).value)" />
        </label>
        @if (entregas().length) {
          <label class="jx-rastro__field jx-rastro__field--entrega">
            <span>Entrega</span>
            <select (change)="filtrarEntrega($any($event.target).value)" data-teste="rastro-entrega">
              <option value="" [selected]="!deliveryId()">Todas do período</option>
              @for (e of entregas(); track e.id) {
                <option [value]="e.id" [selected]="e.id === deliveryId()">{{ rotuloEntrega(e) }}</option>
              }
            </select>
          </label>
        }
        <button type="submit" class="jx-rastro__btn" [disabled]="!courierId() || carregando()" data-teste="rastro-ver">
          {{ carregando() ? 'Carregando…' : 'Ver rastro' }}
        </button>
      </form>

      @if (erro()) {
        <p class="jx-rastro__erro" role="alert">{{ erro() }}</p>
      }

      @if (trail(); as t) {
        <jx-trail-map [trail]="t" [mostrarEntrega]="!deliveryId()" [ariaLabel]="'Trajeto de ' + (t.courier_name || 'entregador')" />
      } @else if (carregando()) {
        <p class="jx-rastro__vazio">Carregando o rastro…</p>
      } @else {
        <p class="jx-rastro__vazio">Busque um entregador pelo nome e escolha o dia para ver o trajeto.</p>
      }
    </section>
  `,
  styles: [
    `
      .jx-rastro { display: flex; flex-direction: column; gap: var(--jx-space-4); }
      .jx-rastro__title { font-family: var(--jx-font-display); font-size: var(--jx-text-2xl); margin: 0; }
      .jx-rastro__sub { margin: var(--jx-space-1) 0 0; color: var(--text-muted); font-size: var(--jx-text-sm); max-width: 680px; }
      .jx-rastro__filters { display: flex; flex-wrap: wrap; align-items: flex-end; gap: var(--jx-space-3); }
      .jx-rastro__field { display: grid; gap: 4px; font-size: var(--jx-text-sm); color: var(--text-muted); }
      .jx-rastro__field select,
      .jx-rastro__field input {
        min-height: 44px; min-width: 180px;
        padding: 0 var(--jx-space-3);
        border: 1px solid var(--border-strong, var(--border));
        border-radius: var(--jx-radius-lg);
        font-size: var(--jx-text-base);
        color: var(--text);
        background: var(--surface);
      }
      .jx-rastro__field--busca input { width: 280px; }
      .jx-rastro__field--entrega select { min-width: 300px; }
      .jx-rastro__field--hora input { min-width: 120px; }
      .jx-rastro__field select:focus,
      .jx-rastro__field input:focus { outline: none; border-color: var(--brand); }
      .jx-rastro__combo { position: relative; }
      .jx-rastro__opcoes {
        position: absolute; top: calc(100% + 4px); left: 0; right: 0; z-index: 1100;
        margin: 0; padding: 4px; list-style: none;
        max-height: 300px; overflow: auto;
        background: var(--surface-elevated);
        border: 1px solid var(--border);
        border-radius: var(--jx-radius-lg);
        box-shadow: var(--shadow-md, var(--shadow-sm));
      }
      .jx-rastro__opcoes li {
        display: flex; align-items: baseline; justify-content: space-between; gap: var(--jx-space-2);
        padding: 10px 12px; border-radius: var(--jx-radius-md);
        color: var(--text); font-size: var(--jx-text-base); cursor: pointer;
      }
      .jx-rastro__opcoes li small { color: var(--text-muted); font-size: var(--jx-text-xs, 12px); font-family: var(--jx-font-mono); }
      .jx-rastro__opcoes li.jx-rastro__op--on { background: var(--surface-sunken); }
      .jx-rastro__opcoes li.jx-rastro__op-vazio { color: var(--text-muted); cursor: default; font-size: var(--jx-text-sm); }
      .jx-rastro__btn {
        min-height: 44px; padding: 0 var(--jx-space-5);
        border: 0; border-radius: var(--jx-radius-lg);
        background: var(--brand); color: var(--on-brand, #fff);
        font-weight: 700; font-size: var(--jx-text-base); cursor: pointer;
      }
      .jx-rastro__btn:disabled { opacity: 0.55; cursor: default; }
      .jx-rastro__erro {
        margin: 0; padding: var(--jx-space-3);
        border-radius: var(--jx-radius-lg);
        background: var(--danger-subtle, var(--surface-sunken));
        color: var(--danger, var(--text));
        font-weight: 600;
      }
      .jx-rastro__vazio { margin: 0; color: var(--text-muted); }
      @media (max-width: 600px) {
        .jx-rastro__field, .jx-rastro__field select, .jx-rastro__field input, .jx-rastro__btn { width: 100%; min-width: 0; }
        .jx-rastro__field--busca input { width: 100%; }
        .jx-rastro__field--hora { width: calc(50% - var(--jx-space-3) / 2); }
      }
    `,
  ],
})
export class AdminRastroPage implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly kyc = inject(AdminKycService);

  protected readonly entregadores = signal<CourierListItem[]>([]);
  protected readonly courierId = signal<number | null>(null);
  protected readonly busca = signal('');
  protected readonly aberto = signal(false);
  protected readonly destaque = signal(0);
  protected readonly entregas = signal<TrailDelivery[]>([]);
  protected readonly dia = signal(diaLocal(new Date()));
  protected readonly das = signal('00:00');
  protected readonly ate = signal('23:59');
  protected readonly deliveryId = signal<number | null>(null);
  protected readonly trail = signal<Trail | null>(null);
  protected readonly carregando = signal(false);
  protected readonly erro = signal<string | null>(null);

  protected readonly maxDia = diaLocal(new Date());
  protected readonly minDia = diaLocal(new Date(Date.now() - 6 * 86_400_000));

  /** Filtra pelo nome (sem acento) ou pelos dígitos do CPF; até 20 sugestões */
  protected readonly sugestoes = computed(() => {
    const q = normalizar(this.busca());
    const lista = this.entregadores();
    if (!q) return lista.slice(0, 20);
    const digitos = q.replace(/\D/g, '');
    return lista
      .filter(
        (c) =>
          normalizar(c.full_name).includes(q) ||
          (digitos.length >= 3 && c.cpf_masked.replace(/\D/g, '').includes(digitos)),
      )
      .slice(0, 20);
  });

  private fecharTimer: ReturnType<typeof setTimeout> | null = null;
  /** Ignora respostas antigas quando o admin troca de entregador rápido */
  private versao = 0;

  async ngOnInit(): Promise<void> {
    const r = await this.kyc.listCouriers();
    this.entregadores.set(
      [...r.items].filter((c) => c.status !== 'pending_kyc').sort((a, b) => a.full_name.localeCompare(b.full_name, 'pt-BR')),
    );
  }

  protected digitar(v: string): void {
    this.busca.set(v);
    this.destaque.set(0);
    this.aberto.set(true);
  }

  protected abrir(): void {
    if (this.fecharTimer) clearTimeout(this.fecharTimer);
    this.destaque.set(0);
    this.aberto.set(true);
  }

  protected fecharDepois(): void {
    this.fecharTimer = setTimeout(() => {
      this.aberto.set(false);
      // Saiu sem escolher: volta o nome do entregador atual
      const atual = this.entregadores().find((c) => c.id === this.courierId());
      if (atual) this.busca.set(atual.full_name);
    }, 120);
  }

  protected teclar(ev: KeyboardEvent): void {
    const total = this.sugestoes().length;
    if (ev.key === 'ArrowDown') {
      ev.preventDefault();
      this.aberto.set(true);
      if (total) this.destaque.update((i) => (i + 1) % total);
    } else if (ev.key === 'ArrowUp') {
      ev.preventDefault();
      if (total) this.destaque.update((i) => (i - 1 + total) % total);
    } else if (ev.key === 'Enter') {
      ev.preventDefault();
      const c = this.sugestoes()[this.destaque()];
      if (this.aberto() && c) this.escolher(c);
    } else if (ev.key === 'Escape') {
      this.aberto.set(false);
    }
  }

  /** Escolheu o entregador: abre na última entrega dele; sem entrega, o dia de hoje inteiro */
  protected escolher(c: CourierListItem): void {
    this.busca.set(c.full_name);
    this.aberto.set(false);
    this.courierId.set(c.id);
    void this.buscar();
  }

  /** Ver rastro: busca as entregas com pontos no período e abre na mais recente delas;
   * sem entrega no período, mostra o período inteiro */
  protected async buscar(): Promise<void> {
    const id = this.courierId();
    if (!id) return;
    this.deliveryId.set(null);
    this.entregas.set([]);
    this.trail.set(null);
    this.erro.set(null);
    const v = ++this.versao;
    this.carregando.set(true);
    const { inicio, fim } = this.periodo();
    let lista: TrailDelivery[] = [];
    try {
      lista = await firstValueFrom(
        this.http.get<TrailDelivery[]>(
          `/v1/admin/couriers/${id}/trail/deliveries?start=${encodeURIComponent(inicio)}&end=${encodeURIComponent(fim)}`,
        ),
      );
    } catch {
      lista = [];
    }
    if (v !== this.versao) return;
    this.entregas.set(lista);
    this.deliveryId.set(lista[0]?.id ?? null);
    await this.carregar();
  }

  protected filtrarEntrega(v: string): void {
    this.deliveryId.set(v ? Number(v) : null);
    void this.carregar();
  }

  /** Mexeu no dia/horário: a lista de entregas some até buscar de novo */
  protected mudarPeriodo(alvo: WritableSignal<string>, valor: string): void {
    alvo.set(valor);
    this.deliveryId.set(null);
    this.entregas.set([]);
  }

  private periodo(): { inicio: string; fim: string } {
    return {
      inicio: new Date(`${this.dia()}T${this.das()}:00`).toISOString(),
      fim: new Date(`${this.dia()}T${this.ate()}:59`).toISOString(),
    };
  }

  protected rotuloEntrega(e: TrailDelivery): string {
    const quando = new Date(e.accepted_at).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
    const loja = e.merchant_name ? ` · ${e.merchant_name}` : '';
    return `#${e.id}${loja} · ${quando}${e.ended_at ? '' : ' (em andamento)'}`;
  }

  protected async carregar(): Promise<void> {
    const id = this.courierId();
    if (!id) return;
    const v = ++this.versao;
    this.carregando.set(true);
    this.erro.set(null);
    try {
      let url: string;
      const entrega = this.deliveryId();
      if (entrega) {
        url = `/v1/admin/couriers/${id}/trail?delivery_id=${entrega}`;
      } else {
        const { inicio, fim } = this.periodo();
        url = `/v1/admin/couriers/${id}/trail?start=${encodeURIComponent(inicio)}&end=${encodeURIComponent(fim)}`;
      }
      const t = await firstValueFrom(this.http.get<Trail>(url));
      if (v !== this.versao) return;
      this.trail.set(t);
    } catch (e) {
      if (v !== this.versao) return;
      this.trail.set(null);
      const msg = e instanceof HttpErrorResponse ? (e.error?.error?.message ?? e.error?.message ?? e.error?.detail) : null;
      this.erro.set(typeof msg === 'string' ? msg : 'Não foi possível carregar o rastro.');
    } finally {
      if (v === this.versao) this.carregando.set(false);
    }
  }
}
