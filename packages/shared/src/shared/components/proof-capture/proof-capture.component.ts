import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
} from '@angular/core';
import {
  DocUploadComponent,
  DocUploadState,
} from '../doc-upload/doc-upload.component';
import {
  GeofencePillComponent,
  GeofenceState,
} from '../geofence-pill/geofence-pill.component';

/** The photo + its captured GPS (A3 contract: client {lat,lng} is the primary evidence). */
export interface ProofCapturePayload {
  file: File;
  lat: number | null;
  lng: number | null;
}

/**
 * jx-proof-capture — WRAPPER of jx-doc-upload + the geofence pill (NOT a fork).
 *
 * It reuses the governed jx-doc-upload for the camera/preview/progress and adds the
 * GPS capture (A3 contract: the client captures {lat,lng} at shutter time and sends
 * it with the photo; EXIF is server-side reinforcement). The geofence pill shows the
 * server verdict; the parent owns the actual upload + submit (the verdict drives the
 * CTA lock/unlock). Tokens only — no hex (Gate 2).
 */
@Component({
  selector: 'jx-proof-capture',
  standalone: true,
  imports: [DocUploadComponent, GeofencePillComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="jx-proof-capture">
      <jx-geofence-pill [state]="geofence" />
      <jx-doc-upload
        [label]="label"
        captureMode="environment"
        [state]="uploadState"
        [progress]="progress"
        [previewUrl]="previewUrl"
        [error]="error"
        (fileSelected)="onFile($event)"
        (open)="open.emit()"
      />
    </div>
  `,
  styleUrl: './proof-capture.component.scss',
})
export class ProofCaptureComponent {
  @Input() label = 'Foto da comprovação';
  @Input() geofence: GeofenceState = 'checking';
  @Input() uploadState: DocUploadState = 'idle';
  @Input() progress = 0;
  @Input() previewUrl: string | null = null;
  @Input() error: string | null = null;

  /** Emits the photo + the GPS captured at shutter time (A3 contract). */
  @Output() captured = new EventEmitter<ProofCapturePayload>();
  @Output() open = new EventEmitter<void>();

  protected onFile(file: File): void {
    // Capture GPS at shutter time (client evidence — server validates the geofence).
    if (typeof navigator !== 'undefined' && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) =>
          this.captured.emit({ file, lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => this.captured.emit({ file, lat: null, lng: null }),
        { enableHighAccuracy: true, timeout: 8000 },
      );
    } else {
      this.captured.emit({ file, lat: null, lng: null });
    }
  }
}
