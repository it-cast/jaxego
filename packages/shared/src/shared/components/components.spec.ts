import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DocCardComponent } from './doc-card/doc-card.component';
import { DocUploadComponent } from './doc-upload/doc-upload.component';
import { FieldComponent } from './field/field.component';
import { PlanCardComponent, type Plan } from './plan-card/plan-card.component';
import {
  WizardStepperComponent,
  type WizardStep,
} from './wizard-stepper/wizard-stepper.component';

const STEPS: WizardStep[] = [
  { label: 'Identificação' },
  { label: 'Confirmação' },
  { label: 'Endereço' },
  { label: 'Plano' },
];

describe('WizardStepperComponent', () => {
  let fixture: ComponentFixture<WizardStepperComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [WizardStepperComponent] });
    fixture = TestBed.createComponent(WizardStepperComponent);
    fixture.componentInstance.steps = STEPS;
    fixture.componentInstance.current = 1;
  });

  it('marks the current step with aria-current="step" (not colour alone)', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    const current = el.querySelector('[aria-current="step"]');
    expect(current).toBeTruthy();
    expect(current!.textContent).toContain('Confirmação');
  });

  it('announces the step in a polite live region', () => {
    fixture.detectChanges();
    const live = fixture.nativeElement.querySelector('[aria-live="polite"]');
    expect(live.textContent).toContain('Passo 2 de 4');
  });

  it('completed steps are buttons that emit goTo', () => {
    const spy = jasmine.createSpy('goTo');
    fixture.componentInstance.goTo.subscribe(spy);
    fixture.detectChanges();
    const backBtn: HTMLButtonElement | null =
      fixture.nativeElement.querySelector('button.jx-stepper__node');
    expect(backBtn).toBeTruthy();
    backBtn!.click();
    expect(spy).toHaveBeenCalledWith(0);
  });
});

describe('FieldComponent', () => {
  let fixture: ComponentFixture<FieldComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [FieldComponent] });
    fixture = TestBed.createComponent(FieldComponent);
    fixture.componentInstance.label = 'CNPJ';
  });

  it('associates the error with the input via aria-describedby', () => {
    fixture.componentInstance.error = 'CNPJ incompleto. Confira os 14 dígitos.';
    fixture.detectChanges();
    const input: HTMLInputElement = fixture.nativeElement.querySelector('input');
    const describedBy = input.getAttribute('aria-describedby');
    expect(describedBy).toBeTruthy();
    expect(input.getAttribute('aria-invalid')).toBe('true');
    const err = fixture.nativeElement.querySelector(`#${describedBy}`);
    expect(err.textContent).toContain('CNPJ incompleto');
  });

  it('applies mono styling when [mono]', () => {
    fixture.componentInstance.mono = true;
    fixture.detectChanges();
    const input: HTMLInputElement = fixture.nativeElement.querySelector('input');
    expect(input.classList).toContain('jx-field__input--mono');
  });
});

describe('PlanCardComponent', () => {
  let fixture: ComponentFixture<PlanCardComponent>;
  const freePlan: Plan = {
    id: 1,
    codename: 'free',
    nome: 'Free',
    preco_mensal_cents: 0,
    preco_anual_cents: 0,
    entregas_mes: 2,
    taxa_entrega_cents: 200,
    is_free: true,
    is_unlimited: false,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [PlanCardComponent] });
    fixture = TestBed.createComponent(PlanCardComponent);
    fixture.componentInstance.plan = freePlan;
  });

  it('renders SEED values, not hardcoded ones', () => {
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.textContent).toContain('R$ 0');
    expect(el.textContent).toContain('2 entregas/mês');
  });

  it('Free CTA carries the fill class (same weight as paid — anti-dark-pattern)', () => {
    fixture.detectChanges();
    const cta: HTMLButtonElement = fixture.nativeElement.querySelector('.jx-plan__cta');
    expect(cta.classList).toContain('jx-plan__cta--fill');
    expect(cta.textContent).toContain('Continuar no Free');
  });

  it('renders unlimited detail when is_unlimited', () => {
    fixture.componentInstance.plan = {
      ...freePlan,
      codename: 'sem_limite',
      nome: 'Sem Limite',
      is_free: false,
      is_unlimited: true,
      preco_mensal_cents: 29900,
      preco_anual_cents: 299000,
    };
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('ilimitado');
  });
});

describe('DocUploadComponent', () => {
  let fixture: ComponentFixture<DocUploadComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [DocUploadComponent] });
    fixture = TestBed.createComponent(DocUploadComponent);
    fixture.componentInstance.label = 'CNH';
  });

  it('announces upload progress in a live region (not colour alone)', () => {
    fixture.componentInstance.state = 'uploading';
    fixture.componentInstance.progress = 60;
    fixture.detectChanges();
    const live = fixture.nativeElement.querySelector('[aria-live="polite"]');
    expect(live.textContent).toContain('Enviando 60%');
    const bar = fixture.nativeElement.querySelector('[role="progressbar"]');
    expect(bar.getAttribute('aria-valuenow')).toBe('60');
  });

  it('shows an actionable error with role="alert" on failure', () => {
    fixture.componentInstance.state = 'error';
    fixture.componentInstance.error = 'Sem conexão. Tente de novo.';
    fixture.detectChanges();
    const alert = fixture.nativeElement.querySelector('[role="alert"]');
    expect(alert.textContent).toContain('Sem conexão');
    // The retry button is present (≥44px enforced by CSS).
    expect(fixture.nativeElement.textContent).toContain('Tentar de novo');
  });

  it('emits the picked file', () => {
    const spy = jasmine.createSpy('fileSelected');
    fixture.componentInstance.fileSelected.subscribe(spy);
    fixture.detectChanges();
    const input: HTMLInputElement =
      fixture.nativeElement.querySelector('input[type="file"]');
    const file = new File(['x'], 'cnh.jpg', { type: 'image/jpeg' });
    const dt = new DataTransfer();
    dt.items.add(file);
    input.files = dt.files;
    input.dispatchEvent(new Event('change'));
    expect(spy).toHaveBeenCalledWith(file);
  });
});

describe('DocCardComponent', () => {
  let fixture: ComponentFixture<DocCardComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [DocCardComponent] });
    fixture = TestBed.createComponent(DocCardComponent);
    fixture.componentInstance.title = 'CNH com EAR';
  });

  it('renders the status badge with text + icon (never colour alone)', () => {
    fixture.componentInstance.status = 'approved';
    fixture.detectChanges();
    const badge = fixture.nativeElement.querySelector('.jx-doc-card__badge');
    expect(badge.textContent).toContain('Aprovado');
    expect(badge.querySelector('[aria-hidden="true"]')).toBeTruthy(); // icon
  });

  it('E4: a rejected item shows the reason and a re-upload CTA (read mode)', () => {
    fixture.componentInstance.mode = 'read';
    fixture.componentInstance.status = 'rejected';
    fixture.componentInstance.rejectReason = 'Sem EAR na CNH.';
    fixture.detectChanges();
    const reject = fixture.nativeElement.querySelector('[role="alert"]');
    expect(reject.textContent).toContain('Sem EAR');
    expect(fixture.nativeElement.textContent).toContain('Reenviar CNH com EAR');
  });

  it('edit mode composes jx-doc-upload', () => {
    fixture.componentInstance.mode = 'edit';
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('jx-doc-upload')).toBeTruthy();
  });
});
