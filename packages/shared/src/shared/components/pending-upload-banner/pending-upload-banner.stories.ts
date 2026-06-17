/**
 * Visual-regression BASELINE for jx-pending-upload-banner (UI-SPEC §12). Plain data.
 * Name: pending-upload-banner-{state}-{theme}.
 */

export interface PendingUploadBannerStory {
  state: string;
  inputs: { count: number; online: boolean };
}

export const pendingUploadBannerStories: PendingUploadBannerStory[] = [
  { state: 'offline-one', inputs: { count: 1, online: false } },
  { state: 'offline-many', inputs: { count: 3, online: false } },
  { state: 'uploading', inputs: { count: 2, online: true } },
];
