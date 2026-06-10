# Skill: file-upload-ux

> Upload de arquivos e imagens em Ionic 8 + Capacitor (mobile) e Angular Material 19 (admin): câmera, galeria, picker, preview, progress, compressão, validação, error handling.
> Categoria: `ux-advanced` · 2026-04-18

## Propósito

Padronizar upload de arquivos no {PROJETO} (portfólio do profissional, fotos de orçamento, avatar, fotos de entrega, anexos de chat). Garante UX consistente (preview antes de enviar, progress real, mensagens claras) e evita os bugs mais comuns (crash em cancel, payload gigante sem compressão, tipo não validado).

## Quando usar (triggers)

- Qualquer tela com upload de imagem/arquivo
- Uso de `@capacitor/camera` no mobile
- `<input type="file">` ou drag-drop no admin
- Endpoint que recebe `multipart/form-data`
- Correção do bug `upload.service.ts` crash no cancel

## Quando NÃO usar

- Upload de dados texto (JSON) → não é upload de arquivo
- Geração de arquivo pelo backend para download → outra coisa

---

## Padrão mobile (Capacitor Camera)

### O bug que o {PROJETO} tem hoje

O arquivo `upload.service.ts` crasheia com **non-null assertion** quando o usuário cancela a câmera. Padrão errado:

```typescript
// ❌ ERRADO — crash no cancel
async pickPhoto() {
  const photo = await Camera.getPhoto({ resultType: CameraResultType.Uri });
  return photo.webPath!;  // 💥 webPath é undefined se cancelou
}
```

### Padrão correto (com tratamento de cancel)

```typescript
// apps/mobile/src/app/core/services/upload.service.ts
import { Camera, CameraResultType, CameraSource, Photo } from '@capacitor/camera';

export type UploadResult =
  | { status: 'ok'; file: File; preview: string }
  | { status: 'cancelled' }
  | { status: 'error'; message: string };

@Injectable({ providedIn: 'root' })
export class UploadService {

  async pickFromCamera(): Promise<UploadResult> {
    try {
      const photo: Photo = await Camera.getPhoto({
        quality: 80,
        allowEditing: false,
        resultType: CameraResultType.DataUrl,  // preview nativo
        source: CameraSource.Camera,
        promptLabelCancel: 'Cancelar',
        promptLabelHeader: 'Foto do serviço',
      });

      // webPath e dataUrl PODEM ser undefined se o usuário cancelou
      if (!photo.dataUrl) {
        return { status: 'cancelled' };
      }

      const blob = await this.dataUrlToBlob(photo.dataUrl);
      const file = new File([blob], `foto-${Date.now()}.jpg`, { type: 'image/jpeg' });

      // Comprimir antes de subir
      const compressed = await this.compress(file, { maxSizeKB: 500, maxWidthPx: 1920 });

      return {
        status: 'ok',
        file: compressed,
        preview: photo.dataUrl,
      };
    } catch (error: any) {
      // Capacitor lança erro específico quando usuário cancela no Android
      if (error?.message?.includes('cancel') || error?.code === 'USER_CANCELLED') {
        return { status: 'cancelled' };
      }
      console.error('Camera error:', error);
      return {
        status: 'error',
        message: 'Não conseguimos acessar a câmera. Verifique as permissões.',
      };
    }
  }

  async pickFromGallery(): Promise<UploadResult> {
    try {
      const photo = await Camera.getPhoto({
        quality: 85,
        resultType: CameraResultType.DataUrl,
        source: CameraSource.Photos,
      });
      if (!photo.dataUrl) return { status: 'cancelled' };

      const blob = await this.dataUrlToBlob(photo.dataUrl);
      const file = new File([blob], `img-${Date.now()}.jpg`, { type: 'image/jpeg' });
      const compressed = await this.compress(file, { maxSizeKB: 500, maxWidthPx: 1920 });
      return { status: 'ok', file: compressed, preview: photo.dataUrl };
    } catch (error: any) {
      if (error?.message?.includes('cancel')) return { status: 'cancelled' };
      return { status: 'error', message: 'Não foi possível abrir a galeria.' };
    }
  }

  private async dataUrlToBlob(dataUrl: string): Promise<Blob> {
    const res = await fetch(dataUrl);
    return await res.blob();
  }

  private async compress(
    file: File,
    opts: { maxSizeKB: number; maxWidthPx: number },
  ): Promise<File> {
    // Implementação com canvas (ver skill completa)
    // ...
  }
}
```

