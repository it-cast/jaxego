/** Visual-regression BASELINE for jx-pix-qr (UI-SPEC §14): aguardando, aprovado, expirado. */
import type { PixState } from './jx-pix-qr.component';

export interface PixQrStory {
  state: string;
  inputs: { copyPaste: string; image: string | null; pixState: PixState };
}

export const pixQrStories: PixQrStory[] = [
  { state: 'aguardando', inputs: { copyPaste: '00020101stub', image: null, pixState: 'aguardando' } },
  { state: 'aprovado', inputs: { copyPaste: '00020101stub', image: null, pixState: 'aprovado' } },
  { state: 'expirado', inputs: { copyPaste: '00020101stub', image: null, pixState: 'expirado' } },
];
