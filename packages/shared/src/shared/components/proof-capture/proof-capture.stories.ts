/**
 * Visual-regression BASELINE for jx-proof-capture (UI-SPEC §12). Plain data.
 * Captures the wrapper across upload states × geofence verdicts × {light, dark}.
 * Name: proof-capture-{state}-{theme}.
 */

import type { DocUploadState } from '../doc-upload/doc-upload.component';
import type { GeofenceState } from '../geofence-pill/geofence-pill.component';

export interface ProofCaptureStory {
  state: string;
  inputs: {
    label: string;
    geofence: GeofenceState;
    uploadState: DocUploadState;
    previewUrl: string | null;
    error: string | null;
  };
}

export const proofCaptureStories: ProofCaptureStory[] = [
  {
    state: 'idle-checking',
    inputs: { label: 'Foto da coleta', geofence: 'checking', uploadState: 'idle', previewUrl: null, error: null },
  },
  {
    state: 'ok-success',
    inputs: { label: 'Foto da coleta', geofence: 'ok', uploadState: 'success', previewUrl: null, error: null },
  },
  {
    state: 'out-error',
    inputs: {
      label: 'Foto da coleta',
      geofence: 'out',
      uploadState: 'error',
      previewUrl: null,
      error: 'Não foi possível enviar a foto agora. Tente de novo.',
    },
  },
];
