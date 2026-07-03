import { Injectable, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { OfferService } from './offer.service';
import type { OfferOut, OfferResult } from './offer.models';

/**
 * OfferMonitorService — singleton que controla o loop de polling de ofertas.
 * Vive acima das páginas individuais (injetado no EntregadorShellComponent)
 * para que o entregador receba a oferta em qualquer tela do app, não apenas
 * na tela de início.
 *
 * Fluxo: startMonitoring() → poll a cada 4s → offer() preenchido → shell
 * exibe o modal. Accept/decline resetam o estado e navegam quando necessário.
 */
@Injectable({ providedIn: 'root' })
export class OfferMonitorService {
  private readonly offerSvc = inject(OfferService);
  private readonly router = inject(Router);

  readonly offer = signal<OfferOut | null>(null);
  readonly offerResult = signal<OfferResult | null>(null);
  readonly processing = signal(false);

  private pollHandle: ReturnType<typeof setInterval> | null = null;
  private readonly sound = new Audio('notificacao.mp3');

  startMonitoring(): void {
    if (this.pollHandle !== null) return; // já está rodando
    this.pollHandle = setInterval(() => void this.poll(), 4000);
  }

  stopMonitoring(): void {
    if (this.pollHandle !== null) {
      clearInterval(this.pollHandle);
      this.pollHandle = null;
    }
    this.offer.set(null);
    this.offerResult.set(null);
    this.processing.set(false);
  }

  private async poll(): Promise<void> {
    if (this.processing()) return;
    try {
      const next = await this.offerSvc.active();
      if (next && !this.offer()) {
        // Nova oferta chegou — toca som e garante resultado limpo.
        this.offerResult.set(null);
        this.sound.play().catch(() => {});
      }
      if (!next && this.offer() && !this.processing()) {
        // Oferta sumiu sem resultado → expirou no servidor.
        this.offer.set(null);
        this.offerResult.set(null);
      }
      if (next) this.offer.set(next);
    } catch {
      // 401 é relançado pelo OfferService; interceptor renova o token.
    }
  }

  async accept(deliveryId: number): Promise<void> {
    this.processing.set(true);
    const result = await this.offerSvc.accept(deliveryId);
    this.processing.set(false);
    if (result === 'won') {
      this.offer.set(null);
      this.offerResult.set(null);
      void this.router.navigate(['/entregador/entrega-ativa']);
      return;
    }
    this.offerResult.set(result);
    setTimeout(() => {
      this.offer.set(null);
      this.offerResult.set(null);
    }, result === 'lost' ? 5000 : 2000);
  }

  async decline(deliveryId: number): Promise<void> {
    await this.offerSvc.decline(deliveryId);
    this.offer.set(null);
    this.offerResult.set(null);
  }
}
