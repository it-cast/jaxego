#!/usr/bin/env node
/**
 * build-tokens.mjs — generate the PRIMITIVE token layer (--jx-*) from the
 * canonical design tokens (docs/identidade-visual/tokens.json) into
 * src/styles/_tokens.scss.
 *
 * Rules (ux-advanced/design-tokens-system + senior-quality-bar):
 *  - This file is the ONLY place where raw hex/values from tokens.json appear.
 *  - Output is deterministic / idempotent: re-running yields a byte-identical
 *    file (git diff empty).
 *  - The semantic layer (_semantic.scss) consumes ONLY these primitives,
 *    never a literal hex.
 *
 * Naming: nested keys are flattened with `-`. Examples:
 *   color.brand.500       -> --jx-brand-500
 *   color.neutral.50      -> --jx-neutral-50
 *   color.semantic.error  -> --jx-error
 *   spacing.4             -> --jx-space-4
 *   radius.lg             -> --jx-radius-lg
 *   font.family.display   -> --jx-font-display
 *   font.size.base        -> --jx-text-base
 *   font.weight.semibold  -> --jx-weight-semibold
 *   shadow.md             -> --jx-shadow-md
 *   motion.normal         -> --jx-motion-normal
 */

import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, '..', '..', '..');
const TOKENS_PATH = resolve(REPO_ROOT, 'docs/identidade-visual/tokens.json');
const OUT_PATH = resolve(__dirname, '..', 'src/styles/_tokens.scss');

const tokens = JSON.parse(readFileSync(TOKENS_PATH, 'utf8'));

/** @type {Array<[string, string]>} pairs of [cssVarName, value] */
const vars = [];

function pushColor(group, prefix) {
  if (!group) return;
  for (const [key, value] of Object.entries(group)) {
    vars.push([`--jx-${prefix}${key}`, value]);
  }
}

// --- Colors ---------------------------------------------------------------
pushColor(tokens.color?.brand, 'brand-');
pushColor(tokens.color?.neutral, 'neutral-');
// semantic colors flattened without the `semantic-` prefix (error, error_bg -> error-bg)
if (tokens.color?.semantic) {
  for (const [key, value] of Object.entries(tokens.color.semantic)) {
    vars.push([`--jx-${key.replace(/_/g, '-')}`, value]);
  }
}
// delivery_state and score_level kept namespaced (used by later phases)
if (tokens.color?.delivery_state) {
  for (const [key, value] of Object.entries(tokens.color.delivery_state)) {
    vars.push([`--jx-delivery-${key.replace(/_/g, '-')}`, value]);
  }
}
if (tokens.color?.score_level) {
  for (const [key, value] of Object.entries(tokens.color.score_level)) {
    vars.push([`--jx-score-${key}`, value]);
  }
}

// --- Spacing --------------------------------------------------------------
if (tokens.spacing) {
  for (const [key, value] of Object.entries(tokens.spacing)) {
    vars.push([`--jx-space-${key}`, value]);
  }
}

// --- Radius ---------------------------------------------------------------
if (tokens.radius) {
  for (const [key, value] of Object.entries(tokens.radius)) {
    vars.push([`--jx-radius-${key}`, value]);
  }
}

// --- Typography -----------------------------------------------------------
if (tokens.font?.family) {
  for (const [key, value] of Object.entries(tokens.font.family)) {
    // serif_accent -> font-serif-accent
    vars.push([`--jx-font-${key.replace(/_/g, '-')}`, value]);
  }
}
if (tokens.font?.size) {
  for (const [key, value] of Object.entries(tokens.font.size)) {
    vars.push([`--jx-text-${key}`, value]);
  }
}
if (tokens.font?.weight) {
  for (const [key, value] of Object.entries(tokens.font.weight)) {
    vars.push([`--jx-weight-${key}`, value]);
  }
}

// --- Shadow ---------------------------------------------------------------
if (tokens.shadow) {
  for (const [key, value] of Object.entries(tokens.shadow)) {
    vars.push([`--jx-shadow-${key}`, value]);
  }
}

// --- Motion ---------------------------------------------------------------
if (tokens.motion) {
  for (const [key, value] of Object.entries(tokens.motion)) {
    // easing_out -> motion-easing-out
    vars.push([`--jx-motion-${key.replace(/_/g, '-')}`, value]);
  }
}

// --- Emit -----------------------------------------------------------------
const header = `// ============================================================================
// GENERATED FILE — DO NOT EDIT BY HAND.
// Source: docs/identidade-visual/tokens.json
// Regenerate: npm run tokens:build  (apps/web)
// Primitive token layer (--jx-*). Components must consume the SEMANTIC layer
// (_semantic.scss), never these primitives or a literal hex.
// tokens.json version: ${tokens._meta?.version ?? 'unknown'}
// ============================================================================
`;

const body = vars.map(([name, value]) => `  ${name}: ${value};`).join('\n');

const out = `${header}\n:root {\n${body}\n}\n`;

writeFileSync(OUT_PATH, out, 'utf8');
console.log(
  `[build-tokens] wrote ${vars.length} primitive vars -> ${OUT_PATH.replace(REPO_ROOT, '.')}`
);
