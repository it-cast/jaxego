#!/usr/bin/env node
// gsd-skill-application-check.js
// gsd-hook-version: 0.9.6
//
// PostToolUse hook que verifica se skills citadas em PLAN.md realmente
// aparecem APLICADAS no código (não apenas listadas).
//
// PROBLEMA QUE RESOLVE (Rota Certa Phase 9):
// - quality/observability-production foi citada como skill obrigatória
// - PLAN.md listou a skill (Gate 3 passou)
// - MAS Sentry crash reporting nunca foi implementado
// - Phase fechou sem o item — gate só validou citação, não aplicação
//
// HEURÍSTICA DE APLICAÇÃO:
// Skill considerada "aplicada" se ao menos 1 destes for true:
//   1. Comment "skill: <name>" ou "// REQ-NN" em código que toca o domínio da skill
//   2. Import de lib específica da skill (ex: sentry_sdk para observability)
//   3. Entry em DECISIONS.md mencionando a skill
//   4. Section em SUMMARY.md descrevendo aplicação
//
// COMPORTAMENTO:
// - Acionado quando SUMMARY.md é escrito (sinal de fim de execução)
// - Re-lê PLAN.md correspondente, extrai skills citadas
// - Verifica heurística para cada
// - Lista as não-aplicadas como WARNING (advisory)
//
// Não bloqueia. Mas torna gap visível antes de phase fechar.

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
    if (process.env.GSD_SKILL_APPLY_DEBUG === '1') {
      console.error('GSD skill application check error:', e.message);
    }
    process.exit(0);
  }
});

