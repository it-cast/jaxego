#!/usr/bin/env node
// gsd-metrics-trigger.js
// gsd-hook-version: 0.8.0
//
// PostToolUse hook que dispara collect-metrics.sh quando SUMMARY.md
// de uma phase é escrito (sinal de fim-de-phase).
//
// PROBLEMA QUE RESOLVE:
// METRICS.md ficou vazio em 9 phases consecutivas (Rota Certa) porque
// collect-metrics.sh existe mas exige rodada manual que ninguém lembra.
// Resultado: tendências entre phases invisíveis, "plan revisions ≤ 2"
// sem histórico, dado de campo perdido.
//
// COMPORTAMENTO:
// - Acionado quando arquivo casando *-SUMMARY.md é escrito
// - Extrai phase_id do path (ex: phases/09-release-ci/09-01-SUMMARY.md → 09-release-ci)
// - Verifica se METRICS.md já tem entry para esse phase
// - Se não tem: dispara collect-metrics.sh com phase_id, cria rascunho
// - Se já tem: skip silencioso (não duplica)
//
// Advisory only. Falha do script não bloqueia (script ausente, etc).

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

let stdinBuffer = '';
const stdinTimeout = setTimeout(() => process.exit(0), 3000);

process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => { stdinBuffer += chunk; });
process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);
  try {
    main(stdinBuffer);
  } catch (e) {
    if (process.env.GSD_METRICS_TRIGGER_DEBUG === '1') {
      console.error('GSD metrics trigger error:', e.message);
    }
    process.exit(0);
  }
});

function main(input) {
  let payload;
  try { payload = JSON.parse(input); } catch { process.exit(0); }

  const toolName = payload?.tool_name || payload?.tool?.name || '';
  if (!/Edit|Write|MultiEdit/i.test(toolName)) process.exit(0);

  const filePath = payload?.tool_input?.file_path
    || payload?.tool_input?.path
    || '';

  if (!filePath || !/-SUMMARY\.md$/i.test(filePath)) process.exit(0);

  // Extrair phase_id do path
  // Pattern: .../phases/NN-name/NN-MM-SUMMARY.md ou .../phases/NN-name/NN-SUMMARY.md
  const phaseMatch = filePath.match(/phases[/\\]([^/\\]+)[/\\]/);
  if (!phaseMatch) process.exit(0);

  const phaseId = phaseMatch[1];

  // Verificar se METRICS.md existe
  const metricsFile = '.planning/METRICS.md';
  if (!fs.existsSync(metricsFile)) process.exit(0);

  // Já tem entry para essa phase?
  const metricsContent = fs.readFileSync(metricsFile, 'utf8');
  const phaseHeader = new RegExp(`^###\\s+${escapeRegex(phaseId)}\\s*$`, 'm');
  if (phaseHeader.test(metricsContent)) {
    // Já existe entry — skip silencioso
    process.exit(0);
  }

  // Localizar collect-metrics.sh
  const candidates = [
    'bin/collect-metrics.sh',
    './bin/collect-metrics.sh',
  ];

  let scriptPath = null;
  for (const c of candidates) {
    if (fs.existsSync(c)) {
      scriptPath = c;
      break;
    }
  }

  if (!scriptPath) {
    // Script ausente — só notifica, sem rodar nada
    console.log('');
    console.log('⚠️  GSD metrics: SUMMARY.md escrito mas bin/collect-metrics.sh não encontrado.');
    console.log('   Adicione collect-metrics.sh para auto-popular .planning/METRICS.md');
    console.log('');
    process.exit(0);
  }

  // Disparar collect-metrics.sh em background, sem bloquear
  const result = spawnSync('bash', [scriptPath, phaseId], {
    encoding: 'utf8',
    timeout: 10000,
  });

  // v0.9.5: também coletar telemetria DO FRAMEWORK (Gate 8, dispatcher, /gsd:go, skills novas)
  for (const ftPath of ['bin/collect-framework-telemetry.sh', './bin/collect-framework-telemetry.sh']) {
    if (fs.existsSync(ftPath)) {
      spawnSync('bash', [ftPath], { encoding: 'utf8', timeout: 10000 });
      break;
    }
  }

  if (result.status === 0) {
    console.log('');
    console.log('═══════════════════════════════════════════════════════════');
    console.log('  📊 GSD METRICS — Rascunho gerado');
    console.log('═══════════════════════════════════════════════════════════');
    console.log('');
    console.log(`  Phase: ${phaseId}`);
    console.log(`  Arquivo atualizado: .planning/METRICS.md`);
    console.log('');
    console.log('  AÇÃO RECOMENDADA antes de fechar a phase:');
    console.log('  1. Abra .planning/METRICS.md');
    console.log(`  2. Localize "### ${phaseId}"`);
    console.log('  3. Substitua os <FILL> com dados reais (3 qualitativos + scores 1-5)');
    console.log('  4. Commit junto com fechamento da phase');
    console.log('');
    console.log('  Sem isso, METRICS.md fica vazio e tendências entre phases');
    console.log('  ficam invisíveis (problema observado em 9 phases consecutivas');
    console.log('  no diagnóstico v0.7.x).');
    console.log('═══════════════════════════════════════════════════════════');
    console.log('');
  } else {
    if (process.env.GSD_METRICS_TRIGGER_DEBUG === '1') {
      console.error('collect-metrics.sh failed:', result.stderr);
    }
  }

  process.exit(0);
}

function escapeRegex(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
