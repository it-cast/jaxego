import { ChangeDetectionStrategy, Component, OnDestroy, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faMagnifyingGlass, faXmark } from '@fortawesome/free-solid-svg-icons';
import {
  DataTableColumn,
  DataTableComponent,
  DataTableState,
} from '@jaxego/shared/components/data-table/data-table.component';
import { StateBadgeComponent, type DeliveryState } from '@jaxego/shared/components/state-badge/state-badge.component';
import { formatBrl } from '@jaxego/shared/util/money';
import { AdminEntrega, AdminEntregasService, FiltroOpcao } from './admin-entregas.service';
import { EntregaDrawerComponent } from './entrega-drawer.component';

const POR_PAGINA = 20;
const EM_ANDAMENTO: DeliveryState[] = ['CRIADA', 'SEM_RESPOSTA', 'ACEITA', 'COLETADA'];

/** Atalhos de status. "Todas" e "Em andamento" sempre; os outros só se houver entregas. */
const ATALHOS: { chave: string; rotulo: string; estados: DeliveryState[]; fixo?: boolean }[] = [
  { chave: '', rotulo: 'Todas', estados: [], fixo: true },
  { chave: 'andamento', rotulo: 'Em andamento', estados: EM_ANDAMENTO, fixo: true },
  { chave: 'AGENDADA', rotulo: 'Agendadas', estados: ['AGENDADA'] },
  { chave: 'AGUARDANDO_PAGAMENTO', rotulo: 'Aguardando PIX', estados: ['AGUARDANDO_PAGAMENTO'] },
  { chave: 'CRIADA', rotulo: 'Procurando', estados: ['CRIADA'] },
  { chave: 'SEM_RESPOSTA', rotulo: 'Sem resposta', estados: ['SEM_RESPOSTA'] },
  { chave: 'ACEITA', rotulo: 'Indo coletar', estados: ['ACEITA'] },
  { chave: 'COLETADA', rotulo: 'A caminho', estados: ['COLETADA'] },
  { chave: 'ENTREGUE', rotulo: 'Entregues', estados: ['ENTREGUE'] },
  { chave: 'RECUSADA_NO_DESTINO', rotulo: 'Recusadas no destino', estados: ['RECUSADA_NO_DESTINO'] },
  { chave: 'FINALIZADA', rotulo: 'Finalizadas', estados: ['FINALIZADA'] },
  { chave: 'CANCELADA', rotulo: 'Canceladas', estados: ['CANCELADA'] },
];

export const PAGAMENTO_ROTULO: Record<string, string> = { direct: 'Direto', pix: 'PIX', card: 'Cartão' };

/**
 * Entregas da cidade (admin da área): busca por nº/referência/loja/entregador, atalhos
 * por status com contagem, filtros (loja, entregador, pagamento, período), paginação e
 * detalhe com histórico. Os filtros ficam na URL (voltar e compartilhar funcionam).
 */
