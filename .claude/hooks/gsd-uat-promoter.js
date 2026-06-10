#!/usr/bin/env node
// gsd-uat-promoter.js
// gsd-hook-version: 0.8.0
//
// PostToolUse hook que escaneia VERIFICATION.md/HUMAN-UAT.md de phases
// e auto-promove items "human_needed" para .planning/HUMAN-UAT-BACKLOG.md.
//
// PROBLEMA QUE RESOLVE:
// Items human_needed ficam espalhados em 3+ arquivos (Phase 7 5 itens,
// Phase 8 4 itens, Phase 9 4 itens — 13 itens total em 3 arquivos sem
// visão consolidada). Owner não sabe "o que ainda falta testar
// manualmente" sem ler todos.
//
// COMPORTAMENTO:
// - Acionado quando *-VERIFICATION.md ou *-HUMAN-UAT.md é escrito
// - Lê items marcados como human_needed | human-needed | 👤
// - Auto-append em HUMAN-UAT-BACKLOG.md se ainda não existirem lá
// - Idempotente: detecção por ID + título evita duplicação
//
// Advisory + ação automática (não bloqueia, mas modifica arquivo).

const fs = require('fs');
const path = require('path');

let stdinBuffer = '';
const stdinTimeout = setTimeout(() => process.exit(0), 3000);

