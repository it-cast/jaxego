import { TestBed } from '@angular/core/testing';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { SaldoService } from './saldo.service';

describe('SaldoService', () => {
  let service: SaldoService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        SaldoService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(SaldoService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('reads the balance + minimum from GET /v1/withdrawals/balance', async () => {
    const promise = service.balance();
    const req = http.expectOne('/v1/withdrawals/balance');
    expect(req.request.method).toBe('GET');
    req.flush({ balance_cents: 12000, minimum_cents: 2000 });
    const balance = await promise;
    expect(balance.balance_cents).toBe(12000);
    // The minimum comes from the backend, never hardcoded in the client.
    expect(balance.minimum_cents).toBe(2000);
  });

  it('reads the extract from GET /v1/withdrawals/extract', async () => {
    const promise = service.extract();
    const req = http.expectOne('/v1/withdrawals/extract');
    expect(req.request.method).toBe('GET');
    req.flush([
      { id: 1, kind: 'credit', delivery_id: 5, amount_cents: 1500, at: null },
    ]);
    const rows = await promise;
    expect(rows[0].kind).toBe('credit');
  });

  it('reads the withdrawal history from GET /v1/withdrawals/history', async () => {
    const promise = service.history();
    const req = http.expectOne('/v1/withdrawals/history');
    expect(req.request.method).toBe('GET');
    req.flush([
      {
        id: 1,
        amount_cents: 2000,
        status: 'paid',
        transaction_id: 'tx1',
        settled_at: null,
        requested_at: null,
      },
    ]);
    const rows = await promise;
    expect(rows[0].status).toBe('paid');
  });

  it('requests a withdrawal via POST /v1/withdrawals with the idempotency key', async () => {
    const promise = service.requestWithdrawal(2000, 'wd_123');
    const req = http.expectOne('/v1/withdrawals');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({
      amount_cents: 2000,
      idempotency_key: 'wd_123',
    });
    req.flush({ id: 9, amount_cents: 2000, status: 'pending', transaction_id: null });
    const result = await promise;
    expect(result.id).toBe(9);
  });
});
