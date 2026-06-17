import { TestBed } from '@angular/core/testing';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import {
  LocationPollingService,
  haversineMeters,
} from './location-polling.service';

describe('LocationPollingService', () => {
  let service: LocationPollingService;
  let httpMock: HttpTestingController;
  let onlineSpy: jasmine.Spy;

  function setOnline(value: boolean): void {
    onlineSpy.and.returnValue(value);
  }

  function stubGeolocation(coords: { latitude: number; longitude: number }[]): void {
    let call = 0;
    spyOn(navigator.geolocation, 'getCurrentPosition').and.callFake(
      (ok: PositionCallback) => {
        ok({ coords: coords[Math.min(call++, coords.length - 1)] } as GeolocationPosition);
      },
    );
  }

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(LocationPollingService);
    httpMock = TestBed.inject(HttpTestingController);
    onlineSpy = spyOnProperty(navigator, 'onLine', 'get').and.returnValue(true);
  });

  afterEach(() => {
    service.stop();
  });

  it('haversine returns metres (close points stay close)', () => {
    const d = haversineMeters(-21.54, -42.18, -21.5405, -42.18);
    expect(d).toBeGreaterThan(40);
    expect(d).toBeLessThan(70);
  });

  it('posts a sample and applies the 50m movement filter', async () => {
    stubGeolocation([
      { latitude: -21.54, longitude: -42.18 },
      { latitude: -21.5402, longitude: -42.18 }, // ~22m → filtered
    ]);
    (service as unknown as { deliveryId: number }).deliveryId = 7;

    // Kick the tick; let the geolocation microtask resolve, then flush the POST.
    const first = service.tick();
    await Promise.resolve();
    await Promise.resolve();
    httpMock.expectOne('/v1/deliveries/7/locations').flush({});
    await first;

    // Second tick: <50m from the last SENT position → no request.
    await service.tick();
    httpMock.expectNone('/v1/deliveries/7/locations');
  });

  it('does not run while offline (online gate)', () => {
    setOnline(false);
    stubGeolocation([{ latitude: -21.54, longitude: -42.18 }]);
    service.start(7);
    expect(service.running).toBe(false);
    service.stop();
    httpMock.verify();
  });

  it('runs when visible and online', async () => {
    setOnline(true);
    stubGeolocation([{ latitude: -21.54, longitude: -42.18 }]);
    service.start(7);
    expect(service.running).toBe(true);
    // start() fires an immediate tick; let it resolve, then flush.
    await Promise.resolve();
    await Promise.resolve();
    httpMock.expectOne('/v1/deliveries/7/locations').flush({});
  });
});
