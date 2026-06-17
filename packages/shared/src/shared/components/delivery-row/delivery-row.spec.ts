import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DeliveryRowComponent } from './delivery-row.component';
import type { DeliveryListItem } from '../../models/delivery.models';

function row(over: Partial<DeliveryListItem>): DeliveryListItem {
  return {
    id: 1,
    public_token: 'AB12CD34EF56',
    state: 'CRIADA',
    payment_method: 'direct',
    dropoff_neighborhood_id: 1,
    estimate_min_cents: 1000,
    estimate_max_cents: 1000,
    fee_cents: 150,
    reference_number: null,
    recipient_name: 'Maria Cliente',
    recipient_phone_masked: '+5522 9••••-7777',
    courier_id: null,
    created_at: '2026-06-10T14:30:00Z',
    ...over,
  };
}

@Component({
  standalone: true,
  imports: [DeliveryRowComponent],
  template: `<table>
    <tbody>
      <tr>
        <jx-delivery-row [delivery]="delivery"></jx-delivery-row>
      </tr>
    </tbody>
  </table>`,
})
class HostComponent {
  delivery: DeliveryListItem = row({});
}

describe('DeliveryRowComponent', () => {
  let fixture: ComponentFixture<HostComponent>;
  let host: HostComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [HostComponent] }).compileComponents();
    fixture = TestBed.createComponent(HostComponent);
    host = fixture.componentInstance;
  });

  it('shows the Cancelar action only in CRIADA', () => {
    host.delivery = row({ state: 'CRIADA' });
    fixture.detectChanges();
    let cancel = fixture.nativeElement.querySelector('.jx-delivery-row__cancel');
    expect(cancel).toBeTruthy();

    host.delivery = row({ state: 'ENTREGUE' });
    fixture.detectChanges();
    cancel = fixture.nativeElement.querySelector('.jx-delivery-row__cancel');
    expect(cancel).toBeNull();
  });

  it('never renders the raw recipient phone', () => {
    host.delivery = row({});
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).not.toContain('7777777');
  });

  it('shows — for missing freight', () => {
    host.delivery = row({ estimate_min_cents: null });
    fixture.detectChanges();
    const freight = fixture.nativeElement.querySelector('.jx-delivery-row__freight');
    expect(freight.textContent.trim()).toBe('—');
  });
});
