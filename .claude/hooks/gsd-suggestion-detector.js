#!/usr/bin/env node
// gsd-suggestion-detector.js
// gsd-hook-version: 0.8.0
//
// PostToolUse hook — quando Claude escreve em SUMMARY.md, RETRO.md ou
// VERIFICATION.md, escaneia por keywords que indicam insights não-óbvios
// que mereciam virar SUGGESTIONS.md entry.
//
// PROBLEMA QUE RESOLVE:
// SUGGESTIONS.md ficou vazio em 9 phases consecutivas (Rota Certa) mesmo
// com pelo menos 6 insights relevantes descobertos durante execução
// (NUMERIC overflow, dateutil.rrule para dias úteis, scoped_session no worker,
// async double-commit, CODE_SIGN_STYLE, versionCode reset). Regra 10 do
// CLAUDE.md exige promoção mas não é enforced.
//
// COMPORTAMENTO:
// - Detecta keywords como "descobri", "aprendi", "solução foi", "padrão",
//   "armadilha", "pitfall", "anti-pattern", "lição"
// - Sugere ao Claude (advisory) registrar em SUGGESTIONS.md
// - Não bloqueia
//
// Advisory only.

const fs = require('fs');

const TRIGGER_FILES = [
  /-SUMMARY\.md$/i,
  /-RETRO\.md$/i,
  /-VERIFICATION\.md$/i,
  /retros\/.*\.md$/i,
];

const INSIGHT_KEYWORDS = [
  // pt-BR
  'descobri',
  'aprendi',
  'solução foi',
  'lição',
  'aprendizado',
  'armadilha',
  'pegadinha',
  'gotcha',
  'padrão útil',
  'anti-pattern',
  'anti-padrão',
  // en
  'discovered',
  'learned',
  'workaround',
  'pitfall',
  'caveat',
  'tip:',
  'note:',
  'insight:',
  // technical signals
  'should be added to suggestions',
  'goes to suggestions',
  'vira tech debt',
  'vira sugestão',
];

let stdinBuffer = '';
const stdinTimeout = setTimeout(() => process.exit(0), 3000);

process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => { stdinBuffer += chunk; });
process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);
  try {
    main(stdinBuffer);
  } catch (e) {
    if (process.env.GSD_SUGGESTION_DEBUG === '1') {
      console.error('GSD suggestion detector error:', e.message);
    }
    process.exit(0);
  }
});

function main(input) {
  let payload;
  try {
    payload = JSON.parse(input);
  } catch {
    process.exit(0);
  }

  // Apenas fires em Edit/Write/MultiEdit
  const toolName = payload?.tool_name || payload?.tool?.name || '';
  if (!/Edit|Write|MultiEdit/i.test(toolName)) process.exit(0);

  const filePath = payload?.tool_input?.file_path
    || payload?.tool_input?.path
    || '';

  if (!filePath) process.exit(0);
  if (!TRIGGER_FILES.some(re => re.test(filePath))) process.exit(0);

  // Ler o arquivo recém escrito
  if (!fs.existsSync(filePath)) process.exit(0);

  const content = fs.readFileSync(filePath, 'utf8').toLowerCase();

  // Procurar keywords
  const found = [];
  for (const kw of INSIGHT_KEYWORDS) {
    if (content.includes(kw.toLowerCase())) {
      found.push(kw);
    }
  }

  if (found.length < 2) process.exit(0); // só notifica se pelo menos 2 indicadores

  // Verificar se SUGGESTIONS.md existe
  const suggestionsPath = '.planning/SUGGESTIONS.md';
  if (!fs.existsSync(suggestionsPath)) process.exit(0);

  const suggestionsContent = fs.readFileSync(suggestionsPath, 'utf8');
  // Heurística: SUGGESTIONS.md tem corpo significativo?
  const hasContent = suggestionsContent.length > 500
    && /^##\s+SUG-/m.test(suggestionsContent);

  // Se já tem conteúdo, baixar prioridade do alerta (humano já está ativo)
  // Se está vazio, alerta forte

  console.log('');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('  💡 GSD SUGGESTION DETECTOR — Insights detectados');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  console.log(`  Arquivo: ${filePath}`);
  console.log(`  Indicadores encontrados (${found.length}): ${found.slice(0, 5).join(', ')}`);
  console.log('');

  if (!hasContent) {
    console.log('  ⚠️  SUGGESTIONS.md está vazio ou não tem entries SUG-*.');
    console.log('');
    console.log('  Regra 10 do CLAUDE.md: insights não-óbvios descobertos');
    console.log('  durante execução DEVEM virar entry em SUGGESTIONS.md.');
    console.log('');
    console.log('  AÇÃO RECOMENDADA antes de fechar a phase:');
    console.log('  1. Re-leia o arquivo acima');
    console.log('  2. Identifique 1-3 insights generalizáveis (úteis fora desta phase)');
    console.log('  3. Adicione como SUG-XXX em .planning/SUGGESTIONS.md');
    console.log('  4. Inclua: contexto, padrão descoberto, quando aplica');
  } else {
    console.log('  Considere se algum insight merece nova entry SUG-XXX.');
    console.log('  Se sim, adicione antes de fechar a phase.');
  }

  console.log('═══════════════════════════════════════════════════════════');
  console.log('');

  process.exit(0);
}
