import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { AbstractControl, FormBuilder, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faEnvelope, faEye, faEyeSlash, faKey, faLock } from '@fortawesome/free-solid-svg-icons';
import { ApiErrorEnvelope, ResetProfile } from '@jaxego/core/auth/auth.models';
import { AuthService } from '@jaxego/core/auth/auth.service';
import { ErrorStateComponent } from '@jaxego/shared/state';
import { LoginBrandPanelComponent } from './login-brand-panel.component';

const SENHA_MIN = 10;

/** Login de cada perfil (para voltar depois de trocar a senha). */
const LOGIN_POR_PERFIL: Record<ResetProfile, string> = {
  loja: '/entrar',
  equipe: '/equipe/entrar',
  admin: '/admin/entrar',
  entregador: '/entrar',
};

function senhasIguais(group: AbstractControl): ValidationErrors | null {
  const nova = group.get('password')?.value;
  const conf = group.get('confirm')?.value;
  return nova && conf && nova !== conf ? { diferentes: true } : null;
}

/**
 * Esqueci minha senha (loja, equipe, admin da cidade e entregador).
 *
 * 1. a pessoa informa o e-mail e pede o código;
 * 2. digita o código e a nova senha;
 * 3. volta para o login com a senha nova.
 *
 * PROVISÓRIO: enquanto não há envio por e-mail, a API devolve o código e a tela mostra.
 * Quando o e-mail existir, a API para de devolver (`code: null`) e a tela só diz para
 * olhar a caixa de entrada — nada muda aqui.
 */
@Component({
  selector: 'jx-esqueci-senha',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, RouterLink, FaIconComponent, ErrorStateComponent, LoginBrandPanelComponent],
  templateUrl: './esqueci-senha.page.html',
  styleUrls: ['./login.page.scss', './esqueci-senha.page.scss'],
})
export class EsqueciSenhaPage implements AfterViewInit {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  protected readonly profile: ResetProfile =
    (this.route.snapshot.data['profile'] as ResetProfile | undefined) ?? 'loja';
  protected readonly loginPath = LOGIN_POR_PERFIL[this.profile];
  protected readonly badge = {
    loja: 'Loja',
    equipe: 'Equipe',
    admin: 'Admin',
    entregador: 'Entregador',
  }[this.profile];
  protected readonly senhaMin = SENHA_MIN;

  protected readonly etapa = signal<'email' | 'codigo' | 'pronto'>('email');
  protected readonly loading = signal(false);
  protected readonly erro = signal<string | null>(null);
  /** Código devolvido pela API (só enquanto não há e-mail). */
  protected readonly codigoNaTela = signal<string | null>(null);
  protected readonly aviso = signal('');
  protected readonly validadeMin = signal(15);
  protected readonly mostrarSenha = signal(false);

  protected readonly i = { email: faEnvelope, senha: faLock, codigo: faKey, olho: faEye, olhoFechado: faEyeSlash };

  protected readonly emailForm = this.fb.nonNullable.group({
    email: [this.route.snapshot.queryParamMap.get('email') ?? '', [Validators.required, Validators.email]],
  });

  protected readonly senhaForm = this.fb.nonNullable.group(
    {
      code: ['', [Validators.required, Validators.pattern(/^\d{6}$/)]],
      password: ['', [Validators.required, Validators.minLength(SENHA_MIN)]],
      confirm: ['', [Validators.required]],
    },
    { validators: senhasIguais }
  );

  private readonly erroRef = viewChild<ElementRef<HTMLElement>>('erroBloco');
  private readonly emailRef = viewChild<ElementRef<HTMLInputElement>>('emailInput');
  private readonly codigoRef = viewChild<ElementRef<HTMLInputElement>>('codigoInput');
  private readonly prontoRef = viewChild<ElementRef<HTMLElement>>('prontoTitulo');

  ngAfterViewInit(): void {
    this.emailRef()?.nativeElement.focus();
  }

  protected get email(): string {
    return this.emailForm.controls.email.value.trim();
  }

  protected async pedirCodigo(): Promise<void> {
    if (this.loading()) return;
    this.erro.set(null);
    if (this.emailForm.invalid) {
      this.emailForm.markAllAsTouched();
      return;
    }
    this.loading.set(true);
    try {
      const r = await this.auth.requestPasswordCode(this.profile, this.email);
      this.codigoNaTela.set(r.code);
      this.aviso.set(r.message);
      this.validadeMin.set(r.expires_in_minutes);
      this.senhaForm.reset();
      this.etapa.set('codigo');
      queueMicrotask(() => this.codigoRef()?.nativeElement.focus());
    } catch (e) {
      this.mostrarErro(e);
    } finally {
      this.loading.set(false);
    }
  }

  protected async salvar(): Promise<void> {
    if (this.loading()) return;
    this.erro.set(null);
    if (this.senhaForm.invalid) {
      this.senhaForm.markAllAsTouched();
      return;
    }
    const { code, password } = this.senhaForm.getRawValue();
    this.loading.set(true);
    try {
      await this.auth.resetPassword(this.profile, { email: this.email, code, new_password: password });
      this.etapa.set('pronto');
      queueMicrotask(() => this.prontoRef()?.nativeElement.focus());
    } catch (e) {
      this.mostrarErro(e);
    } finally {
      this.loading.set(false);
    }
  }

  protected trocarEmail(): void {
    this.erro.set(null);
    this.codigoNaTela.set(null);
    this.etapa.set('email');
    queueMicrotask(() => this.emailRef()?.nativeElement.focus());
  }

  protected irParaLogin(): void {
    void this.router.navigate([this.loginPath]);
  }

  protected invalido(form: 'email' | 'senha', campo: string): boolean {
    const grupo: AbstractControl = form === 'email' ? this.emailForm : this.senhaForm;
    const c = grupo.get(campo);
    return !!c && c.invalid && c.touched;
  }

  private mostrarErro(e: unknown): void {
    let msg = 'Não foi possível concluir agora. Tente de novo.';
    if (e instanceof HttpErrorResponse) {
      const envelope = e.error as ApiErrorEnvelope | undefined;
      if (e.status === 0) msg = 'Sem conexão com o servidor. Verifique sua internet e tente de novo.';
      else if (e.status === 422) msg = `Confira os dados. A senha precisa ter pelo menos ${SENHA_MIN} caracteres.`;
      else if (e.status >= 500) msg = 'Tivemos um problema aqui. Tente de novo em instantes.';
      else if (envelope?.error?.message) msg = envelope.error.message;
    }
    this.erro.set(msg);
    queueMicrotask(() => this.erroRef()?.nativeElement.focus());
  }
}
