import type { CapacitorConfig } from '@capacitor/cli';

// Base Capacitor config. Native build (APK/iOS) is out of scope for Phase 3
// (handled in Phase 14). This only declares the web asset directory so the
// Capacitor tooling is wired and ready.
const config: CapacitorConfig = {
  appId: 'br.com.jaxego.app',
  appName: 'Jaxegô',
  // O app mobile empacota o build do entregador (apps/app).
  webDir: 'dist/app/browser',
};

export default config;
