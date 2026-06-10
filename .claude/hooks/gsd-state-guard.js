#!/usr/bin/env node
// gsd-state-guard.js
// gsd-hook-version: 0.8.0
//
// PostToolUse hook que detecta corrupção do STATE.md frontmatter.
//
// PROBLEMA QUE RESOLVE:
// Quando gsd-tools.cjs faz commit em projeto multi-milestone,
// pode sobrescrever o frontmatter para milestone: v1.0 / status: completed,
// mesmo se o projeto está em v1.1 / in_progress. Este bug foi observado
// em campo (Rota Certa v1.1) — STATE.md corrompido 4x em 2 sessões,
// sem detecção automática.
//
// COMPORTAMENTO:
// - Lê .planning/STATE.md após qualquer ferramenta que modificou arquivos
// - Compara milestone do frontmatter com o último entry de MILESTONES.md
// - Se divergente: emite warning loud no contexto + sugere comando de fix
// - Se MILESTONES.md inexistente: skip silencioso (projeto novo)
//
// Advisory only (não bloqueia).

const fs = require('fs');
const path = require('path');

let stdinBuffer = '';
const stdinTimeout = setTimeout(() => process.exit(0), 3000);

process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => { stdinBuffer += chunk; });
process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);
  try {
    main();
  } catch (e) {
    if (process.env.GSD_STATE_GUARD_DEBUG === '1') {
      console.error('GSD state guard error:', e.message);
    }
    process.exit(0);
  }
});

function main() {
  if (process.env.GSD_STATE_GUARD_ENABLED !== '1') {
    process.exit(0);
  }

  const stateFile = '.planning/STATE.md';
  const milestonesFile = '.planning/MILESTONES.md';

  if (!fs.existsSync(stateFile)) process.exit(0);

  const stateContent = fs.readFileSync(stateFile, 'utf8');
  const stateFrontmatter = parseFrontmatter(stateContent);

  if (!stateFrontmatter) process.exit(0);

  // Heurística 1: Detectar status: completed mas Current Position diz in_progress
  const stateMilestone = stateFrontmatter.milestone;
  const stateStatus = stateFrontmatter.status;

  // Procurar "Current Position" no body do STATE.md
  const positionMatch = stateContent.match(/##\s*Current Position[\s\S]*?(?=##|$)/i);
  const inProgressInBody = positionMatch && /in_progress|em\s*andamento/i.test(positionMatch[0]);

  if (stateStatus === 'completed' && inProgressInBody) {
    emitWarning([
      'STATE.md frontmatter pode estar corrompido:',
      `  status: ${stateStatus}`,
      `  milestone: ${stateMilestone}`,
      '  MAS o body indica milestone em andamento.',
      '',
      'Provável causa: gsd-tools.cjs sobrescreveu frontmatter incorretamente.',
      'Bug conhecido em projetos multi-milestone.',
      '',
      'Recomendação: verifique manualmente .planning/STATE.md e ajuste',
      'frontmatter para refletir milestone atual + status real.',
      '',
      'Se confirmado bug: reportar em SUGGESTIONS.md como SUG-XXX.'
    ]);
  }

  // Heurística 2: Comparar com MILESTONES.md (se existir)
  if (fs.existsSync(milestonesFile)) {
    const milestonesContent = fs.readFileSync(milestonesFile, 'utf8');
    const latestInProgress = findLatestInProgressMilestone(milestonesContent);

    if (latestInProgress && stateMilestone &&
        latestInProgress !== stateMilestone &&
        stateStatus === 'completed') {
      emitWarning([
        'STATE.md/MILESTONES.md divergência detectada:',
        `  STATE.md milestone: ${stateMilestone} (status: ${stateStatus})`,
        `  MILESTONES.md último in_progress: ${latestInProgress}`,
        '',
        'Provável causa: STATE.md frontmatter desatualizado após mudança de milestone.',
        '',
        'Para corrigir, edite .planning/STATE.md frontmatter:',
        `  milestone: ${latestInProgress}`,
        '  status: in_progress'
      ]);
    }
  }

  process.exit(0);
}

function parseFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return null;

  const fm = {};
  for (const line of match[1].split('\n')) {
    const m = line.match(/^([a-zA-Z_]+):\s*(.+)$/);
    if (m) {
      fm[m[1]] = m[2].trim().replace(/^["']|["']$/g, '');
    }
  }
  return fm;
}

function findLatestInProgressMilestone(content) {
  // Procurar tabela markdown com status in_progress
  const lines = content.split('\n');
  for (const line of lines) {
    if (/in_progress|in progress|⏳/i.test(line)) {
      // Tentar extrair MS-XX ou nome similar
      const m = line.match(/\|\s*(MS-\d+|v?\d+\.\d+\.\d+|[\w-]+milestone[\w-]*)\s*\|/i);
      if (m) return m[1];
    }
  }
  return null;
}

function emitWarning(lines) {
  console.log('');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('  ⚠️  GSD STATE GUARD — Alerta de integridade');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  for (const l of lines) {
    console.log('  ' + l);
  }
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
}
