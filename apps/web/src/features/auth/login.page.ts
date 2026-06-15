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
import { Router } from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faEye, faEyeSlash } from '@fortawesome/free-solid-svg-icons';
import { AuthService } from '../../core/auth/auth.service';
import {
  ErrorStateComponent,
  LoadingSkeletonComponent,
} from '../../shared/state';

@Component({
  selector: 'jx-login',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, ErrorStateComponent, LoadingSkeletonComponent, FaIconComponent],
  templateUrl: './login.page.html',
  styleUrl: './login.page.scss',
})
export class LoginPage implements AfterViewInit {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required]],
    totp: [''],
  });

  protected readonly loading = signal(false);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly totpRequired = signal(false);
  protected readonly showPassword = signal(false);
  protected readonly faEye = faEye;
  protected readonly faEyeSlash = faEyeSlash;

  private readonly errorRef =
    viewChild<ElementRef<HTMLElement>>('errorBlock');
  private readonly totpRef = viewChild<ElementRef<HTMLInputElement>>('totpInput');
  private readonly emailRef =
    viewChild<ElementRef<HTMLInputElement>>('emailInput');

  ngAfterViewInit(): void {
    // Initial focus on the e-mail field (UI-SPEC §5.3 idle state).
    this.emailRef()?.nativeElement.focus();
  }

  protected togglePassword(): void {
    this.showPassword.update((v) => !v);
  }

  protected async submit(): Promise<void> {
    console.log('[login] submit clicado — form válido:', this.form.valid, this.form.value);
    console.log('[login] erros email:', this.form.controls.email.errors);
    console.log('[login] erros password:', this.form.controls.password.errors);
    console.log('[login] erros totp:', this.form.controls.totp.errors);
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
    const { email, password, totp } = this.form.getRawValue();
    const result = await this.auth.login({
      email,
      password,
      totp: totp ? totp : undefined,
    });
    this.loading.set(false);
    console.log('[login] resultado da API:', result);

    if (result.ok) {
      const role = this.auth.role;
      console.log('[login] autenticado, role:', role);
      if (role === 'admin_plataforma') {
        void this.router.navigate(['/plataforma/visao-geral']);
      } else if (role?.startsWith('admin_area')) {
        void this.router.navigate(['/admin/inicio']);
      } else if (role === 'courier') {
        void this.router.navigate(['/entregador/inicio']);
      } else if (role === 'merchant') {
        void this.router.navigate(['/loja/painel']);
      } else {
        void this.router.navigate(['/entrar']);
      }
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