### Uso no componente

```typescript
async onAddPhoto() {
  const action = await this.actionSheet.create({
    header: 'Adicionar foto',
    buttons: [
      { text: 'Tirar foto', handler: () => this.capture('camera') },
      { text: 'Escolher da galeria', handler: () => this.capture('gallery') },
      { text: 'Cancelar', role: 'cancel' },
    ],
  });
  await action.present();
}

async capture(source: 'camera' | 'gallery') {
  const result = source === 'camera'
    ? await this.uploadService.pickFromCamera()
    : await this.uploadService.pickFromGallery();

  switch (result.status) {
    case 'ok':
      this.photos.update(list => [...list, result]);
      break;
    case 'cancelled':
      // silêncio, normal
      break;
    case 'error':
      this.toast.showError(result.message);
      break;
  }
}
```

---

## Compressão client-side (obrigatória)

Imagens de câmera modernas têm 3-10 MB. **Backend do {PROJETO} aceita até 5 MB, mas ideal é enviar ~500 KB.**

```typescript
async compress(file: File, opts: { maxSizeKB: number; maxWidthPx: number }): Promise<File> {
  const img = await this.loadImage(file);

  // Redimensionar se maior que o máximo
  const scale = Math.min(1, opts.maxWidthPx / img.width);
  const width = Math.round(img.width * scale);
  const height = Math.round(img.height * scale);

  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  canvas.getContext('2d')!.drawImage(img, 0, 0, width, height);

  // Tentar qualidades decrescentes até ficar abaixo do tamanho
  for (const quality of [0.9, 0.8, 0.7, 0.6, 0.5]) {
    const blob = await this.canvasToBlob(canvas, quality);
    if (blob.size <= opts.maxSizeKB * 1024) {
      return new File([blob], file.name, { type: 'image/jpeg' });
    }
  }

  // Fallback: qualidade mínima aceitável
  const blob = await this.canvasToBlob(canvas, 0.4);
  return new File([blob], file.name, { type: 'image/jpeg' });
}

private loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = URL.createObjectURL(file);
  });
}

private canvasToBlob(canvas: HTMLCanvasElement, quality: number): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(b => b ? resolve(b) : reject(new Error('toBlob null')), 'image/jpeg', quality);
  });
}
```

---

## Padrão admin (drag-drop + file input)

```typescript
// apps/admin/src/app/shared/upload-drop.component.ts
import { Component, output, signal, HostBinding, HostListener } from '@angular/core';

@Component({
  selector: 'app-upload-drop',
  standalone: true,
  template: `
    <div class="dropzone" [class.dragging]="isDragging()">
      <input
        #fileInput
        type="file"
        [accept]="accept"
        [multiple]="multiple"
        (change)="onSelect($event)"
        hidden
      />
      @if (progress() !== null) {
        <mat-progress-bar [value]="progress()" />
        <span>{{ progress() }}%</span>
      } @else {
        <mat-icon>cloud_upload</mat-icon>
        <p>Arraste arquivos aqui ou <a (click)="fileInput.click()">clique para selecionar</a></p>
        <small>Máximo {{ maxSizeMB }}MB · {{ acceptLabel }}</small>
      }
    </div>
  `,
})
export class UploadDropComponent {
  accept = 'image/jpeg,image/png,image/webp';
  acceptLabel = 'JPG, PNG, WEBP';
  maxSizeMB = 5;
  multiple = true;

  isDragging = signal(false);
  progress = signal<number | null>(null);

  fileSelected = output<File[]>();

  @HostListener('dragover', ['$event']) onDragOver(e: DragEvent) {
    e.preventDefault();
    this.isDragging.set(true);
  }
  @HostListener('dragleave') onDragLeave() { this.isDragging.set(false); }
  @HostListener('drop', ['$event']) onDrop(e: DragEvent) {
    e.preventDefault();
    this.isDragging.set(false);
    const files = Array.from(e.dataTransfer?.files ?? []);
    this.process(files);
  }

  onSelect(e: Event) {
    const input = e.target as HTMLInputElement;
    const files = Array.from(input.files ?? []);
    this.process(files);
    input.value = '';  // reset para permitir selecionar o mesmo arquivo de novo
  }

  private process(files: File[]) {
    const valid = files.filter(f => this.validate(f));
    if (valid.length) this.fileSelected.emit(valid);
  }

  private validate(file: File): boolean {
    if (!this.accept.split(',').includes(file.type)) {
      this.snackbar.open(`${file.name}: tipo não permitido`, 'OK');
      return false;
    }
    if (file.size > this.maxSizeMB * 1024 * 1024) {
      this.snackbar.open(`${file.name}: acima de ${this.maxSizeMB}MB`, 'OK');
      return false;
    }
    return true;
  }
}
```

