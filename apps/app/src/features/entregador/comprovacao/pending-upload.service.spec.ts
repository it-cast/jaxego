import { TestBed } from '@angular/core/testing';
import { PendingUpload, PendingUploadService } from './pending-upload.service';

function item(deliveryId: number): PendingUpload {
  return {
    deliveryId,
    proofKind: 'pickup',
    file: new File([new Blob(['x'])], 'p.jpg', { type: 'image/jpeg' }),
    lat: -21.54,
    lng: -42.18,
  };
}

describe('PendingUploadService', () => {
  let service: PendingUploadService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(PendingUploadService);
  });

  it('queues photos and reports pending per delivery (not ENTREGUE until uploaded)', () => {
    service.enqueue(item(7));
    expect(service.count()).toBe(1);
    expect(service.hasPending(7)).toBe(true);
    expect(service.hasPending(99)).toBe(false);
  });

  it('drains only successful uploads, keeps failures queued', async () => {
    service.enqueue(item(7));
    service.enqueue(item(8));
    // Force online for the drain.
    (service as unknown as { _online: { set: (v: boolean) => void } })._online.set(true);

    let calls = 0;
    await service.drain(async (it) => {
      calls++;
      return it.deliveryId === 7; // 7 succeeds, 8 fails → stops, 8 stays queued
    });
    expect(calls).toBe(2);
    expect(service.hasPending(7)).toBe(false);
    expect(service.hasPending(8)).toBe(true);
  });

  it('does not drain while offline', async () => {
    service.enqueue(item(7));
    (service as unknown as { _online: { set: (v: boolean) => void } })._online.set(false);
    let called = false;
    await service.drain(async () => {
      called = true;
      return true;
    });
    expect(called).toBe(false);
    expect(service.count()).toBe(1);
  });
});
