import { TestBed } from '@angular/core/testing';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { GovernancaService } from './governanca.service';
import { AdminGovernancaDisputasPage } from './disputas.page';
import { AdminEntregadorDetalhePage } from './entregador-detalhe.page';

describe('GovernancaService', () => {
  let service: GovernancaService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        GovernancaService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(GovernancaService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('opens a suspension with a mandatory reason (audited)', async () => {
    const p = service.openSuspension('courier', 4, 'atrasos recorrentes');
    const req = httpMock.expectOne('/v1/admin/suspensions');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({
      subject_type: 'courier',
      subject_id: 4,
      reason: 'atrasos recorrentes',
    });
    req.flush({
      id: 1,
      subject_type: 'courier',
      subject_id: 4,
      reason: 'atrasos recorrentes',
      opened_at: '2026-06-11T12:00:00Z',
      sla_due_at: '2026-06-14T12:00:00Z',
      decision: null,
      decided_at: null,
      reverted_at: null,
    });
    expect((await p).subject_id).toBe(4);
  });

  it('records an appeal decision via PATCH', async () => {
    const p = service.decideAppeal(9, 'overturned');
    const req = httpMock.expectOne('/v1/admin/suspensions/9/decision');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ decision: 'overturned' });
    req.flush({
      id: 9,
      subject_type: 'courier',
      subject_id: 4,
      reason: 'x',
      opened_at: '2026-06-11T12:00:00Z',
      sla_due_at: '2026-06-14T12:00:00Z',
      decision: 'overturned',
      decided_at: '2026-06-12T12:00:00Z',
      reverted_at: '2026-06-12T12:00:00Z',
    });
    expect((await p).decision).toBe('overturned');
  });

  it('records an administrative dispute decision (NO financial effect)', async () => {
    const p = service.decideDispute(3, 'procedente', 'contexto');
    const req = httpMock.expectOne('/v1/admin/disputes/3/decision');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ outcome: 'procedente', note: 'contexto' });
    req.flush({
      id: 3,
      delivery_id: 10,
      courier_id: 4,
      status: 'resolved',
      reason: null,
      opened_at: '2026-06-10T12:00:00Z',
    });
    expect((await p).status).toBe('resolved');
  });

  it('sends a null note when none is given', async () => {
    const p = service.decideDispute(3, 'improcedente');
    const req = httpMock.expectOne('/v1/admin/disputes/3/decision');
    expect(req.request.body).toEqual({ outcome: 'improcedente', note: null });
    req.flush({
      id: 3,
      delivery_id: 10,
      courier_id: 4,
      status: 'resolved',
      reason: null,
      opened_at: '2026-06-10T12:00:00Z',
    });
    await p;
  });
});

describe('AdminGovernancaDisputasPage (signals + states)', () => {
  let httpMock: HttpTestingController;

  function build(): AdminGovernancaDisputasPage {
    TestBed.configureTestingModule({
      imports: [AdminGovernancaDisputasPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    });
    httpMock = TestBed.inject(HttpTestingController);
    return TestBed.createComponent(AdminGovernancaDisputasPage).componentInstance;
  }

  afterEach(() => httpMock.verify());

  it('moves disputes to empty when the area has none', async () => {
    const page = build() as unknown as {
      loadDisputes: () => Promise<void>;
      disputesState: () => string;
    };
    const p = page.loadDisputes();
    httpMock.expectOne((r) => r.url === '/v1/admin/disputes').flush([]);
    await p;
    expect(page.disputesState()).toBe('empty');
  });

  it('decides an appeal and reloads the list', async () => {
    const page = build() as unknown as {
      decideAppeal: (a: unknown, d: string) => Promise<void>;
      suspensions: () => unknown[];
    };
    const appeal = { id: 5 };
    const p = page.decideAppeal(appeal, 'overturned');
    httpMock.expectOne('/v1/admin/suspensions/5/decision').flush({
      id: 5,
      subject_type: 'courier',
      subject_id: 4,
      reason: 'x',
      opened_at: '2026-06-11T12:00:00Z',
      sla_due_at: '2026-06-14T12:00:00Z',
      decision: 'overturned',
      decided_at: '2026-06-12T12:00:00Z',
      reverted_at: '2026-06-12T12:00:00Z',
    });
    await Promise.resolve();
    await Promise.resolve();
    httpMock.expectOne((r) => r.url === '/v1/admin/suspensions').flush([]);
    await p;
    expect(page.suspensions().length).toBe(0);
  });
});

describe('AdminEntregadorDetalhePage (signals + states)', () => {
  let httpMock: HttpTestingController;

  function build(courierId = 7): AdminEntregadorDetalhePage {
    TestBed.configureTestingModule({
      imports: [AdminEntregadorDetalhePage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { paramMap: convertToParamMap({ courierId: String(courierId) }) },
          },
        },
      ],
    });
    httpMock = TestBed.inject(HttpTestingController);
    return TestBed.createComponent(AdminEntregadorDetalhePage).componentInstance;
  }

  afterEach(() => httpMock.verify());

  it('shows the score breakdown when a snapshot exists', async () => {
    const page = build(7) as unknown as {
      courierId: { set: (v: number) => void };
      loadScore: () => Promise<void>;
      scoreState: () => string;
      score: () => { level: string } | null;
    };
    page.courierId.set(7);
    const p = page.loadScore();
    httpMock.expectOne('/v1/admin/scores/7').flush({
      courier_id: 7,
      snapshot_date: '2026-06-11',
      total_score: 80,
      level: 'ouro',
      components: [],
    });
    await p;
    expect(page.scoreState()).toBe('ready');
    expect(page.score()?.level).toBe('ouro');
  });

  it('treats a 404 score as empty (not error)', async () => {
    const page = build(7) as unknown as {
      courierId: { set: (v: number) => void };
      loadScore: () => Promise<void>;
      scoreState: () => string;
    };
    page.courierId.set(7);
    const p = page.loadScore();
    httpMock
      .expectOne('/v1/admin/scores/7')
      .flush('no score', { status: 404, statusText: 'Not Found' });
    await p;
    expect(page.scoreState()).toBe('empty');
  });

  it('suspends with a mandatory reason and stores the new appeal', async () => {
    const page = build(7) as unknown as {
      courierId: { set: (v: number) => void };
      suspendForm: { setValue: (v: unknown) => void };
      confirmSuspend: () => Promise<void>;
      appeal: () => { subject_id: number } | null;
    };
    page.courierId.set(7);
    page.suspendForm.setValue({ reason: 'reclamações recorrentes' });
    const p = page.confirmSuspend();
    httpMock.expectOne('/v1/admin/suspensions').flush({
      id: 1,
      subject_type: 'courier',
      subject_id: 7,
      reason: 'reclamações recorrentes',
      opened_at: '2026-06-11T12:00:00Z',
      sla_due_at: '2026-06-14T12:00:00Z',
      decision: null,
      decided_at: null,
      reverted_at: null,
    });
    await p;
    expect(page.appeal()?.subject_id).toBe(7);
  });
});
