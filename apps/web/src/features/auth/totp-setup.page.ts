import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faCircleCheck } from '@fortawesome/free-solid-svg-icons';
import {
  ErrorStateComponent,
  LoadingSkeletonComponent,
} from '@jaxego/shared/state';

interface EnrollResponse {
  provisioning_uri: string;
  secret: string;
}

/**
 * Tela de enrollment TOTP (Correção #018).
 * Exibida quando admin_plataforma ainda não configurou o autenticador.
 * Fluxo: POST /v1/auth/totp/enroll → QR code → POST /v1/auth/totp/verify → plataforma.
 */
@Component({
  selector: 'jx-totp-setup',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, ErrorStateComponent, LoadingSkeletonComponent, FaIconComponent],
  templateUrl: './totp-setup.page.html',
  styleUrl: './totp-setup.page.scss',
})
export class TotpSetupPage implements AfterViewInit {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);

  protected readonly form = this.fb.nonNullable.group({
    code: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(6), Validators.pattern(/^\d{6}$/)]],
  });

  protected readonly loading = signal(true);
  protected readonly submitting = signal(false);
  protected readonly qrDataUrl = signal<string | null>(null);
  protected readonly secretKey = signal<string | null>(null);
  protected readonly loadError = signal<string | null>(null);
  protected readonly verifyError = signal<string | null>(null);
  protected readonly verified = signal(false);

  protected readonly faCircleCheck = faCircleCheck;

  private readonly codeRef = viewChild<ElementRef<HTMLInputElement>>('codeInput');
  private readonly errorRef = viewChild<ElementRef<HTMLElement>>('errorBlock');

  ngAfterViewInit(): void {
    void this.loadEnrollment();
  }

  private async loadEnrollment(): Promise<void> {
    this.loading.set(true);
    this.loadError.set(null);
    try {
      const res = await firstValueFrom(
        this.http.post<EnrollResponse>('/v1/auth/totp/enroll', {}),
      );
      // Format secret in groups of 4 for manual entry readability.
      this.secretKey.set(res.secret.toUpperCase().replace(/(.{4})/g, '$1 ').trim());
      // Generate QR code as data URL (white bg for all scan apps; no dark-mode inversion).
      const { toDataURL } = await import('qrcode');
      const dataUrl = await toDataURL(res.provisioning_uri, {
        width: 200,
        margin: 2,
        color: { dark: '#000000', light: '#ffffff' },
      });
      this.qrDataUrl.set(dataUrl);
      // Focus the code input after QR renders.
      queueMicrotask(() => this.codeRef()?.nativeElement.focus());
    } catch (err) {
      if (err instanceof HttpErrorResponse && err.status === 422) {
        // Already enrolled — safe to proceed to the platform.
        void this.router.navigate(['/plataforma/visao-geral']);
        return;
      }
      this.loadError.set('Não foi possível iniciar a configuração. Tente de novo.');
    } finally {
      this.loading.set(false);
    }
  }

  protected async verify(): Promise<void> {
    if (this.form.invalid || this.submitting()) {
      this.form.markAllAsTouched();
      return;
    }
    this.submitting.set(true);
    this.verifyError.set(null);
    try {
      await firstValueFrom(
        this.http.post('/v1/auth/totp/verify', { code: this.form.getRawValue().code }),
      );
      this.verified.set(true);
      setTimeout(() => void this.router.navigate(['/plataforma/visao-geral']), 1800);
    } catch (err) {
      if (err instanceof HttpErrorResponse && err.status === 401) {
        this.verifyError.set('Código inválido ou expirado. Verifique o app e tente de novo.');
      } else {
        this.verifyError.set('Algo deu errado. Tente de novo.');
      }
      this.form.controls.code.reset();
      queueMicrotask(() => {
        this.errorRef()?.nativeElement.focus();
        this.codeRef()?.nativeElement.focus();
      });
    } finally {
      this.submitting.set(false);
    }
  }

  protected retry(): void {
    this.loadError.set(null);
    void this.loadEnrollment();
  }
}
