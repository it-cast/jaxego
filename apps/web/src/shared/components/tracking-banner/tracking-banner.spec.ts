import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TrackingBannerComponent } from './tracking-banner.component';

describe('TrackingBannerComponent', () => {
  let fixture: ComponentFixture<TrackingBannerComponent>;
  let component: TrackingBannerComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TrackingBannerComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(TrackingBannerComponent);
    component = fixture.componentInstance;
  });

  function text(): string {
    return (fixture.nativeElement.textContent ?? '').trim();
  }

  it('shows the state headline + mono ETA while moving', () => {
    component.state = 'COLETADA';
    component.etaSeconds = 600;
    fixture.detectChanges();
    expect(text()).toContain('A caminho de você');
    expect(text()).toContain('10 min');
  });

  it('omits the ETA once delivered', () => {
    component.state = 'ENTREGUE';
    component.etaSeconds = 600;
    fixture.detectChanges();
    expect(text()).toContain('entregue');
    expect(text()).not.toContain('Chega em');
  });
});
