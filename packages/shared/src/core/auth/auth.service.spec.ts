import { TestBed } from '@angular/core/testing';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { AuthService } from './auth.service';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        AuthService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('200: stores access token in memory and authenticates', async () => {
    const promise = service.login({
      email: 'a@b.com.br',
      password: 'senhasegura1',
    });
    const req = httpMock.expectOne('/v1/auth/login');
    expect(req.request.withCredentials).toBeTrue();
    req.flush({
      access_token: 'tok',
      refresh_token: 'r',
      token_type: 'bearer',
      expires_in: 900,
    });
    const res = await promise;
    expect(res.ok).toBeTrue();
    expect(service.isAuthenticated()).toBeTrue();
    expect(service.accessToken).toBe('tok');
  });

  it('401 invalid_credentials => credentials kind (anti-enumeration)', async () => {
    const promise = service.login({
      email: 'a@b.com.br',
      password: 'senhasegura1',
    });
    httpMock.expectOne('/v1/auth/login').flush(
      {
        error: {
          code: 'invalid_credentials',
          message: 'Credenciais inválidas.',
          request_id: 'req-1',
        },
      },
      { status: 401, statusText: 'Unauthorized' }
    );
    const res = await promise;
    expect(res.ok).toBeFalse();
    expect(res.kind).toBe('credentials');
    expect(service.isAuthenticated()).toBeFalse();
  });

  it('401 totp_required => totp_required kind', async () => {
    const promise = service.login({
      email: 'a@b.com.br',
      password: 'senhasegura1',
    });
    httpMock.expectOne('/v1/auth/login').flush(
      {
        error: {
          code: 'totp_required',
          message: 'Código TOTP obrigatório ou inválido.',
          request_id: 'req-2',
        },
      },
      { status: 401, statusText: 'Unauthorized' }
    );
    const res = await promise;
    expect(res.kind).toBe('totp_required');
  });

  it('status 0 => network kind', async () => {
    const promise = service.login({
      email: 'a@b.com.br',
      password: 'senhasegura1',
    });
    httpMock
      .expectOne('/v1/auth/login')
      .error(new ProgressEvent('error'), { status: 0, statusText: '' });
    const res = await promise;
    expect(res.kind).toBe('network');
  });

  it('5xx => server kind', async () => {
    const promise = service.login({
      email: 'a@b.com.br',
      password: 'senhasegura1',
    });
    httpMock.expectOne('/v1/auth/login').flush(
      { error: { code: 'internal_error', message: 'x', request_id: 'r' } },
      { status: 503, statusText: 'Service Unavailable' }
    );
    const res = await promise;
    expect(res.kind).toBe('server');
  });
});
