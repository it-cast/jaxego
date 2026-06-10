#!/usr/bin/env node
// gsd-state-integrity-check.js
// gsd-hook-version: 0.8.0
//
// SessionStart hook — verifica integridade do STATE.md/MILESTONES.md
// na entrada da sessão. Se Claude começar a sessão com STATE.md
// corrompido, opera baseado em info errada (multi-milestone bug).
//
// Diferença para gsd-state-guard.js (PostToolUse):
// - Este roda 1x por sessão, antes do Claude tomar qualquer ação
// - Se detectar corrupção, alerta IMEDIATAMENTE com instruções
// - Mais barato (uma única vez) e mais visível (entrada da sessão)
//
// Advisory only (não bloqueia início da sessão).

const fs = require('fs');

try {
  const stateFile = '.planning/STATE.md';
  if (!fs.existsSync(stateFile)) process.exit(0);

  const content = fs.readFileSync(stateFile, 'utf8');
  const fm = parseFrontmatter(content);
  if (!fm) process.exit(0);

  const issues = [];

  // Issue 1: status=completed mas body sugere in_progress
  const positionMatch = content.match(/##\s*Current Position[\s\S]*?(?=##|$)/i);
  if (fm.status === 'completed' && positionMatch &&
      /in_progress|em\s*andamento/i.test(positionMatch[0])) {
    issues.push({
      severity: 'high',
      msg: `frontmatter diz "status: completed" mas Current Position diz in_progress`
    });
  }

  // Issue 2: MILESTONES.md tem milestone in_progress diferente do que STATE.md aponta
  const milestonesFile = '.planning/MILESTONES.md';
  if (fs.existsSync(milestonesFile)) {
    const m = fs.readFileSync(milestonesFile, 'utf8');
    const inProg = findLatestInProgressMilestone(m);
    if (inProg && fm.milestone && inProg !== fm.milestone) {
      issues.push({
        severity: 'medium',
        msg: `STATE.md aponta milestone "${fm.milestone}" mas MILESTONES.md tem "${inProg}" como in_progress`
      });
    }
  }

  // Issue 3: progress.percent = 100 mas total_phases > completed_phases
  const totalPhases = parseInt(fm['total_phases'] || '0');
  const completedPhases = parseInt(fm['completed_phases'] || '0');
  const percent = parseInt(fm['percent'] || '0');
  if (percent === 100 && totalPhases > completedPhases && totalPhases > 0) {
    issues.push({
      severity: 'medium',
      msg: `progress.percent=100 mas só ${completedPhases}/${totalPhases} phases completas`
    });
  }

  if (issues.length === 0) process.exit(0);

  console.log('');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('  🚨 GSD STATE INTEGRITY CHECK — INÍCIO DE SESSÃO');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  console.log('  Encontrei inconsistências no .planning/STATE.md:');
  console.log('');
  for (const issue of issues) {
    const icon = issue.severity === 'high' ? '🔴' : '🟡';
    console.log(`  ${icon} ${issue.msg}`);
  }
  console.log('');
  console.log('  CAUSAS PROVÁVEIS:');
  console.log('  - Bug do gsd-tools.cjs em projetos multi-milestone');
  console.log('  - Sobrescrita por hook ou commit anterior');
  console.log('  - Edição manual incompleta');
  console.log('');
  console.log('  AÇÃO RECOMENDADA ANTES DE CONTINUAR:');
  console.log('  1. Abra .planning/STATE.md e verifique frontmatter');
  console.log('  2. Compare com .planning/MILESTONES.md (se existir)');
  console.log('  3. Ajuste manualmente para refletir o estado real');
  console.log('  4. Se for bug recorrente: registre em SUGGESTIONS.md');
  console.log('');
  console.log('  Não opere com base em STATE.md corrompido.');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');

  process.exit(0);
} catch (e) {
  if (process.env.GSD_STATE_GUARD_DEBUG === '1') {
    console.error('GSD integrity check error:', e.message);
  }
  process.exit(0);
}

function parseFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return null;

  const fm = {};
  let inProgress = false;
  for (const line of match[1].split('\n')) {
    const m = line.match(/^([a-zA-Z_]+):\s*(.*)$/);
    if (m) {
      const key = m[1];
      const val = m[2].trim().replace(/^["']|["']$/g, '');
      fm[key] = val;
    } else {
      // Linha indentada (sub-key como progress.percent)
      const sub = line.match(/^\s+([a-zA-Z_]+):\s*(.+)$/);
      if (sub) {
        fm[sub[1]] = sub[2].trim().replace(/^["']|["']$/g, '');
      }
    }
  }
  return fm;
}

function findLatestInProgressMilestone(content) {
  const lines = content.split('\n');
  for (const line of lines) {
    if (/in_progress|in progress|⏳/i.test(line)) {
      const m = line.match(/\|\s*(MS-\d+|v?\d+\.\d+\.\d+|[\w-]+milestone[\w-]*)\s*\|/i);
      if (m) return m[1];
    }
  }
  return null;
}