---

## Progress real com HttpClient

```typescript
uploadWithProgress(file: File, url: string): Observable<number | string> {
  const form = new FormData();
  form.append('file', file);

  return this.http.post(url, form, {
    reportProgress: true,
    observe: 'events',
  }).pipe(
    map(event => {
      if (event.type === HttpEventType.UploadProgress) {
        return event.total ? Math.round(100 * event.loaded / event.total) : 0;
      }
      if (event.type === HttpEventType.Response) {
        return (event.body as { url: string }).url;
      }
      return 0;
    }),
  );
}
```

---

## Anti-patterns

1. ❌ **Non-null assertion em `photo.webPath!`** — crash em cancel (bug atual do {PROJETO})
2. ❌ **Upload sem compressão** — 5 MB foto subindo via 4G = segundos de espera + custo Backblaze
3. ❌ **Upload sem progress** — usuário acha que travou, clica 3 vezes, cria 3 uploads
4. ❌ **Validar tipo só pelo `.extension`** — use `file.type` (MIME) também; arquivo pode estar renomeado
5. ❌ **`accept="image/*"` sem restrição** — aceita HEIC/TIFF/RAW que backend não processa
6. ❌ **Permitir upload sem preview** — usuário sobe foto errada e só descobre depois
7. ❌ **Input file sem `input.value = ''` após** — impossível selecionar o mesmo arquivo 2x
8. ❌ **Enviar File bruto como JSON base64** — use `multipart/form-data` + `FormData`
9. ❌ **Esperar upload completo antes de mostrar UI** — usuário vê tela congelada; mostre o preview local imediatamente e só substitua quando upload terminar
10. ❌ **Não tratar 413 Payload Too Large** — mostre mensagem amigável, não erro cru

---

## Permissões Capacitor (Android/iOS)

### `android/app/src/main/AndroidManifest.xml`

```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32" />
<uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />
```

### `ios/App/App/Info.plist`

```xml
<key>NSCameraUsageDescription</key>
<string>Para tirar fotos do seu portfólio e serviços</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>Para selecionar fotos do seu portfólio e serviços</string>
```

---

## Checklist de review

- [ ] Tratamento de cancel retorna sentinel `{ status: 'cancelled' }`, não lança exception
- [ ] Nenhum `!` non-null assertion em campos do Photo/File
- [ ] Compressão client-side para ~500 KB antes de enviar
- [ ] Validação de tipo via MIME + validação de tamanho
- [ ] Preview local imediato (antes do upload completar)
- [ ] Progress real (não fake spinner)
- [ ] Input file com `input.value = ''` no final
- [ ] Action sheet oferece câmera + galeria
- [ ] Permissões declaradas em AndroidManifest + Info.plist
- [ ] Error handling com mensagem amigável em ptBR
- [ ] Backend valida tipo e tamanho de novo (defense in depth)

<!-- Skill aplicada: qualquer tela com upload, principalmente portfolio, new-quote, chat, avatar, delivery photos -->