process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => { stdinBuffer += chunk; });
process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);
  try {
    main(stdinBuffer);
  } catch (e) {
    if (process.env.GSD_UAT_PROMOTER_DEBUG === '1') {
      console.error('GSD UAT promoter error:', e.message);
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

  if (!filePath) process.exit(0);
  if (!/-(VERIFICATION|HUMAN-UAT)\.md$/i.test(filePath)) process.exit(0);
  if (!fs.existsSync(filePath)) process.exit(0);

  const backlogFile = '.planning/HUMAN-UAT-BACKLOG.md';
  if (!fs.existsSync(backlogFile)) process.exit(0);

  // Extrair phase_id do path
  const phaseMatch = filePath.match(/phases[/\\]([^/\\]+)[/\\]/);
  const phaseId = phaseMatch ? phaseMatch[1] : 'unknown';

  const content = fs.readFileSync(filePath, 'utf8');
  const items = extractHumanNeededItems(content, phaseId, filePath);

  if (items.length === 0) process.exit(0);

  const backlogContent = fs.readFileSync(backlogFile, 'utf8');
  const newItems = items.filter(item => !alreadyInBacklog(item, backlogContent));

  if (newItems.length === 0) {
    // Todos já estão promovidos — silencioso
    process.exit(0);
  }

  // Auto-append em HUMAN-UAT-BACKLOG.md
  const appended = appendItemsToBacklog(backlogFile, backlogContent, newItems);

  console.log('');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('  📋 GSD UAT PROMOTER — Items promovidos para backlog');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  console.log(`  Source: ${filePath}`);
  console.log(`  Phase: ${phaseId}`);
  console.log(`  Items novos: ${newItems.length}`);
  console.log('');
  for (const item of newItems.slice(0, 5)) {
    console.log(`  ✓ ${item.id} — ${item.title.slice(0, 60)}${item.title.length > 60 ? '...' : ''}`);
  }
  if (newItems.length > 5) {
    console.log(`  ... e mais ${newItems.length - 5} items`);
  }
  console.log('');
  console.log('  Items adicionados em .planning/HUMAN-UAT-BACKLOG.md');
  console.log('  Antes de fechar o milestone, execute cada item e marque status.');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');

  process.exit(0);
}

function extractHumanNeededItems(content, phaseId, sourceFile) {
  const items = [];

  // Padrão 1: bullet com human_needed na mesma linha
  // - [ ] T1.2 — Verify ScorePage SVG (human_needed) ...
  const inlinePattern = /^\s*-\s*\[\s\]\s+(.+?(?:human_needed|human-needed|👤).+?)$/gim;
  let m;
  while ((m = inlinePattern.exec(content)) !== null) {
    const fullLine = m[1].trim();
    items.push(buildItem(fullLine, phaseId, sourceFile));
  }

  // Padrão 2: tabela com coluna status human_needed
  // | UAT-08-01 | Validate KYC camera | mobile | human_needed |
  const tablePattern = /^\|\s*(UAT-[\w-]+|HUM-[\w-]+|TEST-[\w-]+)\s*\|\s*([^|]+)\s*\|.*?(?:human_needed|human-needed|👤).*?\|/gm;
  while ((m = tablePattern.exec(content)) !== null) {
    items.push({
      id: m[1].trim(),
      title: m[2].trim(),
      phase: phaseId,
      source: sourceFile,
      type: 'table-row',
    });
  }

  // Padrão 3: section "## human_needed" or "### Items que precisam de verificação humana"
  // Linha-a-linha porque regex multiline com lookahead em JS é frágil.
  const lines = content.split('\n');
  let inSection = false;
  let sectionStart = -1;
  const SECTION_HEADERS = [
    /^##+\s+human_needed/i,
    /^##+\s+Items?\s+que\s+precisam?\s+de\s+verificação\s+humana/i,
    /^##+\s+UAT\s+pendente/i,
    /^##+\s+Human\s+UAT/i,
  ];

  let sectionItems = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const isHeader = /^##+\s+/.test(line);

    if (inSection && isHeader) {
      // Sai da seção
      inSection = false;
      continue;
    }

    if (!inSection && SECTION_HEADERS.some(re => re.test(line))) {
      inSection = true;
      sectionStart = i;
      continue;
    }

    if (inSection) {
      const bm = line.match(/^[-*]\s+(.+)$/);
      if (bm && bm[1].trim().length >= 5) {
        sectionItems.push(bm[1].trim());
      }
    }
  }

  for (let i = 0; i < sectionItems.length; i++) {
    items.push(buildItem(sectionItems[i], phaseId, sourceFile, i + 1));
  }

  // Dedup pelo título (alguns padrões podem casar duas vezes)
  const seen = new Set();
  return items.filter(item => {
    const key = `${item.id}|${item.title.toLowerCase().slice(0, 50)}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function buildItem(rawLine, phaseId, sourceFile, idx) {
  // Tentar extrair ID se já tem (T1.2, UAT-XX, etc)
  const idMatch = rawLine.match(/(T\d+(?:\.\d+)?|UAT-[\w-]+|HUM-[\w-]+|TEST-[\w-]+)/);
  const id = idMatch ? idMatch[1] : `UAT-${phaseId}-auto${idx || ''}`;

  // Limpar título: remover marker human_needed e id detectado
  let title = rawLine
    .replace(/\s*\(human_needed\)\s*/gi, '')
    .replace(/\s*\(human-needed\)\s*/gi, '')
    .replace(/👤/g, '')
    .replace(/^\s*-\s*\[\s\]\s+/, '')
    .trim();

  if (idMatch) {
    title = title.replace(idMatch[0], '').trim();
    // Remove leading dashes/separators
    title = title.replace(/^[—–\-:\s]+/, '').trim();
  }

  return {
    id,
    title: title || rawLine.slice(0, 80),
    phase: phaseId,
    source: sourceFile,
    type: 'extracted',
  };
}

function alreadyInBacklog(item, backlogContent) {
  // Match por ID exato
  if (item.id && backlogContent.includes(item.id)) return true;
  // Match por título (primeiros 40 chars)
  const snippet = item.title.slice(0, 40).toLowerCase();
  if (snippet.length < 10) return false;
  return backlogContent.toLowerCase().includes(snippet);
}

function appendItemsToBacklog(backlogFile, current, items) {
  let block = '\n';
  for (const item of items) {
    block += `\n### ${item.id} — ${item.title}\n\n`;
    block += `- **Origem:** Phase \`${item.phase}\`, file \`${item.source}\`\n`;
    block += `- **Tipo:** [auto-extraído — refinar] (smoke | integration | visual | device | regression)\n`;
    block += `- **Pré-condição:** [preencher]\n`;
    block += `- **Passos:**\n`;
    block += `  1. [preencher]\n`;
    block += `- **Esperado:** [preencher]\n`;
    block += `- **Status:** 📋 pendente\n`;
    block += `- **Notas:** auto-promovido em ${new Date().toISOString().slice(0, 10)}\n`;
  }

  // Inserir antes da seção "## Itens validados" se existir,
  // senão append em "## Itens pendentes"
  let updated;
  if (current.includes('## Itens validados')) {
    updated = current.replace(
      '## Itens validados',
      block + '\n## Itens validados'
    );
  } else if (current.includes('## Itens pendentes')) {
    // append no final da seção pendentes
    updated = current.replace(
      /(## Itens pendentes[\s\S]*?)(\n##|\Z)/,
      `$1${block}$2`
    );
  } else {
    updated = current + block;
  }

  fs.writeFileSync(backlogFile, updated);
  return items.length;
}
