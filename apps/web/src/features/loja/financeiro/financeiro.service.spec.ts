import { TestBed } from '@angular/core/testing';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { LojaFinanceiroService } from './financeiro.service';

describe('LojaFinanceiroService', () => {
  let service: LojaFinanceiroService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        LojaFinanceiroService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(LojaFinanceiroService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('lists invoices from GET /v1/invoices', async () => {
    const promise = service.invoices();
    const req = http.expectOne('/v1/invoices');
    expect(req.request.method).toBe('GET');
    req.flush([
      {
        id: 1,
        competence: '2026-05',
        amount_cents: 24500,
        status: 'open',
        due_at: '2026-06-10T00:00:00Z',
      },
    ]);
    const invoices = await promise;
    expect(invoices.length).toBe(1);
    expect(invoices[0].amount_cents).toBe(24500);
  });

  it('loads invoice lines from GET /v1/invoices/{id}/lines', async () => {
    const promise = service.invoiceLines(7);
    const req = http.expectOne('/v1/invoices/7/lines');
    expect(req.request.method).toBe('GET');
    req.flush([
      { id: 1, delivery_id: 99, description: 'Taxa — entrega #99', amount_cents: 350 },
    ]);
    const lines = await promise;
    expect(lines[0].delivery_id).toBe(99);
  });

  it('pays an invoice via POST /v1/invoices/{id}/pay', async () => {
    const promise = service.payInvoice(3);
    const req = http.expectOne('/v1/invoices/3/pay');
    expect(req.request.method).toBe('POST');
    req.flush({
      id: 3,
      competence: '2026-05',
      amount_cents: 24500,
      status: 'paid',
      due_at: '2026-06-10T00:00:00Z',
      paid_at: '2026-06-05T10:00:00Z',
    });
    const invoice = await promise;
    expect(invoice.status).toBe('paid');
  });

  it('loads a direct-payment receipt from GET /v1/deliveries/{id}/receipt', async () => {
    const promise = service.receipt(42);
    const req = http.expectOne('/v1/deliveries/42/receipt');
    expect(req.request.method).toBe('GET');
    req.flush({
      delivery_id: 42,
      public_token: 'tok_abc',
      reference_number: 'NF-100',
      amount_cents: 2500,
      outcome: 'pix',
      status: 'ENTREGUE',
      confirmed_at: '2026-06-05T10:00:00Z',
    });
    const receipt = await promise;
    expect(receipt.public_token).toBe('tok_abc');
    expect(receipt.amount_cents).toBe(2500);
  });
});
