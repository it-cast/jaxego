#!/usr/bin/env node
/**
 * gsd-td-aging.js — SessionStart hook
 *
 * Analisa .planning/TECH-DEBT.md para detectar TDs que estão envelhecendo
 * (aparecendo em múltiplas phases consecutivas como "pre-existing" / "out-of-scope")
 * e propõe promoção de urgency_class.
 *
 * Origem empírica (Rota Certa phases 2-4): bug TypeScript TS2352/TS2322
 * mencionado em 3 phases consecutivas como "pre-existing, out-of-scope".
 * Framework deveria forçar resolução em vez de permitir acúmulo.
 *
 * Regra:
 *   - TD aberta em > 2 phases sem progresso → propõe promoção de urgency_class
 *   - post_launch_quarter aberta há 3+ phases → propõe post_launch_30d
 *   - post_launch_30d aberta há 3+ phases → propõe pre_launch_high
 *   - pre_launch_high aberta há 2+ phases → propõe pre_launch_blocker
 *
 * Output: aviso no console + sugestão de comando para revisar.
 * Não bloqueia sessão. Não modifica arquivos automaticamente (operador decide).
 *
 * Adicionado em v0.9.2.
 */

const fs = require('fs');
const path = require('path');

const ENABLED = process.env.GSD_TD_AGING_ENABLED !== '0';
if (!ENABLED) process.exit(0);

const TD_FILE = '.planning/TECH-DEBT.md';
const STATE_FILE = '.planning/STATE.md';
const METRICS_FILE = '.planning/METRICS.md';

function parseTDLine(line) {
  // Formato: | TD-XXX | desc | reason | owner | Phase N+M | urgency | plan | status |
  if (!line.startsWith('|')) return null;
  if (line.includes('---')) return null;  // separador
  if (line.includes('| ID ')) return null;  // header
  
  const cells = line.split('|').map(c => c.trim()).filter((_, i, arr) => i > 0 && i < arr.length - 1);
  if (cells.length < 8) return null;
  
  return {
    id: cells[0],
    description: cells[1],
    reason: cells[2],
    owner: cells[3],
    deadline: cells[4],
    urgency_class: cells[5],
    plan_to_resolve: cells[6],
    status: cells[7]
  };
}

function getCurrentPhase() {
  if (!fs.existsSync(STATE_FILE)) return null;
  const content = fs.readFileSync(STATE_FILE, 'utf8');
  // Procurar yaml frontmatter ou seção com phase atual
  const phaseMatch = content.match(/current_phase:\s*([0-9]+)/i) ||
                     content.match(/Phase\s+([0-9]+)/);
  return phaseMatch ? parseInt(phaseMatch[1]) : null;
}

function getPhaseHistoryFromMetrics() {
  // Conta phases completas no METRICS.md
  if (!fs.existsSync(METRICS_FILE)) return [];
  const content = fs.readFileSync(METRICS_FILE, 'utf8');
  const phases = [];
  const phaseMatches = content.matchAll(/- phase:\s*([0-9.]+)/g);
  for (const m of phaseMatches) {
    phases.push(parseFloat(m[1]));
  }
  return phases;
}

function getTDFirstSeenInRetros(tdId) {
  // Tenta detectar primeira phase que mencionou esta TD
  const retrosDir = '.planning/retros';
  if (!fs.existsSync(retrosDir)) return null;
  
  try {
    const files = fs.readdirSync(retrosDir).filter(f => f.endsWith('.md')).sort();
    for (const file of files) {
      const content = fs.readFileSync(path.join(retrosDir, file), 'utf8');
      if (content.includes(tdId)) {
        const phaseMatch = file.match(/phase-?([0-9.]+)/);
        if (phaseMatch) return parseFloat(phaseMatch[1]);
      }
    }
  } catch (e) {
    return null;
  }
  return null;
}

function suggestPromotion(currentClass) {
  const promotions = {
    'post_launch_quarter': 'post_launch_30d',
    'post_launch_30d': 'pre_launch_high',
    'pre_launch_high': 'pre_launch_blocker',
  };
  return promotions[currentClass] || null;
}

function getAgingThreshold(urgencyClass) {
  // Quantas phases pode ficar aberta antes de promover
  const thresholds = {
    'post_launch_quarter': 4,
    'post_launch_30d': 3,
    'pre_launch_medium': 3,
    'pre_launch_high': 2,
    'pre_launch_blocker': 1,
  };
  return thresholds[urgencyClass] || 3;
}

try {
  if (!fs.existsSync(TD_FILE)) {
    process.exit(0);  // sem TECH-DEBT.md, sem aging para analisar
  }
  
  const content = fs.readFileSync(TD_FILE, 'utf8');
  const lines = content.split('\n');
  
  const openTDs = lines
    .map(parseTDLine)
    .filter(td => td && (td.status === 'aberto' || td.status === 'em-progresso'));
  
  if (openTDs.length === 0) {
    process.exit(0);  // sem TDs abertas
  }
  
  const currentPhase = getCurrentPhase();
  const phaseHistory = getPhaseHistoryFromMetrics();
  const phasesCount = phaseHistory.length;
  
  // Analisar cada TD aberta
  const agingTDs = [];
  
  for (const td of openTDs) {
    const firstSeen = getTDFirstSeenInRetros(td.id);
    if (firstSeen === null) continue;
    
    // Quantas phases passaram desde primeira aparição?
    const phasesElapsed = phaseHistory.filter(p => p > firstSeen).length;
    
    const threshold = getAgingThreshold(td.urgency_class);
    
    if (phasesElapsed >= threshold) {
      const suggestedNew = suggestPromotion(td.urgency_class);
      agingTDs.push({
        id: td.id,
        description: td.description.substring(0, 60),
        currentClass: td.urgency_class,
        phasesElapsed,
        threshold,
        firstSeen,
        suggestedNew
      });
    }
  }
  
  if (agingTDs.length === 0) {
    process.exit(0);  // tudo dentro do prazo
  }
  
  // Alerta visível
  console.log('');
  console.log('\x1b[33m⏰ TD AGING DETECTADO\x1b[0m');
  console.log('');
  console.log(`${agingTDs.length} TD(s) acumulando entre phases. Histórico de campo (Rota Certa, Augur, Alfie):`);
  console.log(`bug pré-existente mencionado em 3+ phases consecutivas vira ruído crônico, não é resolvido.`);
  console.log('');
  console.log('TDs aging:');
  
  for (const td of agingTDs) {
    const promoStr = td.suggestedNew ? ` → sugere promover para \x1b[31m${td.suggestedNew}\x1b[0m` : ' (já no topo)';
    console.log(`  • ${td.id}: ${td.description}`);
    console.log(`    Aberta há ${td.phasesElapsed} phases (threshold: ${td.threshold}). Classe atual: ${td.currentClass}${promoStr}`);
  }
  
  console.log('');
  console.log('Sugestão: rode \x1b[36m/gsd:td-review\x1b[0m para decidir promoção ou resolver.');
  console.log('');
  
  process.exit(0);
} catch (e) {
  // Falha silenciosa — hook não pode bloquear sessão
  if (process.env.GSD_DEBUG) {
    console.error('gsd-td-aging error:', e.message);
  }
  process.exit(0);
}
