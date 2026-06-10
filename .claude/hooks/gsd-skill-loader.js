#!/usr/bin/env node
// gsd-skill-loader.js
// gsd-hook-version: 0.7.1
// GSD Skill Loader — UserPromptSubmit hook
//
// Lê prompt do user, detecta keywords em triggers.yaml de skills,
// e adiciona sugestão ao contexto sugerindo a Claude carregar a skill.

const fs = require('fs');
const path = require('path');

const SKILLS_ROOT = '.claude/skills';
const MAX_SUGGESTIONS = 5;
const MIN_KEYWORD_LENGTH = 3;
const MIN_PROMPT_LENGTH = 10;

let stdinBuffer = '';
const stdinTimeout = setTimeout(() => process.exit(0), 3000);

process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => { stdinBuffer += chunk; });
process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);
  try {
    main(stdinBuffer);
  } catch (e) {
    if (process.env.GSD_SKILL_LOADER_DEBUG === '1') {
      console.error('GSD skill loader error:', e.message);
    }
    process.exit(0);
  }
});

function main(input) {
  if (process.env.GSD_SKILL_LOADER_ENABLED !== '1') {
    process.exit(0);
  }

  let userPrompt = '';
  try {
    const payload = JSON.parse(input);
    userPrompt = (payload?.prompt || payload?.user_message || '').toLowerCase();
  } catch {
    userPrompt = input.toLowerCase();
  }

  if (!userPrompt || userPrompt.length < MIN_PROMPT_LENGTH) {
    process.exit(0);
  }

  const skillsDir = path.join(process.cwd(), SKILLS_ROOT);
  if (!fs.existsSync(skillsDir)) {
    process.exit(0);
  }

  const matchedSkills = scanSkills(skillsDir, userPrompt);
  if (matchedSkills.length === 0) {
    process.exit(0);
  }

  const top = matchedSkills.slice(0, MAX_SUGGESTIONS);

  console.log('');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('  📚 GSD SKILL LOADER — Skills relevantes detectadas');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  console.log('  Antes de responder, considere abrir:');
  console.log('');
  for (const s of top) {
    console.log(`    • .claude/skills/${s.path}/SKILL.md`);
    console.log(`      Razão: ${s.reason}`);
    console.log('');
  }
  console.log('  Em phases que envolvem PLAN.md, citar essas skills é');
  console.log('  OBRIGATÓRIO (validado pelo plan-checker — Dimension 6).');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');

  process.exit(0);
}

function scanSkills(skillsDir, prompt) {
  const matches = [];

  let categories;
  try {
    categories = fs.readdirSync(skillsDir).filter(c => {
      try {
        return fs.statSync(path.join(skillsDir, c)).isDirectory();
      } catch { return false; }
    });
  } catch { return []; }

  for (const cat of categories) {
    const catDir = path.join(skillsDir, cat);
    let skills;
    try {
      skills = fs.readdirSync(catDir).filter(s => {
        try {
          return fs.statSync(path.join(catDir, s)).isDirectory();
        } catch { return false; }
      });
    } catch { continue; }

    for (const skill of skills) {
      const triggerFile = path.join(catDir, skill, 'triggers.yaml');
      if (!fs.existsSync(triggerFile)) continue;

      try {
        const content = fs.readFileSync(triggerFile, 'utf8');
        const result = matchTriggers(content, prompt);
        if (result) {
          const priority = extractPriority(content);
          matches.push({
            path: `${cat}/${skill}`,
            name: skill,
            priority,
            reason: result.reason,
            section: result.section
          });
        }
      } catch {
        // skip malformed
      }
    }
  }

  // Ordenar: required > recommended, depois por priority
  matches.sort((a, b) => {
    if (a.section === 'required' && b.section !== 'required') return -1;
    if (b.section === 'required' && a.section !== 'required') return 1;
    const pri = { high: 3, medium: 2, low: 1 };
    return (pri[b.priority] || 2) - (pri[a.priority] || 2);
  });

  return matches;
}

function extractPriority(content) {
  const m = content.match(/^priority:\s*(\w+)/m);
  return m ? m[1] : 'medium';
}

function matchTriggers(content, prompt) {
  // Extrair keywords de required_for
  const requiredKws = extractKeywords(content, 'required_for');
  const matched = findMatch(requiredKws, prompt);
  if (matched) return { reason: `keyword "${matched}" (required)`, section: 'required' };

  // Tentar recommended_for
  const recommendedKws = extractKeywords(content, 'recommended_for');
  const matched2 = findMatch(recommendedKws, prompt);
  if (matched2) return { reason: `keyword "${matched2}" (recommended)`, section: 'recommended' };

  return null;
}

/**
 * Extrai todas as keywords de uma seção do triggers.yaml.
 * Strategy: split por linha. Identifica início da seção (key: no início de linha).
 * Continua até próxima key de top-level (linha começando com letra+:).
 * Dentro da seção, procura linhas com keyword_any: [...].
 */
function extractKeywords(content, sectionName) {
  const lines = content.split('\n');
  const keywords = [];
  let inSection = false;

  for (const line of lines) {
    // Top-level key (começa com letra, depois :, sem espaço antes)
    const isTopLevelKey = /^[a-z_]+:/i.test(line);

    if (isTopLevelKey) {
      if (line.startsWith(sectionName + ':')) {
        inSection = true;
        continue;
      } else if (inSection) {
        // Outra section, paramos
        break;
      }
    }

    if (inSection) {
      // Procurar keyword_any: [...]
      const m = line.match(/keyword_any:\s*\[([^\]]+)\]/);
      if (m) {
        const kws = m[1]
          .split(',')
          .map(k => k.trim().replace(/^["']|["']$/g, '').toLowerCase())
          .filter(k => k.length >= MIN_KEYWORD_LENGTH);
        keywords.push(...kws);
      }
    }
  }

  return keywords;
}

function findMatch(keywords, prompt) {
  for (const kw of keywords) {
    // Para keywords simples (sem espaço), exigir word boundary para evitar
    // falsos positivos como "cor" matching dentro de "score" ou "pis" em "kpis".
    // Para keywords compostas (com espaço), substring match é seguro.
    if (kw.includes(' ')) {
      if (prompt.includes(kw)) return kw;
    } else {
      // Word boundary regex (escapa caracteres especiais incluindo unicode)
      const escaped = kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const re = new RegExp('(^|[^a-zA-Z0-9_\u00C0-\u017F])' + escaped + '($|[^a-zA-Z0-9_\u00C0-\u017F])', 'i');
      if (re.test(prompt)) return kw;
    }
  }
  return null;
}
