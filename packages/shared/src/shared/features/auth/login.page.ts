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
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faEye, faEyeSlash, faEnvelope, faLock, faShieldHalved } from '@fortawesome/free-solid-svg-icons';
import { AuthService } from '@jaxego/core/auth/auth.service';
import {
  ErrorStateComponent,
  LoadingSkeletonComponent,
} from '@jaxego/shared/state';

@Component({
  selector: 'jx-login',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, RouterLink, ErrorStateComponent, LoadingSkeletonComponent, FaIconComponent],
  templateUrl: './login.page.html',
  styleUrl: './login.page.scss',
})
export class LoginPage implements AfterViewInit {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  protected readonly isApp = this.route.snapshot.data['surface'] === 'app';

  private readonly REMEMBER_KEY = 'jx-remember-email';

  protected readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required]],
    totp: [''],
    remember: [false],
  });

  protected readonly loading = signal(false);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly totpRequired = signal(false);
  protected readonly showPassword = signal(false);
  protected readonly faEye = faEye;
  protected readonly faEyeSlash = faEyeSlash;
  protected readonly faEnvelope = faEnvelope;
  protected readonly faLock = faLock;
  protected readonly faShield = faShieldHalved;

  private readonly errorRef =
    viewChild<ElementRef<HTMLElement>>('errorBlock');
  private readonly totpRef = viewChild<ElementRef<HTMLInputElement>>('totpInput');
  private readonly emailRef =
    viewChild<ElementRef<HTMLInputElement>>('emailInput');

  ngAfterViewInit(): void {
    const saved = localStorage.getItem(this.REMEMBER_KEY);
    if (saved) {
      this.form.controls.email.setValue(saved);
      this.form.controls.remember.setValue(true);
    }
    this.emailRef()?.nativeElement.focus();
  }

  protected togglePassword(): void {
    this.showPassword.update((v) => !v);
  }

  protected async submit(): Promise<void> {
    if (this.loading()) return; // no double submit
    this.errorMessage.set(null);

    // When TOTP is required, the code field becomes mandatory.
    if (this.totpRequired()) {
      this.form.controls.totp.addValidators(Validators.required);
      this.form.controls.totp.updateValueAndValidity();
    }

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    const { email, password, totp, remember } = this.form.getRawValue();
    if (remember) {
      localStorage.setItem(this.REMEMBER_KEY, email);
    } else {
      localStorage.removeItem(this.REMEMBER_KEY);
    }
    const result = await this.auth.login({
      email,
      password,
      totp: totp ? totp : undefined,
    });
    this.loading.set(false);

    if (result.ok) {
      // Roteamento por papel via /me (R0.4) — resolve TODAS as superfícies,
      // inclusive courier/merchant (que o claim `role` do JWT não distingue).
      const me = await this.auth.loadMe();
      if (!me || me.surface === 'none') {
        this.errorMessage.set(
          'Sua conta ainda não tem acesso a nenhuma área. Fale com o suporte.'
        );
        queueMicrotask(() => this.errorRef()?.nativeElement.focus());
        return;
      }
      if (me.surface === 'loja' && me.status === 'pending_payment') {
        void this.router.navigate(['/loja/aguardando-pagamento']);
        return;
      }
      void this.router.navigate([this.auth.surfaceHome(me.surface)]);
      return;
    }

    if (result.kind === 'totp_required') {
      this.totpRequired.set(true);
      // Reveal + focus the TOTP field after the view updates.
      queueMicrotask(() => this.totpRef()?.nativeElement.focus());
      this.errorMessage.set(null);
      return;
    }

    this.errorMessage.set(
      result.message ?? 'Não foi possível entrar agora. Tente de novo.'
    );
    // Move focus to the alert (error-ux-patterns / accessibility-pro).
    queueMicrotask(() => this.errorRef()?.nativeElement.focus());
  }
}