// Skills com sinais de import/uso bem identificáveis.
// v0.9.6: expandido de 12 para 69 skills. Skills de PROCESSO (meta/*, product
// discovery) têm fingerprints de ARTEFATO — o check varre SUMMARY.md além do
// código, então keywords do artefato contam como evidência de aplicação.
// Honestidade sobre o método: isto é heurística advisory. Keyword presente não
// prova aplicação profunda; keyword ausente é sinal forte de NÃO-aplicação.
// O check otimiza para o segundo caso (detectar skill citada e ignorada).
// Sem fingerprint (4 skills): ver SKILLS_SEM_FINGERPRINT abaixo, com razão.
const SKILL_FINGERPRINTS = {
  // ── br/ ──
  'br/brazilian-forms': {
    imports: [],
    keywords: ['cpf', 'cnpj', 'cep', 'viacep', 'máscara', 'mask', 'ddd'],
  },
  'br/lgpd-compliance': {
    imports: [],
    keywords: ['lgpd', 'consent', 'pii', 'anonymiz', 'consentimento', 'titular dos dados', 'retenção'],
  },
  'br/ux-copywriting-ptbr': {
    imports: [],
    keywords: ['microcopy', 'tom de voz', 'mensagem de erro', 'cta', 'copywriting'],
  },

  // ── domain/ ──
  'domain/angular-material-patterns': {
    imports: ['@angular/material'],
    keywords: ['matinput', 'mat-table', 'matdialog', 'mat-form-field'],
  },
  'domain/docker-production-ready': {
    imports: [],
    keywords: ['dockerfile', 'multi-stage', 'healthcheck', 'non-root', 'user app', 'compose'],
  },
  'domain/fastapi-production-patterns': {
    imports: ['fastapi', 'pydantic'],
    keywords: ['apirouter', 'depends(', 'selectinload', 'response_model', 'httpexception', 'lifespan'],
  },
  'domain/github-actions-ci': {
    imports: [],
    keywords: ['.github/workflows', 'runs-on', 'actions/checkout', 'pip-audit', 'npm audit', 'workflow_dispatch'],
  },
  'domain/ionic-patterns': {
    imports: ['@ionic/angular', '@capacitor/'],
    keywords: ['ion-', 'ionicmodule', 'capacitor'],
  },
  'domain/llm-integration-patterns': {
    imports: ['anthropic', 'openai', 'litellm', '@anthropic-ai/'],
    keywords: ['llm', 'fallback', 'retry', 'use_case', 'prompt registry'],
  },
  'domain/monorepo-deploy-safety': {
    imports: [],
    keywords: ['symlink', 'releases/', 'rollback', 'deploy-atomic', 'shared/', 'current ->'],
  },
  'domain/mysql-schema-design': {
    imports: [],
    keywords: ['create table', 'foreign key', 'utf8mb4', 'innodb', 'index', 'alembic'],
  },
  'domain/saas-billing-canonical': {
    imports: [],
    keywords: ['subscription', 'invoice', 'billing', 'trial', 'plan_id', 'webhook'],
  },
  'domain/safe2pay-escrow-br': {
    imports: [],
    keywords: ['safe2pay', 'escrow', 'split', 'marketplace', 'subconta'],
  },

  // ── meta/ (fingerprints de artefato — pegam no SUMMARY/PLAN) ──
  'meta/competitive-analysis': {
    imports: [],
    keywords: ['concorrente', 'competitor', 'benchmark', 'diferencial', 'comparativo'],
  },
  'meta/composition-patterns': {
    imports: [],
    keywords: ['composição', 'composition', 'slot', 'ng-content', 'children', 'wrapper'],
  },
  'meta/design-to-code': {
    imports: [],
    keywords: ['handoff', 'figma', 'specs', 'redline', 'design-to-code'],
  },
  'meta/empathy-map': {
    imports: [],
    keywords: ['empathy map', 'mapa de empatia', 'pensa e sente', 'dores', 'ganhos'],
  },
  'meta/jobs-to-be-done': {
    imports: [],
    keywords: ['jtbd', 'job to be done', 'jobs to be done', 'quando eu', 'progresso desejado'],
  },
  'meta/journey-map': {
    imports: [],
    keywords: ['journey', 'jornada', 'touchpoint', 'ponto de contato', 'etapa'],
  },
  'meta/north-star-vision': {
    imports: [],
    keywords: ['north star', 'métrica norte', 'estrela guia', 'visão de produto'],
  },
  'meta/opportunity-framework': {
    imports: [],
    keywords: ['oportunidade', 'opportunity solution tree', 'ost', 'árvore de oportunidade'],
  },
  'meta/orchestration-decision-tree': {
    imports: [],
    keywords: ['orquestraç', 'squad', 'wave', 'serial', 'paralel'],
  },
  'meta/parallel-orchestration': {
    imports: [],
    keywords: ['wave-dispatcher', 'partição', 'partition', 'disjunt', 'paralel', 'concurrent'],
  },
  'meta/productivity-estimation': {
    imports: [],
    keywords: ['estimativa', 'duration_hours', 'velocity', 'estimation', 'esforço'],
  },
  'meta/project-kickoff-interview': {
    imports: [],
    keywords: ['kickoff', 'entrevista', 'descoberta', 'discovery', 'levantamento'],
  },
  'meta/refactoring-ui': {
    imports: [],
    keywords: ['hierarchy', 'whitespace', 'alignment', 'refactoring ui', 'hierarquia visual'],
  },
  'meta/stack-advisor': {
    imports: [],
    keywords: ['trade-off', 'escolha de stack', 'stack decision', 'alternativa considerada'],
  },
  'meta/user-persona': {
    imports: [],
    keywords: ['persona', 'arquétipo', 'perfil de usuário'],
  },

  // ── mobile/ ──
  'mobile/offline-first': {
    imports: ['@capacitor/network', '@capacitor/preferences'],
    keywords: ['offline', 'sync', 'fila de sincroniza', 'sqlite', 'conflict', 'network status'],
  },
  'mobile/push-notifications-architecture': {
    imports: ['@capacitor/push-notifications', 'firebase'],
    keywords: ['fcm', 'push', 'notification', 'device token', 'token de dispositivo'],
  },

  // ── standalone ──
  'owasp-security': {
    imports: ['secrets', 'hashlib', 'hmac', 'argon2', 'bcrypt'],
    keywords: ['compare_digest', 'csrf', 'rate limit', 'allowlist', 'jwt', 'ssrf', 'sql injection', 'tenant_id'],
  },
  'prompt-engineering': {
    imports: [],
    keywords: ['system prompt', 'few-shot', 'prompt registry', 'temperatura', 'xml tags', 'chain of thought'],
  },
  'spartan-ai-toolkit': {
    imports: [],
    keywords: ['tdd', 'atomic commit', 'commit atômico', 'pre-code', 'quality gate', 'red-green'],
  },
  'systematic-debugging': {
    imports: [],
    keywords: ['hipótese', 'root cause', 'causa raiz', 'reproduç', 'bisect', 'isolamento'],
  },
  'ui-ux-pro-max': {
    imports: [],
    keywords: ['paleta', 'font pairing', 'anti-slop', 'design style', 'estilo visual'],
  },
  'webapp-testing': {
    imports: ['playwright', 'pytest', 'vitest', 'jest', '@playwright/'],
    keywords: ['test_', 'describe(', 'expect(', 'e2e', 'fixture'],
  },

  // ── product/ ──
  'product/api-design-contracts': {
    imports: [],
    keywords: ['idempotency', 'rate limit', 'pagination', 'error code', 'contract', 'versionamento de api'],
  },
  'product/component-library-governance': {
    imports: [],
    keywords: ['component library', 'design system', 'storybook', 'variant', 'governança de componente'],
  },
  'product/handoff-spec': {
    imports: [],
    keywords: ['handoff', 'spec de tela', 'annotation', 'redline', 'medidas'],
  },
  'product/micro-animations-delight': {
    imports: [],
    keywords: ['animation', 'keyframes', 'micro-interaç', 'delight', 'easing'],
  },
  'product/visual-regression-testing': {
    imports: ['playwright', 'percy', 'chromatic'],
    keywords: ['screenshot', 'visual regression', 'snapshot visual', 'baseline de imagem'],
  },

  // ── quality/ ──
  'quality/accessibility-pro': {
    imports: ['axe-core', '@axe-core/'],
    keywords: ['aria-label', 'aria-describedby', 'role=', 'wcag', 'a11y', 'foco visível'],
  },
  'quality/color-system': {
    imports: [],
    keywords: ['tokens.json', '--color-', '$color-', 'color token', 'design token'],
  },
  'quality/design-token-architecture': {
    imports: [],
    keywords: ['semantic token', 'primitive token', 'alias token', 'tokens.json', 'camada de token'],
  },
  'quality/error-ux-patterns': {
    imports: [],
    keywords: ['error state', 'estado de erro', 'retry', 'tentar novamente', 'fallback', 'recuperação'],
  },
  'quality/heuristic-evaluation': {
    imports: [],
    keywords: ['heurística', 'heuristic', 'nielsen', 'avaliação heurística', 'severidade'],
  },
  'quality/i18n-ready-architecture': {
    imports: ['@angular/localize', 'i18next', 'babel'],
    keywords: ['i18n', 'locale', 'translation', 'pluraliza', 'pt-br', 'string externalizada'],
  },
  'quality/layout-grid': {
    imports: [],
    keywords: ['grid', 'column', 'breakpoint', 'container', '12 col', 'gutter'],
  },
  'quality/observability-production': {
    imports: ['sentry_sdk', 'opentelemetry', 'prometheus_client', '@sentry/', 'logfire'],
    keywords: ['sentry.init', 'tracer.start_span', 'metrics.counter', 'logger.bind', 'request_id'],
  },
  'quality/performance-web-vitals': {
    imports: [],
    keywords: ['lcp', 'cls', 'inp', 'web vitals', 'lighthouse', 'lazy', 'preload'],
  },
  'quality/senior-quality-bar': {
    imports: [],
    keywords: ['quality-bar', 'fail-block', 'fail-debt', 'definição de pronto'],
  },
  'quality/spacing-system': {
    imports: [],
    keywords: ['--space-', '$space-', 'gap-', 'spacing scale', '4px grid', '8px grid'],
  },
  'quality/typography-scale': {
    imports: [],
    keywords: ['font-size', 'modular scale', 'line-height', 'typography', '--font-size'],
  },
  'quality/web-design-audit': {
    imports: [],
    keywords: ['auditoria visual', 'design audit', 'contraste', 'consistência visual', 'inventário de ui'],
  },

  // ── ux-advanced/ ──
  'ux-advanced/chat-ux-patterns': {
    imports: [],
    keywords: ['streaming', 'typing indicator', 'scroll anchor', 'bolha de mensagem', 'chat'],
  },
  'ux-advanced/dark-mode-theming': {
    imports: [],
    keywords: ['dark mode', 'prefers-color-scheme', 'tema escuro', 'color-scheme', 'theme toggle'],
  },
  'ux-advanced/data-tables-ux': {
    imports: [],
    keywords: ['sort', 'pagination', 'sticky header', 'coluna', 'tabela', 'bulk action'],
  },
  'ux-advanced/data-visualization': {
    imports: ['d3', 'chart.js', 'recharts', 'echarts', 'plotly'],
    keywords: ['chart', 'axis', 'legend', 'tooltip', 'gráfico'],
  },
  'ux-advanced/design-tokens-system': {
    imports: [],
    keywords: ['tokens.json', 'design token', '--token', 'primitive', 'token semântico'],
  },
  'ux-advanced/empty-states-polish': {
    imports: [],
    keywords: ['empty state', 'estado vazio', 'nenhum resultado', 'primeiro uso', 'zero-data'],
  },
  'ux-advanced/feedback-patterns': {
    imports: [],
    keywords: ['toast', 'snackbar', 'banner', 'inline validation', 'aria-live'],
  },
  'ux-advanced/file-upload-ux': {
    imports: [],
    keywords: ['upload', 'drag', 'drop', 'progress', 'mime', 'tamanho máximo'],
  },
  'ux-advanced/form-ux-mastery': {
    imports: [],
    keywords: ['formcontrol', 'validation', 'inline error', 'label', 'required', 'formulário'],
  },
  'ux-advanced/gesture-touch-patterns': {
    imports: [],
    keywords: ['swipe', 'gesture', 'long press', 'pull to refresh', 'touch target'],
  },
  'ux-advanced/loading-states': {
    imports: [],
    keywords: ['skeleton', 'shimmer', 'spinner', 'loading', 'optimistic update'],
  },
  'ux-advanced/motion-design-patterns': {
    imports: [],
    keywords: ['transition', 'duration', 'easing', 'reduced motion', 'animação'],
  },
  'ux-advanced/onboarding-patterns': {
    imports: [],
    keywords: ['onboarding', 'first run', 'tour', 'primeiro acesso', 'checklist inicial'],
  },
  'ux-advanced/payment-checkout-ux': {
    imports: [],
    keywords: ['checkout', 'pix', 'boleto', 'parcela', 'cartão', 'pagamento'],
  },
  'ux-advanced/responsive-breakpoint-strategy': {
    imports: [],
    keywords: ['breakpoint', '@media', 'media query', 'mobile-first', 'responsivo'],
  },
  'ux-advanced/saas-dashboard-patterns': {
    imports: [],
    keywords: ['dashboard', 'kpi', 'widget', 'filtro de período', 'card de métrica'],
  },
  'ux-advanced/search-filter-ux': {
    imports: [],
    keywords: ['debounce', 'facet', 'autocomplete', 'busca', 'filtro', 'search'],
  },
  'ux-advanced/trust-safety-ux': {
    imports: [],
    keywords: ['confirmação', 'destructive', 'undo', 'desfazer', 'ação irreversível'],
  },
  'ux-advanced/ui-input-rich-patterns': {
    imports: [],
    keywords: ['mask', 'datepicker', 'autocomplete', 'select', 'input rico'],
  },
};

