import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { LoginPage } from './login.page';
import { AuthService, LoginResult } from '../../core/auth/auth.service';

class MockAuthService {
  result: LoginResult = { ok: true };
  lastReq: unknown;
  isAuthenticated = () => false;
  async login(req: unknown): Promise<LoginResult> {
    this.lastReq = req;
    return this.result;
  }
  // O fluxo de login resolve a superfície via /me e roteia por ela (R0.4).
  async loadMe() {
    return {
      user_id: 1,
      surface: 'loja' as const,
      area_id: 1,
      courier_id: null,
      merchant_id: 1,
      status: 'active',
    };
  }
  surfaceHome(): string {
    return '/loja';
  }
}

describe('LoginPage', () => {
  let fixture: ComponentFixture<LoginPage>;
  let page: LoginPage;
  let auth: MockAuthService;

  beforeEach(async () => {
    auth = new MockAuthService();
    await TestBed.configureTestingModule({
      imports: [LoginPage],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: auth },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(LoginPage);
    page = fixture.componentInstance;
    fixture.detectChanges();
  });

  function setForm(email: string, password: string): void {
    // @ts-expect-error access protected form in test
    page.form.setValue({ email, password, totp: '' });
  }

  it('idle: renders the form with the brand header and Entrar button', () => {
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('h1')?.textContent).toContain('rapidinho.');
    const btn = el.querySelector(
      '.jx-login__submit'
    ) as HTMLButtonElement;
    expect(btn.textContent?.trim()).toBe('Entrar');
    expect(btn.disabled).toBeFalse();
  });

  it('does not submit when the form is invalid', async () => {
    setForm('not-an-email', 'short');
    // @ts-expect-error protected
    await page.submit();
    expect(auth.lastReq).toBeUndefined();
  });

  it('error (anti-enumeration): shows credential message and an alert', async () => {
    auth.result = {
      ok: false,
      kind: 'credentials',
      message: 'E-mail ou senha incorretos. Tente de novo ou recupere a senha.',
    };
    setForm('user@exemplo.com.br', 'senhasegura1');
    // @ts-expect-error protected
    await page.submit();
    fixture.detectChanges();
    const alert = fixture.nativeElement.querySelector('[role="alert"]');
    expect(alert).toBeTruthy();
    expect(alert.textContent).toContain('E-mail ou senha incorretos');
  });

  it('totp_required: reveals the TOTP field', async () => {
    auth.result = { ok: false, kind: 'totp_required' };
    setForm('user@exemplo.com.br', 'senhasegura1');
    // @ts-expect-error protected
    await page.submit();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('#totp')).toBeTruthy();
    // sends totp on the next submit
    // @ts-expect-error protected
    page.form.controls.totp.setValue('123456');
    auth.result = { ok: true };
    // @ts-expect-error protected
    await page.submit();
    expect((auth.lastReq as { totp?: string }).totp).toBe('123456');
  });

  it('success: calls auth.login with the credentials', async () => {
    auth.result = { ok: true };
    setForm('user@exemplo.com.br', 'senhasegura1');
    // @ts-expect-error protected
    await page.submit();
    expect((auth.lastReq as { email: string }).email).toBe(
      'user@exemplo.com.br'
    );
  });
});
