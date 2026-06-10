/**
 * Partition — particionamento determinístico de tasks para execução paralela.
 *
 * v0.9.6: antes, a lógica de "particionar por fronteira de arquivos" vivia
 * apenas como prosa no agente gsd-wave-dispatcher.md — o componente de MAIOR
 * risco do paralelismo dependia do LLM aplicar as regras de cabeça. Este
 * módulo torna a partição determinística e testável; o agente passa a CHAMAR
 * `gsd-tools partition` e obedecer ao resultado, em vez de calculá-la.
 *
 * Regras (espelham a tabela do agente):
 *  1. Fronteiras implícitas são EXPANDIDAS antes de comparar:
 *     - arquivo em models/ → arrasta models/__init__.py (registro central)
 *     - pyproject.toml → arrasta uv.lock e poetry.lock
 *     - package.json → arrasta package-lock.json, yarn.lock, pnpm-lock.yaml
 *  2. Task com arquivo SERIAL-TRIGGER vai para o trilho serial:
 *     - migrations (alembic/versions/, qualquer dir migrations/)
 *     - lockfiles (*.lock, package-lock.json)
 *     - config global (.planning/, angular.json, capacitor.config.*,
 *       settings.py, main.py raiz de app)
 *  3. Tasks restantes: union-find sobre interseção de arquivos expandidos.
 *     Qualquer arquivo em comum → mesmo grupo (não paralelizam entre si).
 *  4. Em dúvida (task sem files declarados) → serial. Conservador por design.
 */

const path = require('path');
const { output, error } = require('./core.cjs');

const SERIAL_TRIGGERS = [
  /(^|\/)alembic\/versions\//,
  /(^|\/)migrations\//,
  /(^|\/)package-lock\.json$/,
  /\.lock$/,                       // uv.lock, poetry.lock, yarn.lock, pnpm-lock.yaml (renomeado), Cargo.lock
  /(^|\/)pnpm-lock\.yaml$/,
  /(^|\/)\.planning\//,
  /(^|\/)angular\.json$/,
  /(^|\/)capacitor\.config\.(ts|json)$/,
  /(^|\/)settings\.py$/,
  /^(src\/)?(app\/)?main\.py$/,
];

const IMPLICIT_EXPANSIONS = [
  { match: /(^|\/)models\/[^/]+\.py$/, add: (f) => [path.posix.join(path.posix.dirname(f), '__init__.py')] },
  { match: /(^|\/)pyproject\.toml$/, add: (f) => {
      const dir = path.posix.dirname(f);
      return [path.posix.join(dir, 'uv.lock'), path.posix.join(dir, 'poetry.lock')];
    } },
  { match: /(^|\/)package\.json$/, add: (f) => {
      const dir = path.posix.dirname(f);
      return [
        path.posix.join(dir, 'package-lock.json'),
        path.posix.join(dir, 'yarn.lock'),
        path.posix.join(dir, 'pnpm-lock.yaml'),
      ];
    } },
];

function normalize(f) {
  return String(f).replace(/\\/g, '/').replace(/^\.\//, '');
}

function expandFiles(files) {
  const out = new Set();
  for (const raw of files) {
    const f = normalize(raw);
    out.add(f);
    for (const rule of IMPLICIT_EXPANSIONS) {
      if (rule.match.test(f)) {
        for (const extra of rule.add(f)) out.add(normalize(extra));
      }
    }
  }
  return out;
}

function serialReason(files) {
  for (const f of files) {
    for (const trig of SERIAL_TRIGGERS) {
      if (trig.test(f)) return `arquivo serial-trigger: ${f}`;
    }
  }
  return null;
}

function partitionTasks(tasks) {
  if (!Array.isArray(tasks)) {
    return { error: 'input deve ter campo "tasks" como array' };
  }

  const serial = [];
  const reasons = {};
  const parallelizable = [];

  for (const t of tasks) {
    const id = t.id || t.name;
    if (!id) return { error: 'toda task precisa de "id"' };
    const files = Array.isArray(t.files) ? t.files : [];

    if (files.length === 0) {
      serial.push(id);
      reasons[id] = 'sem files declarados — em dúvida, serial (conservador por design)';
      continue;
    }

    const expanded = expandFiles(files);
    const sr = serialReason(expanded);
    if (sr) {
      serial.push(id);
      reasons[id] = sr;
      continue;
    }
    parallelizable.push({ id, files: expanded });
  }

  // Union-find por interseção de arquivos
  const parent = {};
  const find = (x) => (parent[x] === x ? x : (parent[x] = find(parent[x])));
  const union = (a, b) => { parent[find(a)] = find(b); };
  for (const t of parallelizable) parent[t.id] = t.id;

  const fileOwner = {};
  for (const t of parallelizable) {
    for (const f of t.files) {
      if (fileOwner[f]) {
        union(t.id, fileOwner[f]);
        reasons[t.id] = reasons[t.id] || `compartilha ${f} com ${fileOwner[f]}`;
      } else {
        fileOwner[f] = t.id;
      }
    }
  }

  const groupMap = {};
  for (const t of parallelizable) {
    const root = find(t.id);
    (groupMap[root] = groupMap[root] || []).push(t.id);
  }
  const groups = Object.values(groupMap).sort((a, b) => b.length - a.length);

  return {
    serial,
    groups,
    parallel_viable: groups.length > 1,
    reasons,
    summary: groups.length > 1
      ? `${groups.length} grupos disjuntos paralelizáveis + ${serial.length} task(s) no trilho serial`
      : `wave é serial — ${serial.length + (groups[0]?.length || 0)} task(s); ` +
        (serial.length ? 'serial-triggers presentes' : 'tasks compartilham arquivos'),
  };
}

function cmdPartition(cwd, args, raw) {
  const fileArg = args.find(a => !a.startsWith('--'));
  let inputJson;
  if (fileArg) {
    const fs = require('fs');
    const full = path.isAbsolute(fileArg) ? fileArg : path.join(cwd, fileArg);
    if (!fs.existsSync(full)) error(`arquivo não encontrado: ${fileArg}`);
    inputJson = fs.readFileSync(full, 'utf-8');
  } else {
    // ler do stdin (síncrono)
    try {
      inputJson = require('fs').readFileSync(0, 'utf-8');
    } catch {
      error('Usage: gsd-tools partition <tasks.json>  (ou JSON via stdin)\nFormato: {"tasks":[{"id":"T1","files":["app/api/users.py"]}]}');
    }
  }

  let parsed;
  try { parsed = JSON.parse(inputJson); } catch (e) {
    error(`JSON inválido: ${e.message}`);
  }

  const result = partitionTasks(parsed.tasks);
  if (result.error) error(result.error);
  output(result, raw, result.summary);
}

module.exports = { cmdPartition, partitionTasks };