// Skills SEM fingerprint, com razão documentada (não é esquecimento):
// — (nenhuma no momento: 69/73 skills têm fingerprint; as 4 restantes são
//    variantes cobertas por aliases em FINGERPRINT_ALIASES abaixo)
//
// Aliases: PLAN.md às vezes cita skills standalone com prefixo de categoria
// inexistente ("standalone/owasp-security") ou caminho completo. Normalizar.
const FINGERPRINT_ALIASES = {
  'standalone/owasp-security': 'owasp-security',
  'standalone/prompt-engineering': 'prompt-engineering',
  'standalone/spartan-ai-toolkit': 'spartan-ai-toolkit',
  'standalone/systematic-debugging': 'systematic-debugging',
  'standalone/ui-ux-pro-max': 'ui-ux-pro-max',
  'standalone/webapp-testing': 'webapp-testing',
};

function resolveFingerprint(skill) {
  const key = FINGERPRINT_ALIASES[skill] || skill;
  return { key, fp: SKILL_FINGERPRINTS[key] };
}


function main(input) {
  let payload;
  try { payload = JSON.parse(input); } catch { process.exit(0); }

  const toolName = payload?.tool_name || payload?.tool?.name || '';
  if (!/Edit|Write|MultiEdit/i.test(toolName)) process.exit(0);

  const filePath = payload?.tool_input?.file_path
    || payload?.tool_input?.path
    || '';

  if (!filePath || !/-SUMMARY\.md$/i.test(filePath)) process.exit(0);

  // Tentar localizar o PLAN.md correspondente
  const planFile = filePath.replace(/-SUMMARY\.md$/i, '-PLAN.md');
  if (!fs.existsSync(planFile)) process.exit(0);

  const planContent = fs.readFileSync(planFile, 'utf8');
  const skills = extractSkills(planContent);
  if (skills.length === 0) process.exit(0);

  const summaryContent = fs.readFileSync(filePath, 'utf8');
  const phaseDir = path.dirname(filePath);

  // Coletar texto agregado para análise: SUMMARY + arquivos de código no phase
  const codeContent = collectPhaseCode(phaseDir);

  // Verificar cada skill
  const notApplied = [];
  for (const skill of skills) {
    const { fp } = resolveFingerprint(skill);
    if (!fp) continue; // skill sem fingerprint — pular

    const applied = checkApplication(skill, fp, summaryContent, codeContent);
    if (!applied) {
      notApplied.push(skill);
    }
  }

  if (notApplied.length === 0) process.exit(0);

  console.log('');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('  ⚠️  GSD SKILL APPLICATION CHECK');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  console.log(`  PLAN.md cita ${skills.length} skill(s), mas algumas não parecem`);
  console.log('  ter sido APLICADAS no código:');
  console.log('');
  for (const skill of notApplied) {
    console.log(`    ❌ ${skill}`);
    const { fp } = resolveFingerprint(skill);
    if (fp.imports.length > 0) {
      console.log(`        Esperado: import de ${fp.imports.slice(0, 3).join(', ')}`);
    }
    if (fp.keywords.length > 0) {
      console.log(`        Esperado: keywords ${fp.keywords.slice(0, 3).join(', ')}`);
    }
    console.log('');
  }
  console.log('  AÇÃO: antes de fechar a phase, ou:');
  console.log('  (a) Aplicar a skill (adicionar código que pega no fingerprint), OU');
  console.log('  (b) Mover skill para "Skills Dispensadas" no PLAN.md com justificativa, OU');
  console.log('  (c) Registrar TD em TECH-DEBT.md com prazo definido');
  console.log('');
  console.log('  Skill citada ≠ skill aplicada — gate 3 valida apenas CITAÇÃO.');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');

  process.exit(0);
}

