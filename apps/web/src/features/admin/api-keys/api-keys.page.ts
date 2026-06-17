import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  OnInit,
  ViewChild,
  computed,
  inject,
  signal,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import {
  DataTableColumn,
  DataTableComponent,
  DataTableState,
} from '@jaxego/shared/components/data-table/data-table.component';
import { SecretRevealComponent } from '@jaxego/shared/components/secret-reveal/secret-reveal.component';
import { ErrorStateComponent } from '@jaxego/shared/state/error-state.component';
import {
  AdminApiKeysService,
  API_KEY_SCOPES,
  ApiKey,
  ApiKeyCreated,
  WEBHOOK_EVENTS,
  WebhookDelivery,
  WebhookEndpoint,
} from './api-keys.service';

/** Mapeia o status de entrega de webhook ao token semântico + rótulo pt-BR. */
const DELIVERY_STATUS_META: Record<
  WebhookDelivery['status'],
  { label: string; tone: 'success' | 'warning' | 'error' }
> = {
  delivered: { label: 'Entregue', tone: 'success' },
  pending: { label: 'Pendente', tone: 'warning' },
  failed: { label: 'Falhou', tone: 'error' },
};

interface WebhookEventOption {
  value: string;
  label: string;
}

/** Rótulos pt-BR sem jargão para os eventos (UI-SPEC §copy). */
const EVENT_LABELS: Record<string, string> = {
  'delivery.created': 'Entrega criada',
  'delivery.accepted': 'Entrega aceita',
  'delivery.collected': 'Entrega coletada',
  'delivery.delivered': 'Entrega concluída',
  'delivery.finalized': 'Entrega finalizada',
  'delivery.canceled': 'Entrega cancelada',
};

/**
 * Tela 22 — Admin de área · Chaves de API & Webhook (UI-SPEC / D-10).
 *
 * Lista de chaves (jx-data-table), criação com segredo exibido 1× (jx-secret-reveal),
 * revogação com confirmação sensível before→after (padrão Phase 6), e painel de
 * webhook (URL + secret + eventos + histórico de entregas). Estados empty/loading/
 * error em todas as listas. Tokens semânticos; AA nos 2 temas (DEC-001). pt-BR.
 */
