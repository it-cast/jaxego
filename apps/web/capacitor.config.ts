import type { CapacitorConfig } from '@capacitor/cli';

// Base Capacitor config. Native build (APK/iOS) is out of scope for Phase 3
// (handled in Phase 14). This only declares the web asset directory so the
// Capacitor tooling is wired and ready.
const config: CapacitorConfig = {
  appId: 'br.com.jaxego.app',
  appName: 'Jaxegô',
  // MR-5: o app mobile empacota o build SEPARADO do entregador.
  webDir: 'dist/entregador/browser',
};

export default config;
