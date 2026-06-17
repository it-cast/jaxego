import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Component } from '@angular/core';
import { EmptyStateComponent } from './empty-state.component';
import { ErrorStateComponent } from './error-state.component';
import { LoadingSkeletonComponent } from './loading-skeleton.component';
import { WarnBannerComponent } from './warn-banner.component';

describe('EmptyStateComponent', () => {
  let fixture: ComponentFixture<EmptyStateComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [EmptyStateComponent] });
    fixture = TestBed.createComponent(EmptyStateComponent);
    fixture.componentInstance.title = 'Nada por aqui ainda.';
    fixture.componentInstance.message = 'Crie a primeira no botão acima.';
  });

  it('renders title + message with role="status"', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('[role="status"]')).toBeTruthy();
    expect(el.textContent).toContain('Nada por aqui ainda.');
    expect(el.textContent).toContain('Crie a primeira no botão acima.');
  });

  it('emits cta only when ctaLabel is set', () => {
    fixture.componentInstance.ctaLabel = 'Criar agora';
    const spy = jasmine.createSpy('cta');
    fixture.componentInstance.cta.subscribe(spy);
    fixture.detectChanges();
    const btn: HTMLButtonElement | null =
      fixture.nativeElement.querySelector('button');
    expect(btn).toBeTruthy();
    btn!.click();
    expect(spy).toHaveBeenCalled();
  });
});

describe('ErrorStateComponent', () => {
  let fixture: ComponentFixture<ErrorStateComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [ErrorStateComponent] });
    fixture = TestBed.createComponent(ErrorStateComponent);
    fixture.componentInstance.message =
      'Não conseguimos carregar. Tente de novo.';
  });

  it('uses role="alert" and shows the message', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('[role="alert"]')).toBeTruthy();
    expect(el.textContent).toContain('Não conseguimos carregar.');
  });

  it('emits retry when retryLabel set and clicked', () => {
    fixture.componentInstance.retryLabel = 'Tentar de novo';
    const spy = jasmine.createSpy('retry');
    fixture.componentInstance.retry.subscribe(spy);
    fixture.detectChanges();
    const btn: HTMLButtonElement = fixture.nativeElement.querySelector('button');
    btn.click();
    expect(spy).toHaveBeenCalled();
  });
});

describe('LoadingSkeletonComponent', () => {
  it('is aria-hidden and applies the variant class', () => {
    TestBed.configureTestingModule({ imports: [LoadingSkeletonComponent] });
    const fixture = TestBed.createComponent(LoadingSkeletonComponent);
    fixture.componentInstance.variant = 'circle';
    fixture.detectChanges();
    const span: HTMLElement = fixture.nativeElement.querySelector('.jx-skeleton');
    expect(span.getAttribute('aria-hidden')).toBe('true');
    expect(span.classList).toContain('jx-skeleton--circle');
  });
});

describe('WarnBannerComponent', () => {
  let fixture: ComponentFixture<WarnBannerComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [WarnBannerComponent] });
    fixture = TestBed.createComponent(WarnBannerComponent);
    fixture.componentInstance.message = 'Conexão instável. Mostrando dados salvos.';
  });

  it('renders with role="status"', () => {
    fixture.detectChanges();
    expect(
      fixture.nativeElement.querySelector('[role="status"]')
    ).toBeTruthy();
  });

  it('dismiss button has aria-label and hides the banner on click', () => {
    fixture.componentInstance.dismissible = true;
    const spy = jasmine.createSpy('dismiss');
    fixture.componentInstance.dismiss.subscribe(spy);
    fixture.detectChanges();
    const btn: HTMLButtonElement = fixture.nativeElement.querySelector(
      '.jx-warn__dismiss'
    );
    expect(btn.getAttribute('aria-label')).toBe('Dispensar aviso');
    btn.click();
    fixture.detectChanges();
    expect(spy).toHaveBeenCalled();
    expect(fixture.nativeElement.querySelector('[role="status"]')).toBeNull();
  });
});

// Host harness sanity: components compose without runtime errors.
@Component({
  standalone: true,
  imports: [
    EmptyStateComponent,
    ErrorStateComponent,
    LoadingSkeletonComponent,
    WarnBannerComponent,
  ],
  template: `
    <jx-empty-state title="t" />
    <jx-error-state message="m" />
    <jx-loading-skeleton variant="line" />
    <jx-warn-banner message="w" />
  `,
})
class HostComponent {}

describe('state components composition', () => {
  it('all four mount together', () => {
    TestBed.configureTestingModule({ imports: [HostComponent] });
    const fixture = TestBed.createComponent(HostComponent);
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('jx-empty-state')).toBeTruthy();
    expect(el.querySelector('jx-error-state')).toBeTruthy();
    expect(el.querySelector('jx-loading-skeleton')).toBeTruthy();
    expect(el.querySelector('jx-warn-banner')).toBeTruthy();
  });
});
