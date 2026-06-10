#!/usr/bin/env node
/**
 * gsd-projeto-watcher.js — SessionStart hook
 *
 * Detecta se há arquivos novos ou modificados em projeto/ desde o último
 * /gsd:ingest. Se sim, sugere ao operador rodar /gsd:ingest novamente.
 *
 * Não bloqueia. Apenas avisa.
 *
 * Comparação:
 * - mtime do INGESTOR-HANDOFF.json (última execução do ingest)
 * - mtime mais recente de qualquer arquivo em projeto/ (excluindo READMEs)
 *
 * Adicionado em v0.9.1.
 */

const fs = require('fs');
const path = require('path');

const ENABLED = process.env.GSD_PROJETO_WATCHER_ENABLED !== '0';
if (!ENABLED) process.exit(0);

const PROJETO_DIR = 'projeto';
const HANDOFF_FILE = '.planning/INGESTOR-HANDOFF.json';

function getLatestMtime(dir) {
  let latest = 0;
  if (!fs.existsSync(dir)) return null;
  
  const walk = (current) => {
    const entries = fs.readdirSync(current, { withFileTypes: true });
    for (const entry of entries) {
      const full = path.join(current, entry.name);
      if (entry.isDirectory()) {
        walk(full);
      } else if (entry.isFile() && entry.name !== 'README.md') {
        const m = fs.statSync(full).mtimeMs;
        if (m > latest) latest = m;
      }
    }
  };
  
  try {
    walk(dir);
  } catch (e) {
    return null;
  }
  return latest > 0 ? latest : null;
}

try {
  // Se projeto/ não existe ou está vazio, hook é no-op
  if (!fs.existsSync(PROJETO_DIR)) process.exit(0);
  
  const latestProjeto = getLatestMtime(PROJETO_DIR);
  if (!latestProjeto) process.exit(0);  // pasta vazia
  
  // Se nunca rodou ingest, sugerir
  if (!fs.existsSync(HANDOFF_FILE)) {
    console.log('\n💡 Detectados arquivos em projeto/ mas /gsd:ingest nunca foi rodado.');
    console.log('   Rode: /gsd:ingest para gerar .planning/ automaticamente.\n');
    process.exit(0);
  }
  
  // Comparar mtimes
  const handoffMtime = fs.statSync(HANDOFF_FILE).mtimeMs;
  
  if (latestProjeto > handoffMtime) {
    const minutesSince = Math.floor((latestProjeto - handoffMtime) / 60000);
    console.log('\n💡 Detectados arquivos novos/modificados em projeto/ desde o último ingest.');
    console.log(`   Último ingest: ${new Date(handoffMtime).toISOString()}`);
    console.log(`   Última modificação em projeto/: ${minutesSince}min atrás`);
    console.log('   Sugestão: rode /gsd:ingest --only=requirements para atualizar REQs.\n');
  }
  
  process.exit(0);
} catch (e) {
  // Silent fail — hook não pode bloquear sessão
  process.exit(0);
}