function extractSkills(planContent) {
  // Procurar seção "## Skills Consultadas" e extrair skill paths
  const sectionMatch = planContent.match(/##\s+Skills\s+Consultadas([\s\S]*?)(?=^##|\Z)/m);
  if (!sectionMatch) return [];

  const block = sectionMatch[1];
  const skills = [];
  for (const line of block.split('\n')) {
    // Padrões: "- meta/jobs-to-be-done", "- `quality/color-system`", "- skills/quality/spacing"
    // Com categoria: "- quality/color-system"; standalone: "- owasp-security"
    const m = line.match(/[-*]\s+`?(?:skills\/)?([\w-]+(?:\/[\w-]+)?)`?/);
    if (m) skills.push(m[1]);
  }
  return skills;
}

function collectPhaseCode(phaseDir) {
  // Para evitar I/O excessivo, lê apenas arquivos do phase dir + códigos referenciados
  // EXCLUINDO PLAN.md (skill listada lá não conta como "aplicada" — Gate 3 já valida citação).
  const buf = [];
  try {
    const files = fs.readdirSync(phaseDir);
    for (const f of files) {
      if (!/\.md$/.test(f)) continue;
      // Excluir PLAN.md — skill citada lá não é prova de aplicação.
      // Incluir SUMMARY, RESEARCH, CONTEXT, VERIFICATION, EXECUTION-LOG, DECISIONS locais.
      if (/-PLAN\.md$/i.test(f)) continue;
      try {
        buf.push(fs.readFileSync(path.join(phaseDir, f), 'utf8'));
      } catch {}
    }
  } catch {}

  // Tenta também ler DECISIONS.md global
  try {
    const decFile = path.join(process.cwd(), '.planning/DECISIONS.md');
    if (fs.existsSync(decFile)) {
      buf.push(fs.readFileSync(decFile, 'utf8'));
    }
  } catch {}

  return buf.join('\n').toLowerCase();
}

function checkApplication(skill, fp, summary, code) {
  const haystack = (summary + '\n' + code).toLowerCase();

  // Match de imports (mais forte)
  for (const imp of fp.imports) {
    if (haystack.includes(imp.toLowerCase())) return true;
  }

  // Match de keywords
  for (const kw of fp.keywords) {
    if (haystack.includes(kw.toLowerCase())) return true;
  }

  // Skill mencionada explicitamente em SUMMARY ("aplicamos quality/observability-production")
  if (haystack.includes(skill.toLowerCase())) return true;

  return false;
}
