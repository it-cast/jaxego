import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  EventEmitter,
  HostListener,
  Input,
  OnChanges,
  Output,
  ViewChild,
  WritableSignal,
  computed,
  signal,
} from '@angular/core';

import type { Trail } from './trail-map.component';

/** Uma linha do histórico: posição periódica ou ação da entrega */
export interface LinhaHistorico {
  at: string;
  /** 'posicao' ou a ação (aceitou, coletou, ...) */
  tipo: string;
  lat: number;
  lng: number;
  accuracy_m: number | null;
  delivery_id: number | null;
}

const POR_PAGINA = 10;

const ROTULOS: Record<string, string> = {
  posicao: 'Posição',
  aceitou: 'Aceitou',
  coletou: 'Coletou',
  chegou_destino: 'Chegou ao destino',
  entregou: 'Entregou',
  recusou_entrega: 'Recusado no destino',
  cancelou_aceite: 'Desistiu',
};

const pad = (n: number) => String(n).padStart(2, '0');
const horaLocal = (iso: string) => {
  const d = new Date(iso);
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

/**
 * jx-trail-history — modal "Histórico de localizações" do rastro: tabela com cada
 * posição e cada ação da entrega, filtros (tipo, entrega, horário), ordem pelo
 * horário e paginação de 10 em 10. "Ver no mapa" fecha o modal e centraliza o ponto.
 */
@Component({
  selector: 'jx-trail-history',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="jx-hist-overlay" (click)="fechar.emit()">
      <div
        class="jx-hist"
        role="dialog"
        aria-modal="true"
        aria-labelledby="jx-hist-title"
        (click)="$event.stopPropagation()"
      >
        <header class="jx-hist__head">
          <div>
            <h2 id="jx-hist-title" class="jx-hist__title" tabindex="-1" #titulo>Histórico de localizações</h2>
            <p class="jx-hist__sub">{{ todas().length }} registros{{ nome ? ' de ' + nome : '' }}</p>
          </div>
          <button type="button" class="jx-hist__x" (click)="fechar.emit()" aria-label="Fechar">✕</button>
        </header>

        <div class="jx-hist__filtros">
          <label class="jx-hist__campo">
            <span>Tipo</span>
            <select [value]="tipo()" (change)="mudar(tipo, $any($event.target).value)">
              <option value="">Todos</option>
              <option value="posicao">Só posições</option>
              <option value="acoes">Só ações da entrega</option>
              @for (a of acoesPresentes(); track a) {
                <option [value]="a">{{ rotulo(a) }}</option>
              }
            </select>
          </label>
          @if (mostrarEntrega && entregas().length > 1) {
            <label class="jx-hist__campo">
              <span>Entrega</span>
              <select [value]="entrega()" (change)="mudar(entrega, $any($event.target).value)">
                <option value="">Todas</option>
                @for (id of entregas(); track id) {
                  <option [value]="id">#{{ id }}</option>
                }
                <option value="sem">Sem entrega</option>
              </select>
            </label>
          }
          <label class="jx-hist__campo jx-hist__campo--hora">
            <span>Das</span>
            <input type="time" [value]="das()" (change)="mudar(das, $any($event.target).value)" />
          </label>
          <label class="jx-hist__campo jx-hist__campo--hora">
            <span>Até</span>
            <input type="time" [value]="ate()" (change)="mudar(ate, $any($event.target).value)" />
          </label>
          @if (temFiltro()) {
            <button type="button" class="jx-hist__limpar" (click)="limpar()">Limpar filtros</button>
          }
        </div>

        <div class="jx-hist__tabela">
          <table>
            <caption class="jx-sr-only">Histórico de localizações</caption>
            <thead>
              <tr>
                <th scope="col" [attr.aria-sort]="ordem() === 'asc' ? 'ascending' : 'descending'">
                  <button type="button" class="jx-hist__ordem" (click)="inverterOrdem()">
                    Horário <span aria-hidden="true">{{ ordem() === 'asc' ? '▴' : '▾' }}</span>
                  </button>
                </th>
                <th scope="col">Tipo</th>
                @if (mostrarEntrega) {
                  <th scope="col">Entrega</th>
                }
                <th scope="col">Coordenadas</th>
                <th scope="col" class="jx-hist__num">Precisão</th>
                <th scope="col"><span class="jx-sr-only">Ações</span></th>
              </tr>
            </thead>
            <tbody>
              @for (l of pagina(); track l.at + l.tipo + l.lat) {
                <tr>
                  <td class="jx-hist__mono">{{ dataHora(l.at) }}</td>
                  <td>
                    <span class="jx-hist__tipo" [class.jx-hist__tipo--acao]="l.tipo !== 'posicao'">
                      @if (l.tipo !== 'posicao') {
                        <span class="jx-hist__dot" [style.background]="corDe(l.tipo)"></span>
                      }
                      {{ rotulo(l.tipo) }}
                    </span>
                  </td>
                  @if (mostrarEntrega) {
                    <td>{{ l.delivery_id ? '#' + l.delivery_id : '—' }}</td>
                  }
                  <td class="jx-hist__mono">{{ l.lat.toFixed(5) }}, {{ l.lng.toFixed(5) }}</td>
                  <td class="jx-hist__num">{{ l.accuracy_m != null ? '±' + round(l.accuracy_m) + ' m' : '—' }}</td>
                  <td class="jx-hist__acao">
                    <button type="button" (click)="verNoMapa.emit(l)">Ver no mapa</button>
                  </td>
                </tr>
              } @empty {
                <tr>
                  <td [attr.colspan]="mostrarEntrega ? 6 : 5" class="jx-hist__vazio">Nenhum registro com esses filtros.</td>
                </tr>
              }
            </tbody>
          </table>
        </div>

        @if (filtradas().length) {
          <nav class="jx-hist__pager" aria-label="Paginação do histórico">
            <span class="jx-hist__info">
              {{ inicio() + 1 }}–{{ fim() }} de {{ filtradas().length }}
            </span>
            <div class="jx-hist__pager-btns">
              <button type="button" (click)="irPara(0)" [disabled]="pag() === 0" aria-label="Primeira página">«</button>
              <button type="button" (click)="irPara(pag() - 1)" [disabled]="pag() === 0">← Anterior</button>
              <span class="jx-hist__info">Página {{ pag() + 1 }} de {{ totalPaginas() }}</span>
              <button type="button" (click)="irPara(pag() + 1)" [disabled]="pag() >= totalPaginas() - 1">Próxima →</button>
              <button
                type="button"
                (click)="irPara(totalPaginas() - 1)"
                [disabled]="pag() >= totalPaginas() - 1"
                aria-label="Última página"
              >
                »
              </button>
            </div>
          </nav>
        }
      </div>
    </div>
  `,
  styles: [
    `
      .jx-hist-overlay {
        position: fixed; inset: 0; z-index: 2000;
        background: rgba(0, 0, 0, 0.5);
        display: flex; align-items: center; justify-content: center;
        padding: var(--jx-space-4);
      }
      .jx-hist {
        width: 100%; max-width: 920px; max-height: calc(100vh - 2 * var(--jx-space-4));
        display: flex; flex-direction: column; gap: var(--jx-space-3);
        padding: var(--jx-space-5);
        background: var(--surface-elevated);
        color: var(--text);
        border-radius: var(--jx-radius-xl);
        box-shadow: var(--shadow-lg);
        overflow: hidden;
      }
      .jx-hist__head { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--jx-space-3); }
      .jx-hist__title { margin: 0; font-family: var(--jx-font-display); font-size: var(--jx-text-xl); }
      .jx-hist__title:focus-visible { outline: none; }
      .jx-hist__sub { margin: 2px 0 0; font-size: var(--jx-text-sm); color: var(--text-muted); }
      .jx-hist__x {
        width: 40px; height: 40px; flex: none;
        border: 1px solid var(--border); border-radius: 50%;
        background: var(--surface); color: var(--text); cursor: pointer; font-size: 16px;
      }
      .jx-hist__filtros { display: flex; flex-wrap: wrap; align-items: flex-end; gap: var(--jx-space-2) var(--jx-space-3); }
      .jx-hist__campo { display: grid; gap: 4px; font-size: var(--jx-text-sm); color: var(--text-muted); }
      .jx-hist__campo select,
      .jx-hist__campo input {
        min-height: 40px; min-width: 170px; padding: 0 var(--jx-space-3);
        border: 1px solid var(--border-strong, var(--border)); border-radius: var(--jx-radius-lg);
        background: var(--surface); color: var(--text); font-size: var(--jx-text-sm);
      }
      .jx-hist__campo--hora input { min-width: 110px; }
      .jx-hist__campo select:focus, .jx-hist__campo input:focus { outline: none; border-color: var(--brand); }
      .jx-hist__limpar {
        min-height: 40px; padding: 0 var(--jx-space-3);
        border: 0; background: transparent; color: var(--brand);
        font-weight: 600; font-size: var(--jx-text-sm); cursor: pointer;
      }
      .jx-hist__tabela {
        overflow: auto; min-height: 0; flex: 1;
        border: 1px solid var(--border); border-radius: var(--jx-radius-lg);
      }
      .jx-hist__tabela table { width: 100%; border-collapse: collapse; font-size: var(--jx-text-sm); }
      .jx-hist__tabela thead th {
        position: sticky; top: 0; z-index: 1;
        background: var(--surface-sunken);
        text-align: left; font-weight: 600; color: var(--text-muted);
        font-size: var(--jx-text-xs, 12px); text-transform: uppercase; letter-spacing: 0.04em;
        padding: 10px 12px; white-space: nowrap;
      }
      .jx-hist__tabela td { padding: 10px 12px; border-top: 1px solid var(--border); white-space: nowrap; }
      .jx-hist__tabela tbody tr:hover td { background: var(--surface-sunken); }
      .jx-hist__ordem {
        border: 0; background: transparent; padding: 0; cursor: pointer;
        font: inherit; color: inherit; text-transform: inherit; letter-spacing: inherit;
      }
      .jx-hist__num { text-align: right !important; }
      .jx-hist__mono { font-family: var(--jx-font-mono); font-size: 13px; }
      .jx-hist__tipo { display: inline-flex; align-items: center; gap: 6px; color: var(--text-muted); }
      .jx-hist__tipo--acao { color: var(--text); font-weight: 600; }
      .jx-hist__dot { width: 10px; height: 10px; border-radius: 50%; flex: none; }
      .jx-hist__acao { text-align: right; }
      .jx-hist__acao button {
        border: 1px solid var(--border); background: var(--surface); color: var(--brand);
        border-radius: var(--jx-radius-sm); padding: 4px 10px; font-weight: 600; cursor: pointer;
        font-size: var(--jx-text-sm);
      }
      .jx-hist__vazio { text-align: center; color: var(--text-muted); padding: var(--jx-space-5) !important; }
      .jx-hist__pager { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: var(--jx-space-2); }
      .jx-hist__pager-btns { display: flex; flex-wrap: wrap; align-items: center; gap: var(--jx-space-2); }
      .jx-hist__pager button {
        min-height: 36px; padding: 0 12px;
        border: 1px solid var(--border); border-radius: var(--jx-radius-sm);
        background: var(--surface); color: var(--text); cursor: pointer; font-size: var(--jx-text-sm);
      }
      .jx-hist__pager button:disabled { opacity: 0.5; cursor: default; }
      .jx-hist__info { font-size: var(--jx-text-sm); color: var(--text-muted); }
      @media (max-width: 600px) {
        .jx-hist-overlay { padding: 0; align-items: stretch; }
        .jx-hist { max-height: none; border-radius: 0; padding: var(--jx-space-4); }
        .jx-hist__campo, .jx-hist__campo select { width: 100%; min-width: 0; }
        .jx-hist__campo--hora { width: calc(50% - var(--jx-space-3) / 2); }
        .jx-hist__campo--hora input { width: 100%; min-width: 0; }
      }
    `,
  ],
})
export class TrailHistoryComponent implements OnChanges, AfterViewInit {
  @Input({ required: true }) trail!: Trail;
  @Input() mostrarEntrega = false;
  /** Cor do marcador de cada ação (a mesma do mapa) */
  @Input() corAcao: (acao: string) => string = () => 'currentColor';
  @Output() fechar = new EventEmitter<void>();
  @Output() verNoMapa = new EventEmitter<LinhaHistorico>();

  @ViewChild('titulo') private readonly tituloRef?: ElementRef<HTMLElement>;

  protected readonly todas = signal<LinhaHistorico[]>([]);
  protected readonly tipo = signal('');
  protected readonly entrega = signal('');
  protected readonly das = signal('');
  protected readonly ate = signal('');
  protected readonly ordem = signal<'asc' | 'desc'>('asc');
  protected readonly pag = signal(0);
  protected nome: string | null = null;

  protected readonly acoesPresentes = computed(() => [
    ...new Set(this.todas().filter((l) => l.tipo !== 'posicao').map((l) => l.tipo)),
  ]);
  protected readonly entregas = computed(() =>
    [...new Set(this.todas().map((l) => l.delivery_id).filter((id): id is number => id != null))].sort((a, b) => a - b),
  );
  protected readonly temFiltro = computed(() => !!(this.tipo() || this.entrega() || this.das() || this.ate()));

  protected readonly filtradas = computed(() => {
    const tipo = this.tipo();
    const entrega = this.entrega();
    const das = this.das();
    const ate = this.ate();
    const lista = this.todas().filter((l) => {
      if (tipo === 'posicao' && l.tipo !== 'posicao') return false;
      if (tipo === 'acoes' && l.tipo === 'posicao') return false;
      if (tipo && tipo !== 'posicao' && tipo !== 'acoes' && l.tipo !== tipo) return false;
      if (entrega === 'sem' && l.delivery_id != null) return false;
      if (entrega && entrega !== 'sem' && l.delivery_id !== Number(entrega)) return false;
      const h = horaLocal(l.at);
      if (das && h < das) return false;
      if (ate && h > ate) return false;
      return true;
    });
    return this.ordem() === 'asc' ? lista : [...lista].reverse();
  });
  protected readonly totalPaginas = computed(() => Math.max(1, Math.ceil(this.filtradas().length / POR_PAGINA)));
  protected readonly inicio = computed(() => this.pag() * POR_PAGINA);
  protected readonly fim = computed(() => Math.min(this.inicio() + POR_PAGINA, this.filtradas().length));
  protected readonly pagina = computed(() => this.filtradas().slice(this.inicio(), this.fim()));

  ngOnChanges(): void {
    const t = this.trail;
    this.nome = t?.courier_name ?? null;
    const linhas: LinhaHistorico[] = [
      ...(t?.points ?? []).map((p) => ({ ...p, tipo: 'posicao' })),
      ...(t?.actions ?? []).map((a) => ({
        at: a.at,
        tipo: a.action,
        lat: a.lat,
        lng: a.lng,
        accuracy_m: null,
        delivery_id: a.delivery_id,
      })),
    ].sort((a, b) => a.at.localeCompare(b.at));
    this.todas.set(linhas);
    if (this.pag() >= this.totalPaginas()) this.pag.set(0);
  }

  ngAfterViewInit(): void {
    this.tituloRef?.nativeElement.focus();
  }

  @HostListener('document:keydown.escape')
  protected onEsc(): void {
    this.fechar.emit();
  }

  protected mudar(alvo: WritableSignal<string>, valor: string): void {
    alvo.set(valor);
    this.pag.set(0);
  }

  protected limpar(): void {
    this.tipo.set('');
    this.entrega.set('');
    this.das.set('');
    this.ate.set('');
    this.pag.set(0);
  }

  protected inverterOrdem(): void {
    this.ordem.update((o) => (o === 'asc' ? 'desc' : 'asc'));
    this.pag.set(0);
  }

  protected irPara(p: number): void {
    this.pag.set(Math.min(Math.max(0, p), this.totalPaginas() - 1));
  }

  protected rotulo(tipo: string): string {
    return ROTULOS[tipo] ?? tipo;
  }

  protected corDe(tipo: string): string {
    return this.corAcao(tipo);
  }

  protected dataHora(iso: string): string {
    return new Date(iso).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  }

  protected round(n: number): number {
    return Math.round(n);
  }
}
