import { TestBed } from '@angular/core/testing';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { AdminApiKeysService } from './api-keys.service';
import { AdminApiKeysPage } from './api-keys.page';

describe('AdminApiKeysService', () => {
  let service: AdminApiKeysService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        AdminApiKeysService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(AdminApiKeysService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('lists keys from the admin area route', async () => {
    const p = service.listKeys(7);
    const req = httpMock.expectOne(
      (r) => r.url === '/v1/admin/areas/7/api-keys' && r.method === 'GET',
    );
    expect(req.request.params.get('limit')).toBe('20');
    req.flush({ items: [], total: 0 });
    await expectAsync(p).toBeResolvedTo({ items: [], total: 0 });
  });

  it('creates a key and returns the one-time secret', async () => {
    const p = service.createKey(7, 'Menu Certo', ['deliveries:write']);
    const req = httpMock.expectOne('/v1/admin/areas/7/api-keys');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({
      name: 'Menu Certo',
      scopes: ['deliveries:write'],
    });
    req.flush({
      id: 1,
      key_id: 'k_abc',
      name: 'Menu Certo',
      scopes: 'deliveries:write',
      secret: 'jxg_k_abc_secret',
    });
    const created = await p;
    expect(created.secret).toBe('jxg_k_abc_secret');
  });

  it('revokes a key via DELETE on its pk', async () => {
    const p = service.revokeKey(7, 99);
    const req = httpMock.expectOne('/v1/admin/areas/7/api-keys/99');
    expect(req.request.method).toBe('DELETE');
    req.flush({
      id: 99,
      key_id: 'k_x',
      name: 'X',
      scopes: 'deliveries:write',
      revoked: true,
      created_at: null,
      last_used_at: null,
    });
    expect((await p).revoked).toBeTrue();
  });

  it('configures the webhook with PUT', async () => {
    const p = service.configureWebhook(7, {
      url: 'https://x.com/hook',
      events: ['delivery.created'],
      enabled: true,
      rotate_secret: false,
    });
    const req = httpMock.expectOne('/v1/admin/areas/7/webhook');
    expect(req.request.method).toBe('PUT');
    req.flush({
      id: 1,
      url: 'https://x.com/hook',
      secret: 'whsec_1',
      events: 'delivery.created',
      enabled: true,
      created_at: null,
    });
    expect((await p).url).toBe('https://x.com/hook');
  });

  it('lists webhook deliveries (paginated)', async () => {
    const p = service.listDeliveries(7);
    const req = httpMock.expectOne(
      (r) =>
        r.url === '/v1/admin/areas/7/webhook/deliveries' && r.method === 'GET',
    );
    req.flush({ items: [], total: 0 });
    await expectAsync(p).toBeResolvedTo({ items: [], total: 0 });
  });
});

describe('AdminApiKeysPage (signals + states)', () => {
  let httpMock: HttpTestingController;

  function build(): AdminApiKeysPage {
    TestBed.configureTestingModule({
      imports: [AdminApiKeysPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    httpMock = TestBed.inject(HttpTestingController);
    return TestBed.createComponent(AdminApiKeysPage).componentInstance;
  }

  afterEach(() => httpMock.verify());

  it('moves keys to "empty" when the area has no keys', async () => {
    const page = build() as unknown as {
      loadKeys: () => Promise<void>;
      keysState: () => string;
    };
    const p = page.loadKeys();
    httpMock
      .expectOne((r) => r.url === '/v1/admin/areas/1/api-keys')
      .flush({ items: [], total: 0 });
    await p;
    expect(page.keysState()).toBe('empty');
  });

  it('moves keys to "ready" when there are keys', async () => {
    const page = build() as unknown as {
      loadKeys: () => Promise<void>;
      keysState: () => string;
      keys: () => unknown[];
    };
    const p = page.loadKeys();
    httpMock.expectOne((r) => r.url === '/v1/admin/areas/1/api-keys').flush({
      items: [
        {
          id: 1,
          key_id: 'k_a',
          name: 'A',
          scopes: 'deliveries:write',
          revoked: false,
          created_at: null,
          last_used_at: null,
        },
      ],
      total: 1,
    });
    await p;
    expect(page.keysState()).toBe('ready');
    expect(page.keys().length).toBe(1);
  });

  it('moves keys to "error" on a failed load', async () => {
    const page = build() as unknown as {
      loadKeys: () => Promise<void>;
      keysState: () => string;
    };
    const p = page.loadKeys();
    httpMock
      .expectOne((r) => r.url === '/v1/admin/areas/1/api-keys')
      .flush('boom', { status: 500, statusText: 'Server Error' });
    await p;
    expect(page.keysState()).toBe('error');
  });

  it('surfaces the one-time secret after a successful create', async () => {
    const page = build() as unknown as {
      createForm: { setValue: (v: unknown) => void };
      submitCreate: () => Promise<void>;
      createdSecret: () => { secret: string } | null;
      highlightedKeyId: () => string | null;
    };
    page.createForm.setValue({ name: 'Menu Certo', scopes: ['deliveries:write'] });
    const p = page.submitCreate();
    httpMock.expectOne('/v1/admin/areas/1/api-keys').flush({
      id: 5,
      key_id: 'k_new',
      name: 'Menu Certo',
      scopes: 'deliveries:write',
      secret: 'jxg_k_new_secret',
    });
    // The POST resolution schedules the list reload; let the microtask run.
    await Promise.resolve();
    await Promise.resolve();
    httpMock.expectOne((r) => r.method === 'GET').flush({ items: [], total: 0 });
    await p;
    expect(page.createdSecret()?.secret).toBe('jxg_k_new_secret');
    expect(page.highlightedKeyId()).toBe('k_new');
  });

  it('rejects a non-https webhook URL (anti-SSRF inline validation)', () => {
    const page = build() as unknown as {
      webhookForm: { controls: { url: { setValue: (v: string) => void; markAsTouched: () => void } } };
      urlError: () => string | null;
    };
    httpMock.match(() => true).forEach((r) => r.flush(null));
    page.webhookForm.controls.url.setValue('http://internal.local/hook');
    page.webhookForm.controls.url.markAsTouched();
    expect(page.urlError()).toContain('https://');
  });

  it('reveals the rotated webhook secret only when it actually changes', async () => {
    const page = build() as unknown as {
      webhook: (v?: unknown) => unknown;
      webhookForm: { setValue: (v: unknown) => void };
      saveWebhook: (rotate?: boolean) => Promise<void>;
      rotatedSecret: () => string | null;
    };
    // seed the current secret
    (page.webhook as (v: unknown) => void)({
      id: 1,
      url: 'https://x.com/h',
      secret: 'whsec_old',
      events: '',
      enabled: true,
      created_at: null,
    });
    page.webhookForm.setValue({
      url: 'https://x.com/h',
      events: [],
      enabled: true,
    });
    const p = page.saveWebhook(true);
    httpMock.expectOne('/v1/admin/areas/1/webhook').flush({
      id: 1,
      url: 'https://x.com/h',
      secret: 'whsec_new',
      events: '',
      enabled: true,
      created_at: null,
    });
    await p;
    expect(page.rotatedSecret()).toBe('whsec_new');
  });
});
