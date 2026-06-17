import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { PublicTrackingPage } from './public-tracking.page';
import { PublicTrackingService } from './public-tracking.service';

describe('PublicTrackingPage', () => {
  let serviceSpy: jasmine.SpyObj<PublicTrackingService>;
  let fixture: ComponentFixture<PublicTrackingPage> | null = null;

  async function setup(token: string): Promise<ComponentFixture<PublicTrackingPage>> {
    await TestBed.configureTestingModule({
      imports: [PublicTrackingPage],
      providers: [
        { provide: PublicTrackingService, useValue: serviceSpy },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap({ token }) } },
        },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(PublicTrackingPage);
    fixture.detectChanges(); // ngOnInit fires load()
    // Let the resolved service promise settle (avoid whenStable — the page sets a
    // 60s refresh interval that would keep the zone unstable forever).
    await Promise.resolve();
    await Promise.resolve();
    fixture.detectChanges();
    return fixture;
  }

  beforeEach(() => {
    serviceSpy = jasmine.createSpyObj('PublicTrackingService', ['get']);
  });

  afterEach(() => {
    fixture?.destroy(); // clears the refresh interval
    fixture = null;
    TestBed.resetTestingModule();
  });

  it('shows the generic error state on an invalid token (anti-enumeração)', async () => {
    serviceSpy.get.and.resolveTo({ ok: false, notFound: true });
    const f = await setup('BADTOKEN');
    const text = (f.nativeElement.textContent ?? '').toLowerCase();
    expect(text).toContain('expirado');
    expect(text).not.toContain('existe'); // never reveals existence
  });

  it('renders the timeline + banner for a valid token', async () => {
    serviceSpy.get.and.resolveTo({
      ok: true,
      data: {
        state: 'COLETADA',
        timeline: [
          { state: 'CRIADA', at: '2026-06-10T10:00:00Z' },
          { state: 'COLETADA', at: '2026-06-10T10:20:00Z' },
        ],
        eta_seconds: 600,
        dropoff: { neighborhood_id: 1, address: 'Rua X' },
        courier: { vehicle_type: 'moto' },
        courier_position: null, // no position → map not shown (LCP = timeline)
      },
    });
    const f = await setup('GOODTOKEN');
    const text = (f.nativeElement.textContent ?? '').toLowerCase();
    expect(text).toContain('a caminho');
    expect(f.nativeElement.querySelector('jx-tracking-timeline')).toBeTruthy();
    // No courier_position → the lazy map is not mounted (LCP = timeline).
    expect(f.nativeElement.querySelector('jx-live-map')).toBeFalsy();
  });
});
