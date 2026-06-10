/**
 * Visual-regression BASELINE for jx-data-table (UI-SPEC §10). Plain data (no
 * Storybook). Captured `jx-data-table-{state}-{theme}.png` light+dark.
 */

import type { DataTableColumn, DataTableState } from './data-table.component';

export const DATA_TABLE_COLUMNS: DataTableColumn[] = [
  { key: 'name', label: 'Nome' },
  { key: 'polygon', label: 'Polígono' },
  { key: 'actions', label: 'Ações', numeric: true },
];

const ROWS = [
  { name: 'Centro', polygon: 'defined' },
  { name: 'Aldeia', polygon: 'by_name' },
  { name: 'Vila do Pescador', polygon: 'by_name' },
];

export interface DataTableStory {
  state: string;
  inputs: {
    columns: DataTableColumn[];
    rows: unknown[];
    state: DataTableState;
    zebra?: boolean;
  };
}

export const dataTableStories: DataTableStory[] = [
  { state: 'ready', inputs: { columns: DATA_TABLE_COLUMNS, rows: ROWS, state: 'ready' } },
  {
    state: 'com-zebra',
    inputs: { columns: DATA_TABLE_COLUMNS, rows: ROWS, state: 'ready', zebra: true },
  },
  {
    state: 'ordenado',
    inputs: {
      columns: [{ key: 'name', label: 'Nome', sortable: true }, ...DATA_TABLE_COLUMNS.slice(1)],
      rows: ROWS,
      state: 'ready',
    },
  },
  { state: 'loading', inputs: { columns: DATA_TABLE_COLUMNS, rows: [], state: 'loading' } },
  { state: 'vazio', inputs: { columns: DATA_TABLE_COLUMNS, rows: [], state: 'empty' } },
  { state: 'erro', inputs: { columns: DATA_TABLE_COLUMNS, rows: [], state: 'error' } },
];
