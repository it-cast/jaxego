import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  HostListener,
  OnDestroy,
  effect,
  inject,
  input,
  output,
  signal,
  viewChild,
} from '@angular/core';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faArrowUpRightFromSquare, faXmark } from '@fortawesome/free-solid-svg-icons';
import { StateBadgeComponent, type DeliveryState } from '@jaxego/shared/components/state-badge/state-badge.component';
import { formatBrl } from '@jaxego/shared/util/money';
import { AdminEntregaDetalhe, AdminEntregasService } from './admin-entregas.service';

const ESTADO_ROTULO: Record<string, string> = {
  AGENDADA: 'Agendada',
  AGUARDANDO_PAGAMENTO: 'Aguardando PIX',
  CRIADA: 'Criada / procurando',
  SEM_RESPOSTA: 'Sem resposta',
  ACEITA: 'Aceita',
  COLETADA: 'Coletada',
  ENTREGUE: 'Entregue',
  RECUSADA_NO_DESTINO: 'Recusada no destino',
  FINALIZADA: 'Finalizada',
  CANCELADA: 'Cancelada',
};

const QUEM: Record<string, string> = {
  courier: 'Entregador',
  merchant: 'Loja',
  area_admin: 'Admin da cidade',
  platform_admin: 'Admin da plataforma',
  team: 'Equipe',
  system: 'Sistema',
};

const PAGAMENTO: Record<string, string> = { direct: 'Direto ao entregador', pix: 'PIX', card: 'Cartão' };
const COMPROVACAO: Record<string, string> = {
  none: 'Sem comprovação',
  photo: 'Foto',
  photo_reference: 'Foto + referência',
  otp: 'Código',
};

