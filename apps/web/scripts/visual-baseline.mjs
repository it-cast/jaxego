#!/usr/bin/env node
/**
 * visual-baseline.mjs — capture the Phase 3 visual baseline + run axe a11y on
 * the key screens, in BOTH themes (UI-SPEC §9, REQ a11y_axe_required).
 *
 * Baseline-only (no comparison this phase). Outputs:
 *   apps/web/visual-baseline/{screen}-{theme}.png
 *   prints axe critical-violation count per screen (fails on any critical).
 *
 * Requires a running dev server (default http://localhost:4200) and Playwright:
 *   npm i -D playwright @axe-core/playwright
 *   npx playwright install chromium
 *   npm run start            # in another terminal (proxies /v1 -> :8000)
 *   node scripts/visual-baseline.mjs
 *
 * This script is intentionally not run in CI yet (no baseline comparison); it is
 * the live-verification harness for the orchestrator.
 */
import { mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const BASE = process.env.JX_BASE_URL ?? 'http://localhost:4200';
const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = resolve(__dirname, '..', 'visual-baseline');
mkdirSync(OUT_DIR, { recursive: true });

const screens = [
  { name: 'login', path: '/entrar', viewport: { width: 420, height: 900 } },
  { name: 'not-found', path: '/rota-inexistente', viewport: { width: 420, height: 900 } },
];
const themes = ['light', 'dark'];

async function main() {
  let chromium, AxeBuilder;
  try {
    ({ chromium } = await import('playwright'));
    ({ default: AxeBuilder } = await import('@axe-core/playwright'));
  } catch {
    console.error(
      'Missing deps. Run: npm i -D playwright @axe-core/playwright && npx playwright install chromium'
    );
    process.exit(2);
  }

  const browser = await chromium.launch();
  let criticalTotal = 0;

  for (const theme of themes) {
    const context = await browser.newContext();
    // Pre-seed the theme so the anti-FOUC script applies it before paint.
    await context.addInitScript((t) => {
      try {
        localStorage.setItem('jx-theme', t);
      } catch {
        /* ignore */
      }
    }, theme);

    for (const screen of screens) {
      const page = await context.newPage();
      await page.setViewportSize(screen.viewport);
      await page.goto(`${BASE}${screen.path}`, { waitUntil: 'networkidle' });

      // Confirm no theme flash: attribute must already match.
      const applied = await page.getAttribute('html', 'data-theme');
      if (applied !== theme) {
        console.warn(
          `[warn] ${screen.name}/${theme}: data-theme=${applied} (anti-FOUC mismatch?)`
        );
      }

      const file = resolve(OUT_DIR, `${screen.name}-${theme}.png`);
      await page.screenshot({ path: file, fullPage: true });

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();
      const critical = results.violations.filter(
        (v) => v.impact === 'critical'
      );
      criticalTotal += critical.length;
      console.log(
        `[axe] ${screen.name}/${theme}: ${critical.length} critical, ${results.violations.length} total -> ${file}`
      );
      for (const v of critical) {
        console.log(`   - ${v.id}: ${v.help}`);
      }
      await page.close();
    }
    await context.close();
  }

  await browser.close();
  if (criticalTotal > 0) {
    console.error(`FAIL: ${criticalTotal} critical a11y violation(s).`);
    process.exit(1);
  }
  console.log('OK: baseline captured, zero critical a11y violations.');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
