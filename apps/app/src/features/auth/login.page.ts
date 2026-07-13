import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import {
  FormBuilder,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faEye, faEyeSlash } from '@fortawesome/free-solid-svg-icons';
import { AuthService } from '@jaxego/core/auth/auth.service';
import {
  ErrorStateComponent,
  LoadingSkeletonComponent,
} from '@jaxego/shared/state';

@Component({
  selector: 'jx-app-login',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, FormsModule, RouterLink, ErrorStateComponent, LoadingSkeletonComponent, FaIconComponent],
  templateUrl: './login.page.html',
  styleUrl: './login.page.scss',
})
export class AppLoginPage implements AfterViewInit {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required]],
    totp: [''],
  });

  protected rememberMe = false;

  protected readonly loading = signal(false);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly totpRequired = signal(false);
  protected readonly showPassword = signal(false);
  protected readonly faEye = faEye;
  protected readonly faEyeSlash = faEyeSlash;

  private readonly errorRef = viewChild<ElementRef<HTMLElement>>('errorBlock');
  private readonly totpRef = viewChild<ElementRef<HTMLInputElement>>('totpInput');
  private readonly emailRef = viewChild<ElementRef<HTMLInputElement>>('emailInput');

  constructor() {
    try {
      const saved = sessionStorage.getItem('jx-remember-login');
      if (saved) {
        const data = JSON.parse(saved);
        this.form.patchValue({ email: data.email ?? '', password: data.password ?? '' });
        this.rememberMe = true;
      }
    } catch { /* ignore */ }
  }

  ngAfterViewInit(): void {
    this.emailRef()?.nativeElement.focus();
  }

  protected togglePassword(): void {
    this.showPassword.update((v) => !v);
  }

  protected async submit(): Promise<void> {
    if (this.loading()) return;
    this.errorMessage.set(null);

    if (this.totpRequired()) {
      this.form.controls.totp.addValidators(Validators.required);
      this.form.controls.totp.updateValueAndValidity();
    }

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    const { email, password, totp } = this.form.getRawValue();
    const result = await this.auth.login(
      {
        email,
        password,
        totp: totp ? totp : undefined,
      },
      'entregador'
    );
    this.loading.set(false);

    if (result.ok) {
      try {
        if (this.rememberMe) {
          sessionStorage.setItem('jx-remember-login', JSON.stringify({ email, password }));
        } else {
          sessionStorage.removeItem('jx-remember-login');
        }
      } catch { /* ignore */ }
      const me = await this.auth.loadMe();
      if (!me || me.surface === 'none') {
        this.errorMessage.set(
          'Sua conta ainda nao tem acesso a nenhuma area. Fale com o suporte.'
        );
        queueMicrotask(() => this.errorRef()?.nativeElement.focus());
        return;
      }
      void this.router.navigate([this.auth.surfaceHome(me.surface)]);
      return;
    }

    if (result.kind === 'totp_required') {
      this.totpRequired.set(true);
      queueMicrotask(() => this.totpRef()?.nativeElement.focus());
      this.errorMessage.set(null);
      return;
    }

    this.errorMessage.set(
      result.message ?? 'Nao foi possivel entrar agora. Tente de novo.'
    );
    queueMicrotask(() => this.errorRef()?.nativeElement.focus());
  }
}