/** Painel lateral com o detalhe de uma entrega da cidade (só leitura). */
@Component({
  selector: 'jx-entrega-drawer',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FaIconComponent, StateBadgeComponent],
  template: `
    <div class="jx-dr__fundo" (click)="fechar.emit()"></div>
    <aside class="jx-dr" role="dialog" aria-modal="true" aria-labelledby="jx-dr-titulo">
      <header class="jx-dr__topo">
        <h2 id="jx-dr-titulo" #titulo tabindex="-1" class="jx-dr__titulo">
          Entrega <span class="jx-mono">#{{ entregaId() }}</span>
        </h2>
        <button type="button" class="jx-dr__x" aria-label="Fechar" (click)="fechar.emit()">
          <fa-icon [icon]="i.fechar" aria-hidden="true" />
        </button>
      </header>

      <div class="jx-dr__corpo">
        @if (erro()) {
          <p class="jx-dr__erro" role="alert">{{ erro() }}</p>
        } @else if (!d()) {
          <p class="jx-dr__muted">Carregando…</p>
        } @else {
          @let e = d()!;
          <div class="jx-dr__resumo">
            <jx-state-badge [state]="estadoBadge(e.state)" />
            @if (e.reference_number) {
              <span class="jx-dr__muted">Ref. {{ e.reference_number }}</span>
            }
            <a class="jx-dr__link" [href]="'/r/' + e.public_token" target="_blank" rel="noopener">
              Acompanhamento <fa-icon [icon]="i.abrir" aria-hidden="true" />
            </a>
          </div>

          <section class="jx-dr__bloco">
            <h3>Quem</h3>
            <dl>
              <dt>Loja</dt><dd>{{ e.merchant_name || '—' }}</dd>
              <dt>Entregador</dt><dd>{{ e.courier_name || 'Ainda sem entregador' }}</dd>
            </dl>
          </section>

          <section class="jx-dr__bloco">
            <h3>Trajeto</h3>
            <dl>
              <dt>Coleta</dt><dd>{{ e.pickup_address }}</dd>
              <dt>Entrega</dt>
              <dd>
                {{ e.dropoff_address }}@if (e.dropoff_number) {, {{ e.dropoff_number }}}@if (e.dropoff_complement) { · {{ e.dropoff_complement }}}
                @if (e.dropoff_neighborhood) {<br /><span class="jx-dr__muted">{{ e.dropoff_neighborhood }}</span>}
                @if (e.dropoff_reference) {<br /><span class="jx-dr__muted">Ref.: {{ e.dropoff_reference }}</span>}
              </dd>
              @if (e.distance_m) {
                <dt>Distância</dt><dd class="jx-mono">{{ km(e.distance_m) }}</dd>
              }
            </dl>
          </section>

          <section class="jx-dr__bloco">
            <h3>Destinatário e itens</h3>
            <dl>
              <dt>Nome</dt><dd>{{ e.recipient_name || '—' }}</dd>
              <dt>Telefone</dt><dd class="jx-mono">{{ e.recipient_phone_masked || '—' }}</dd>
              <dt>Itens</dt><dd>{{ e.items_quantity }}× {{ e.items_description || 'sem descrição' }}</dd>
              @if (e.notes) {
                <dt>Observação</dt><dd>{{ e.notes }}</dd>
              }
            </dl>
          </section>

          <section class="jx-dr__bloco">
            <h3>Pagamento</h3>
            <dl>
              <dt>Forma</dt><dd>{{ pagamento[e.pagamento] || e.pagamento }}</dd>
              <dt>Frete</dt><dd class="jx-mono">{{ brl(e.price_cents) }}</dd>
              <dt>Taxa da plataforma</dt><dd class="jx-mono">{{ brl(e.fee_cents) }}</dd>
              <dt>Comprovação</dt><dd>{{ comprovacao[e.proof_method] || e.proof_method }}</dd>
            </dl>
          </section>

          @if (e.cancel_reason) {
            <section class="jx-dr__bloco">
              <h3>Cancelamento</h3>
              <p>{{ e.cancel_reason }}</p>
            </section>
          }

          <section class="jx-dr__bloco">
            <h3>Histórico</h3>
            @if (e.historico.length) {
              <ol class="jx-dr__linha">
                @for (h of e.historico; track $index) {
                  <li>
                    <span class="jx-dr__quando jx-mono">{{ dataHora(h.created_at) }}</span>
                    <strong>{{ rotulo(h.to_state) }}</strong>
                    @if (quem(h.actor_type)) {
                      <span class="jx-dr__muted">{{ quem(h.actor_type) }}</span>
                    }
                    @if (h.reason) {
                      <span class="jx-dr__motivo">{{ h.reason }}</span>
                    }
                  </li>
                }
              </ol>
            } @else {
              <p class="jx-dr__muted">Criada em {{ dataHora(e.created_at) }}. Sem outras mudanças registradas.</p>
            }
          </section>
        }
      </div>
    </aside>
  `,
  styles: `
    :host {
      position: fixed;
      inset: 0;
      z-index: 2000;
    }
    .jx-dr__fundo {
      position: absolute;
      inset: 0;
      background: rgba(0, 0, 0, 0.5); /* mesmo fundo dos outros modais */
    }
    .jx-dr {
      position: absolute;
      top: 0;
      right: 0;
      bottom: 0;
      display: flex;
      flex-direction: column;
      width: min(480px, 100vw);
      background: var(--surface-elevated);
      box-shadow: var(--shadow-lg);
      animation: jx-dr-in 200ms var(--jx-motion-easing-out, ease-out);
    }
    @keyframes jx-dr-in {
      from {
        transform: translateX(24px);
        opacity: 0;
      }
    }
    @media (prefers-reduced-motion: reduce) {
      .jx-dr {
        animation: none;
      }
    }
    .jx-dr__topo {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--jx-space-4) var(--jx-space-5);
      border-bottom: 1px solid var(--border);
    }
    .jx-dr__titulo {
      margin: 0;
      font-size: var(--jx-text-xl);
      font-weight: var(--jx-weight-extrabold);
      color: var(--text);
      outline: none;
    }
    .jx-dr__x {
      min-width: 44px;
      min-height: 44px;
      background: none;
      border: 0;
      border-radius: var(--jx-radius-md);
      color: var(--text-muted);
      font-size: var(--jx-text-lg);
      cursor: pointer;
    }
    .jx-dr__x:hover {
      background: var(--surface-hover);
      color: var(--text);
    }
    .jx-dr__x:focus-visible,
    .jx-dr__link:focus-visible {
      outline: none;
      box-shadow: var(--focus-ring);
    }
    .jx-dr__corpo {
      flex: 1;
      overflow-y: auto;
      padding: var(--jx-space-4) var(--jx-space-5) var(--jx-space-6);
      overscroll-behavior: contain;
      color: var(--text);
      font-size: var(--jx-text-sm);
    }
    .jx-dr__resumo {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: var(--jx-space-3);
      margin-bottom: var(--jx-space-4);
    }
    .jx-dr__link {
      margin-left: auto;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      color: var(--brand);
      font-weight: var(--jx-weight-bold);
      text-decoration: none;
    }
    .jx-dr__link:hover {
      text-decoration: underline;
    }
    .jx-dr__bloco {
      padding: var(--jx-space-4) 0;
      border-top: 1px solid var(--border);
    }
    .jx-dr__bloco h3 {
      margin: 0 0 var(--jx-space-3);
      font-size: var(--jx-text-xs);
      font-weight: var(--jx-weight-bold);
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--text-muted);
    }
    .jx-dr__bloco p {
      margin: 0;
    }
    dl {
      display: grid;
      grid-template-columns: minmax(110px, auto) 1fr;
      gap: var(--jx-space-2) var(--jx-space-4);
      margin: 0;
    }
    dt {
      color: var(--text-muted);
    }
    dd {
      margin: 0;
      overflow-wrap: anywhere;
    }
    .jx-mono {
      font-family: var(--jx-font-mono);
    }
    .jx-dr__muted {
      color: var(--text-muted);
    }
    .jx-dr__erro {
      color: var(--error);
    }
    .jx-dr__linha {
      list-style: none;
      margin: 0;
      padding: 0 0 0 var(--jx-space-4);
      border-left: 2px solid var(--border);
    }
    .jx-dr__linha li {
      position: relative;
      display: flex;
      flex-wrap: wrap;
      gap: 2px var(--jx-space-2);
      padding: 0 0 var(--jx-space-3);
    }
    .jx-dr__linha li::before {
      content: '';
      position: absolute;
      left: calc(-1 * var(--jx-space-4) - 6px);
      top: 4px;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--brand);
    }
    .jx-dr__quando {
      width: 100%;
      font-size: var(--jx-text-xs);
      color: var(--text-muted);
    }
    .jx-dr__motivo {
      width: 100%;
      font-size: var(--jx-text-xs);
      color: var(--text-muted);
      font-style: italic;
    }
  `,
})
export class EntregaDrawerComponent implements OnDestroy {
  private readonly svc = inject(AdminEntregasService);