@Component({
  selector: 'jx-admin-api-keys-page',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    DataTableComponent,
    SecretRevealComponent,
    ErrorStateComponent,
  ],
  templateUrl: './api-keys.page.html',
  styleUrl: './api-keys.page.scss',
})
export class AdminApiKeysPage implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly service = inject(AdminApiKeysService);

  // A área vem do escopo do token do admin; rota /admin/api-keys (M1: área única).
  protected areaId = 1;

  // --- Lista de chaves ------------------------------------------------------
  protected readonly keysState = signal<DataTableState>('loading');
  protected readonly keys = signal<ApiKey[]>([]);
  protected readonly highlightedKeyId = signal<string | null>(null);

  protected readonly keyColumns: DataTableColumn[] = [
    { key: 'name', label: 'Nome' },
    { key: 'key_id', label: 'ID da chave' },
    { key: 'scopes', label: 'Escopos' },
    { key: 'created_at', label: 'Criada em' },
    { key: 'last_used_at', label: 'Último uso' },
    { key: 'status', label: 'Status' },
  ];

  // --- Criação de chave -----------------------------------------------------
  protected readonly creating = signal(false);
  protected readonly createSubmitting = signal(false);
  protected readonly createError = signal<string | null>(null);
  protected readonly createdSecret = signal<ApiKeyCreated | null>(null);

  protected readonly scopeOptions = API_KEY_SCOPES;
  protected readonly createForm = this.fb.nonNullable.group({
    name: this.fb.nonNullable.control('', [
      Validators.required,
      Validators.minLength(2),
      Validators.maxLength(120),
    ]),
    scopes: this.fb.nonNullable.control<string[]>(['deliveries:write']),
  });

  // --- Revogação ------------------------------------------------------------
  protected readonly revoking = signal<ApiKey | null>(null);
  protected readonly revokeSubmitting = signal(false);
  protected readonly revokeError = signal<string | null>(null);

  // --- Webhook --------------------------------------------------------------
  protected readonly webhookState = signal<DataTableState>('loading');
  protected readonly webhook = signal<WebhookEndpoint | null>(null);
  protected readonly webhookLoadError = signal<string | null>(null);
  protected readonly webhookSaving = signal(false);
  protected readonly webhookSaved = signal(false);
  protected readonly webhookSaveError = signal<string | null>(null);
  protected readonly rotatedSecret = signal<string | null>(null);

  protected readonly eventOptions: WebhookEventOption[] = WEBHOOK_EVENTS.map(
    (value) => ({ value, label: EVENT_LABELS[value] ?? value }),
  );

  protected readonly webhookForm = this.fb.nonNullable.group({
    url: this.fb.nonNullable.control('', [
      Validators.required,
      Validators.pattern(/^https:\/\/.+/),
    ]),
    events: this.fb.nonNullable.control<string[]>([]),
    enabled: this.fb.nonNullable.control(true),
  });

  // --- Histórico de entregas ------------------------------------------------
  protected readonly deliveriesState = signal<DataTableState>('loading');
  protected readonly deliveries = signal<WebhookDelivery[]>([]);

  protected readonly deliveryColumns: DataTableColumn[] = [
    { key: 'event_type', label: 'Evento' },
    { key: 'attempts', label: 'Tentativa', numeric: true },
    { key: 'last_status_code', label: 'Status HTTP', numeric: true },
    { key: 'next_retry_at', label: 'Próx. tentativa' },
    { key: 'created_at', label: 'Quando' },
    { key: 'status', label: 'Resultado' },
  ];

  // Restaura o foco ao gatilho ao fechar modais (a11y — retorno de foco).
  @ViewChild('createTrigger') private createTrigger?: ElementRef<HTMLButtonElement>;

  protected readonly hasKeys = computed(() => this.keys().length > 0);

  async ngOnInit(): Promise<void> {
    await Promise.all([
      this.loadKeys(),
      this.loadWebhook(),
      this.loadDeliveries(),
    ]);
  }

  // --- Carregamento ---------------------------------------------------------
  protected async loadKeys(): Promise<void> {
    this.keysState.set('loading');
    try {
      const res = await this.service.listKeys(this.areaId);
      this.keys.set(res.items);
      this.keysState.set(res.items.length === 0 ? 'empty' : 'ready');
    } catch {
      this.keysState.set('error');
    }
  }

  protected async loadWebhook(): Promise<void> {
    this.webhookState.set('loading');
    this.webhookLoadError.set(null);
    try {
      const endpoint = await this.service.getWebhook(this.areaId);
      this.webhook.set(endpoint);
      if (endpoint) {
        this.webhookForm.patchValue({
          url: endpoint.url,
          events: endpoint.events ? endpoint.events.split(' ').filter(Boolean) : [],
          enabled: endpoint.enabled,
        });
      }
      this.webhookState.set('ready');
    } catch {
      this.webhookState.set('error');
      this.webhookLoadError.set(
        'Não conseguimos carregar a configuração de webhook. Tente de novo.',
      );
    }
  }

  protected async loadDeliveries(): Promise<void> {
    this.deliveriesState.set('loading');
    try {
      const res = await this.service.listDeliveries(this.areaId);
      this.deliveries.set(res.items);
      this.deliveriesState.set(res.items.length === 0 ? 'empty' : 'ready');
    } catch {
      this.deliveriesState.set('error');
    }
  }

  // --- Criação --------------------------------------------------------------
  protected openCreate(): void {
    this.createError.set(null);
    this.createdSecret.set(null);
    this.createForm.reset({ name: '', scopes: ['deliveries:write'] });
    this.creating.set(true);
  }

  protected closeCreate(): void {
    this.creating.set(false);
    this.createdSecret.set(null);
    this.createTrigger?.nativeElement.focus();
  }

  protected toggleScope(scope: string, checked: boolean): void {
    const current = this.createForm.controls.scopes.value;
    const next = checked
      ? Array.from(new Set([...current, scope]))
      : current.filter((s) => s !== scope);
    this.createForm.controls.scopes.setValue(next);
  }

  protected isScopeSelected(scope: string): boolean {
    return this.createForm.controls.scopes.value.includes(scope);
  }

  protected nameError(): string | null {
    const ctrl = this.createForm.controls.name;
    if (!ctrl.touched || ctrl.valid) {
      return null;
    }
    return 'Dê um nome com pelo menos 2 caracteres para identificar a chave.';
  }

  async submitCreate(): Promise<void> {
    if (this.createForm.invalid) {
      this.createForm.markAllAsTouched();
      return;
    }
    this.createSubmitting.set(true);
    this.createError.set(null);
    try {
      const v = this.createForm.getRawValue();
      const created = await this.service.createKey(this.areaId, v.name, v.scopes);
      this.createdSecret.set(created);
      this.highlightedKeyId.set(created.key_id);
      await this.loadKeys();
      // Remove o destaque após ~2s (UI-SPEC: key nova destacada).
      setTimeout(() => this.highlightedKeyId.set(null), 2000);
    } catch {
      this.createError.set(
        'Não conseguimos criar a chave agora. Tente de novo em instantes.',
      );
    } finally {
      this.createSubmitting.set(false);
    }
  }

  // --- Revogação ------------------------------------------------------------
  protected requestRevoke(key: ApiKey): void {
    this.revokeError.set(null);
    this.revoking.set(key);
  }

  protected cancelRevoke(): void {
    this.revoking.set(null);
  }

  async confirmRevoke(): Promise<void> {
    const key = this.revoking();
    if (!key) {
      return;
    }
    this.revokeSubmitting.set(true);
    this.revokeError.set(null);
    try {
      await this.service.revokeKey(this.areaId, key.id);
      this.revoking.set(null);
      await this.loadKeys();
    } catch {
      this.revokeError.set(
        'Não conseguimos revogar a chave agora. Tente de novo.',
      );
    } finally {
      this.revokeSubmitting.set(false);
    }
  }

  // --- Webhook --------------------------------------------------------------
  protected toggleEvent(event: string, checked: boolean): void {
    const current = this.webhookForm.controls.events.value;
    const next = checked
      ? Array.from(new Set([...current, event]))
      : current.filter((e) => e !== event);
    this.webhookForm.controls.events.setValue(next);
  }

  protected isEventSelected(event: string): boolean {
    return this.webhookForm.controls.events.value.includes(event);
  }

  protected urlError(): string | null {
    const ctrl = this.webhookForm.controls.url;
    if (!ctrl.touched || ctrl.valid) {
      return null;
    }
    if (ctrl.hasError('required')) {
      return 'Informe a URL https para onde enviaremos as notificações.';
    }
    return 'A URL precisa começar com https:// (não aceitamos http nem hosts internos).';
  }

  async saveWebhook(rotateSecret = false): Promise<void> {
    if (this.webhookForm.invalid) {
      this.webhookForm.markAllAsTouched();
      return;
    }
    this.webhookSaving.set(true);
    this.webhookSaved.set(false);
    this.webhookSaveError.set(null);
    this.rotatedSecret.set(null);
    try {
      const v = this.webhookForm.getRawValue();
      const previousSecret = this.webhook()?.secret ?? null;
      const endpoint = await this.service.configureWebhook(this.areaId, {
        url: v.url,
        events: v.events,
        enabled: v.enabled,
        rotate_secret: rotateSecret,
      });
      this.webhook.set(endpoint);
      this.webhookSaved.set(true);
      // Se o secret mudou (rotação), exibe-o 1× via jx-secret-reveal.
      if (rotateSecret && endpoint.secret !== previousSecret) {
        this.rotatedSecret.set(endpoint.secret);
      }
    } catch {
      this.webhookSaveError.set(
        'Não conseguimos salvar o webhook. Verifique a URL e tente de novo.',
      );
    } finally {
      this.webhookSaving.set(false);
    }
  }

  protected dismissRotatedSecret(): void {
    this.rotatedSecret.set(null);
  }

  // --- Helpers de exibição --------------------------------------------------
  protected keyStatusLabel(key: ApiKey): string {
    return key.revoked ? 'Revogada' : 'Ativa';
  }

  protected keyStatusTone(key: ApiKey): 'success' | 'error' {
    return key.revoked ? 'error' : 'success';
  }

  protected deliveryStatusLabel(status: WebhookDelivery['status']): string {
    return DELIVERY_STATUS_META[status].label;
  }

  protected deliveryStatusTone(
    status: WebhookDelivery['status'],
  ): 'success' | 'warning' | 'error' {
    return DELIVERY_STATUS_META[status].tone;
  }

  protected formatDate(iso: string | null): string {
    if (!iso) {
      return '—';
    }
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) {
      return iso;
    }
    return d.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  protected eventLabel(event: string): string {
    return EVENT_LABELS[event] ?? event;
  }

  protected trackKey = (item: unknown): unknown => (item as ApiKey).id;
  protected trackDelivery = (item: unknown): unknown =>
    (item as WebhookDelivery).id;
}
