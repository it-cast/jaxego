import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import {
  DataTableColumn,
  DataTableComponent,
} from './data-table.component';

@Component({
  standalone: true,
  imports: [DataTableComponent],
  template: `
    <jx-data-table
      [columns]="columns"
      [rows]="rows"
      [state]="state"
      [hasActions]="true"
      caption="Bairros"
    >
      <ng-template #row let-item>
        <td>{{ item.name }}</td>
        <td>{{ item.polygon }}</td>
        <td><button type="button">Remover</button></td>
      </ng-template>
    </jx-data-table>
  `,
})
class HostComponent {
  columns: DataTableColumn[] = [
    { key: 'name', label: 'Nome', sortable: true },
    { key: 'polygon', label: 'Polígono' },
  ];
  rows: { name: string; polygon: string }[] = [
    { name: 'Centro', polygon: 'defined' },
    { name: 'Aldeia', polygon: 'by_name' },
  ];
  state: 'loading' | 'empty' | 'error' | 'ready' = 'ready';
}

describe('DataTableComponent', () => {
  let fixture: ComponentFixture<HostComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HostComponent] });
    fixture = TestBed.createComponent(HostComponent);
    fixture.detectChanges();
  });

  function el(): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  it('renders a row per item when ready', () => {
    const bodyRows = el().querySelectorAll('tbody tr');
    expect(bodyRows.length).toBe(2);
    expect(el().textContent).toContain('Centro');
  });

  it('renders a real sort button with aria-sort on the sortable column', () => {
    const sortBtn = el().querySelector('.jx-data-table__sort') as HTMLButtonElement;
    expect(sortBtn).toBeTruthy();
    const th = sortBtn.closest('th') as HTMLElement;
    expect(th.getAttribute('aria-sort')).toBe('none');
    sortBtn.click();
    fixture.detectChanges();
    expect(th.getAttribute('aria-sort')).toBe('ascending');
    sortBtn.click();
    fixture.detectChanges();
    expect(th.getAttribute('aria-sort')).toBe('descending');
  });

  it('shows the empty state instead of a body when empty', () => {
    fixture.componentInstance.state = 'empty';
    fixture.detectChanges();
    expect(el().querySelector('tbody')).toBeNull();
    expect(el().querySelector('jx-empty-state')).toBeTruthy();
  });

  it('shows the error state with a retry when error', () => {
    fixture.componentInstance.state = 'error';
    fixture.detectChanges();
    expect(el().querySelector('jx-error-state')).toBeTruthy();
  });

  it('shows skeletons with aria-busy when loading', () => {
    fixture.componentInstance.state = 'loading';
    fixture.detectChanges();
    const busy = el().querySelector('[aria-busy="true"]');
    expect(busy).toBeTruthy();
  });
});
