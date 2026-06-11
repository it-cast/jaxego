import { TestBed } from '@angular/core/testing';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { PlatformAdminService } from './platform-admin.service';
import { PlataformaVisaoGeralPage } from './visao-geral.page';
import { PlataformaPessoasPage } from './pessoas.page';
import { PlataformaDisputasPage } from './disputas.page';

describe('PlatformAdminService', () => {
  let service: PlatformAdminService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        PlatformAdminService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(PlatformAdminService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('reads the platform overview', async () => {
    const p = service.overview();
    const req = httpMock.expectOne(
      (r) => r.url === '/v1/platform/overview' && r.method === 'GET',
    );
    req.flush([]);
    await expectAsync(p).toBeResolvedTo([]);
  });

  it('searches couriers with bound q + area filters', async () => {
    const p = service.searchCouriers({ q: 'ana', areaId: 3 });
    const req = httpMock.expectOne((r) => r.url === '/v1/platform/couriers');
    expect(req.request.params.get('q')).toBe('ana');
    expect(req.request.params.get('area_id')).toBe('3');
    req.flush([]);
    await p;
  });

  it('omits empty filters from the courier search', async () => {
    const p = service.searchCouriers({});
    const req = httpMock.expectOne((r) => r.url === '/v1/platform/couriers');
    expect(req.request.params.has('q')).toBeFalse();
    expect(req.request.params.has('area_id')).toBeFalse();
    req.flush([]);
    await p;
  });

  it('sets the revenue share via PUT (config only — no money)', async () => {
    const p = service.setRevenueShare(2, 12.5);
    const req = httpMock.expectOne('/v1/platform/areas/2/revenue-share');
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual({ share_pct: 12.5 });
    req.flush({
      area_id: 2,
      share_pct: 12.5,
      effective_from: '2026-06-11T00:00:00Z',
    });
    expect((await p).share_pct).toBe(12.5);
  });

  it('reads a courier score breakdown from the admin route', async () => {
    const p = service.courierScore(9);
    const req = httpMock.expectOne('/v1/admin/scores/9');
    expect(req.request.method).toBe('GET');
    req.flush({
      courier_id: 9,
      snapshot_date: '2026-06-11',
      total_score: 80,
      level: 'ouro',
      components: [],
    });
    expect((await p).level).toBe('ouro');
  });
});

describe('PlataformaVisaoGeralPage (signals + states)', () => {
  let httpMock: HttpTestingController;

  function build(): PlataformaVisaoGeralPage {
    TestBed.configureTestingModule({
      imports: [PlataformaVisaoGeralPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    });
    httpMock = TestBed.inject(HttpTestingController);
    return TestBed.createComponent(PlataformaVisaoGeralPage).componentInstance;
  }

  afterEach(() => httpMock.verify());

  it('moves to empty when there are no areas', async () => {
    const page = build() as unknown as {
      load: () => Promise<void>;
      state: () => string;
    };
    const p = page.load();
    httpMock.expectOne('/v1/platform/overview').flush([]);
    await p;
    expect(page.state()).toBe('empty');
  });

  it('aggregates KPIs and loads revenue share per area', async () => {
    const page = build() as unknown as {
      load: () => Promise<void>;
      state: () => string;
      totalCouriers: () => number;
      revenueLabel: (id: number) => string;
    };
    const p = page.load();
    httpMock.expectOne('/v1/platform/overview').flush([
      {
        area_id: 1,
        codename: 'centro',
        name: 'Centro',
        couriers: 5,
        merchants: 3,
        deliveries: 40,
      },
    ]);
    await Promise.resolve();
    await Promise.resolve();
    httpMock
      .expectOne('/v1/platform/areas/1/revenue-share')
      .flush({ area_id: 1, share_pct: 10, effective_from: '2026-06-11T00:00:00Z' });
    await p;
    expect(page.state()).toBe('ready');
    expect(page.totalCouriers()).toBe(5);
    expect(page.revenueLabel(1)).toContain('10% parametrizado');
  });

  it('moves to error when the overview fails', async () => {
    const page = build() as unknown as {
      load: () => Promise<void>;
      state: () => string;
    };
    const p = page.load();
    httpMock
      .expectOne('/v1/platform/overview')
      .flush('boom', { status: 500, statusText: 'Server Error' });
    await p;
    expect(page.state()).toBe('error');
  });
});

describe('PlataformaPessoasPage (signals + states)', () => {
  let httpMock: HttpTestingController;

  function build(): PlataformaPessoasPage {
    TestBed.configureTestingModule({
      imports: [PlataformaPessoasPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    });
    httpMock = TestBed.inject(HttpTestingController);
    return TestBed.createComponent(PlataformaPessoasPage).componentInstance;
  }

  afterEach(() => httpMock.verify());

  it('loads couriers and opens the score breakdown drawer', async () => {
    const page = build() as unknown as {
      search: () => Promise<void>;
      couriersState: () => string;
      openBreakdown: (c: unknown) => Promise<void>;
      scoreState: () => string;
      score: () => { level: string } | null;
    };
    const ps = page.search();
    httpMock.expectOne((r) => r.url === '/v1/platform/couriers').flush([
      {
        courier_id: 7,
        area_id: 1,
        full_name: 'Ana',
        status: 'active',
        score_total: 80,
        score_level: 'ouro',
      },
    ]);
    await ps;
    expect(page.couriersState()).toBe('ready');

    const pb = page.openBreakdown({ courier_id: 7, full_name: 'Ana' });
    httpMock.expectOne('/v1/admin/scores/7').flush({
      courier_id: 7,
      snapshot_date: '2026-06-11',
      total_score: 80,
      level: 'ouro',
      components: [],
    });
    await pb;
    expect(page.scoreState()).toBe('ready');
    expect(page.score()?.level).toBe('ouro');
  });
});

describe('PlataformaDisputasPage (signals + states)', () => {
  let httpMock: HttpTestingController;

  function build(): PlataformaDisputasPage {
    TestBed.configureTestingModule({
      imports: [PlataformaDisputasPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    });
    httpMock = TestBed.inject(HttpTestingController);
    return TestBed.createComponent(PlataformaDisputasPage).componentInstance;
  }

  afterEach(() => httpMock.verify());

  it('loads the global disputes list', async () => {
    const page = build() as unknown as {
      loadDisputes: () => Promise<void>;
      disputesState: () => string;
    };
    const p = page.loadDisputes();
    httpMock.expectOne((r) => r.url === '/v1/platform/disputes').flush([]);
    await p;
    expect(page.disputesState()).toBe('empty');
  });
});