  readonly entregaId = input.required<number>();
  readonly fechar = output<void>();

  protected readonly d = signal<AdminEntregaDetalhe | null>(null);
  protected readonly erro = signal<string | null>(null);
  protected readonly i = { fechar: faXmark, abrir: faArrowUpRightFromSquare };
  protected readonly pagamento = PAGAMENTO;
  protected readonly comprovacao = COMPROVACAO;
  private readonly tituloRef = viewChild<ElementRef<HTMLElement>>('titulo');
  private readonly origem = document.activeElement as HTMLElement | null;

  constructor() {
    effect(() => {
      const id = this.entregaId();
      this.d.set(null);
      this.erro.set(null);
      this.svc
        .detalhe(id)
        .then((r) => this.d.set(r))
        .catch(() => this.erro.set('Não foi possível carregar esta entrega. Ela pode não ser da sua cidade.'));
    });
    queueMicrotask(() => this.tituloRef()?.nativeElement.focus());
  }

  @HostListener('document:keydown.escape')
  protected onEsc(): void {
    this.fechar.emit();
  }

  ngOnDestroy(): void {
    this.origem?.focus?.();
  }

  protected estadoBadge(s: string): DeliveryState {
    return s as DeliveryState;
  }

  protected rotulo(s: string): string {
    return ESTADO_ROTULO[s] ?? s;
  }

  protected quem(t: string | null): string {
    return t ? (QUEM[t] ?? t) : ''; // registros antigos não guardam quem fez
  }

  protected brl(c: number | null): string {
    return c == null ? '—' : formatBrl(c / 100);
  }

  protected km(m: number): string {
    return `${(m / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} km`;
  }

  protected dataHora(iso: string | null): string {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
}