@Component({
  selector: 'jx-admin-entregas',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DataTableComponent, StateBadgeComponent, FaIconComponent, EntregaDrawerComponent],
  templateUrl: './entregas.page.html',
  styleUrl: './entregas.page.scss',
})
export class AdminEntregasPage implements OnDestroy {
  private readonly svc = inject(AdminEntregasService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  protected readonly i = { busca: faMagnifyingGlass, limpar: faXmark };
  protected readonly pagamentoRotulo = PAGAMENTO_ROTULO;
  protected readonly colunas: DataTableColumn[] = [
    { key: 'id', label: 'Nº' },
    { key: 'criada', label: 'Criada em' },
    { key: 'loja', label: 'Loja' },
    { key: 'entregador', label: 'Entregador' },
    { key: 'destino', label: 'Destino' },
    { key: 'pagamento', label: 'Pagamento' },
    { key: 'valor', label: 'Frete', numeric: true },
    { key: 'status', label: 'Status' },
  ];
  protected readonly trackById = (r: unknown) => (r as AdminEntrega).id;

  // Filtros (espelham a URL)
  protected readonly busca = signal('');
  protected readonly atalho = signal('');
  protected readonly loja = signal<number | null>(null);
  protected readonly entregador = signal<number | null>(null);
  protected readonly pagamento = signal('');
  protected readonly de = signal('');
  protected readonly ate = signal('');
  protected readonly pagina = signal(0);

  protected readonly linhas = signal<AdminEntrega[]>([]);
  protected readonly total = signal(0);
  protected readonly porEstado = signal<Partial<Record<DeliveryState, number>>>({});
  protected readonly estado = signal<DataTableState>('loading');
  protected readonly lojas = signal<FiltroOpcao[]>([]);
  protected readonly entregadores = signal<FiltroOpcao[]>([]);
  protected readonly aberta = signal<number | null>(null);

  protected readonly totalPaginas = computed(() => Math.max(1, Math.ceil(this.total() / POR_PAGINA)));
  protected readonly temFiltro = computed(
    () => !!(this.busca() || this.atalho() || this.loja() || this.entregador() || this.pagamento() || this.de() || this.ate())
  );
  protected readonly atalhos = computed(() => {
    const cont = this.porEstado();
    const soma = (estados: DeliveryState[]) =>
      estados.length ? estados.reduce((t, e) => t + (cont[e] ?? 0), 0) : Object.values(cont).reduce((t, n) => t + (n ?? 0), 0);
    return ATALHOS.map((a) => ({ ...a, total: soma(a.estados) })).filter(
      (a) => a.fixo || a.total > 0 || a.chave === this.atalho()
    );
  });

  private versao = 0;
  private buscaTimer: ReturnType<typeof setTimeout> | null = null;
  private readonly sub = this.route.queryParamMap.subscribe((p) => {
    this.busca.set(p.get('q') ?? '');
    this.atalho.set(p.get('status') ?? '');
    this.loja.set(p.get('loja') ? Number(p.get('loja')) : null);
    this.entregador.set(p.get('entregador') ? Number(p.get('entregador')) : null);
    this.pagamento.set(p.get('pagamento') ?? '');
    this.de.set(p.get('de') ?? '');
    this.ate.set(p.get('ate') ?? '');
    this.pagina.set(Math.max(0, Number(p.get('pagina') ?? 1) - 1));
    const entrega = Number(p.get('entrega'));
    this.aberta.set(Number.isFinite(entrega) && entrega > 0 ? entrega : null);
    void this.carregar();
  });

  constructor() {
    this.svc
      .opcoes()
      .then((o) => {
        this.lojas.set(o.lojas);
        this.entregadores.set(o.entregadores);
      })
      .catch(() => undefined);
  }

  ngOnDestroy(): void {
    this.sub.unsubscribe();
    if (this.buscaTimer) clearTimeout(this.buscaTimer);
  }

  protected async carregar(): Promise<void> {
    const v = ++this.versao;
    this.estado.set('loading');
    const atalho = ATALHOS.find((a) => a.chave === this.atalho());
    try {
      const r = await this.svc.listar({
        q: this.busca().trim() || undefined,
        state: atalho?.estados.join(',') || undefined,
        merchant_id: this.loja(),
        courier_id: this.entregador(),
        payment_method: this.pagamento() || undefined,
        inicio: this.de() ? new Date(`${this.de()}T00:00:00`).toISOString() : null,
        fim: this.ate() ? new Date(`${this.ate()}T23:59:59.999`).toISOString() : null,
        limit: POR_PAGINA,
        offset: this.pagina() * POR_PAGINA,
      });
      if (v !== this.versao) return; // resposta velha (filtro mudou no meio)
      this.linhas.set(r.items);
      this.total.set(r.total);
      this.porEstado.set(r.por_estado);
      this.estado.set(r.items.length ? 'ready' : 'empty');
    } catch {
      if (v === this.versao) this.estado.set('error');
    }
  }

  /** Atualiza a URL (que dispara a busca). Mudar filtro volta para a página 1. */
  private aplicar(mudancas: Record<string, string | number | null>, opts: { manterPagina?: boolean; substituir?: boolean } = {}): void {
    const params: Record<string, string | number | null> = { ...mudancas };
    if (!opts.manterPagina) params['pagina'] = null;
    for (const k of Object.keys(params)) if (params[k] === '' ) params[k] = null;
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: params,
      queryParamsHandling: 'merge',
      replaceUrl: opts.substituir ?? false,
    });
  }

  protected digitarBusca(valor: string): void {
    this.busca.set(valor);
    if (this.buscaTimer) clearTimeout(this.buscaTimer);
    this.buscaTimer = setTimeout(() => this.aplicar({ q: valor.trim() }, { substituir: true }), 350);
  }

  protected escolherAtalho(chave: string): void {
    this.aplicar({ status: chave });
  }

  protected filtrar(campo: 'loja' | 'entregador' | 'pagamento' | 'de' | 'ate', valor: string): void {
    this.aplicar({ [campo]: valor });
  }

  protected limpar(): void {
    void this.router.navigate([], { relativeTo: this.route, queryParams: {} });
  }

  protected irPara(pagina: number): void {
    this.aplicar({ pagina: pagina + 1 }, { manterPagina: true });
  }

  protected abrir(id: number): void {
    this.aplicar({ entrega: id }, { manterPagina: true });
  }

  protected fechar(): void {
    this.aplicar({ entrega: null }, { manterPagina: true });
  }

  protected brl(cents: number | null): string {
    return cents == null ? '—' : formatBrl(cents / 100);
  }

  protected dataHora(iso: string | null): string {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  }
}
