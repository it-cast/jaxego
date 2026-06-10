/**
 * Wireframe Contract — extrai o contrato estrutural de um wireframe HTML/JSX.
 *
 * v0.9.7: a cadeia de fidelidade de wireframe estava QUEBRADA. O ingestor lia
 * o DOM (DECISION-49), mas o ui-phase não era obrigado a consultar o wireframe
 * ao gerar o UI-SPEC, e nenhum checker validava a tela construída contra ele.
 * Resultado: wireframe informava a descoberta, mas a fidelidade na construção
 * dependia da boa vontade do agente.
 *
 * Este módulo fecha o elo: extrai do wireframe um CONTRATO verificável —
 * regiões, headings, elementos interativos (com texto e destino), forms,
 * estados e cores — que o UI-SPEC é obrigado a cobrir (Dimension 7 do
 * ui-checker) e que o verify-phase confere contra o código construído.
 *
 * Determinístico, sem dependências externas (regex sobre o markup estático).
 * Limitação honesta: HTML gerado por JS em runtime não é visível aqui — o
 * contrato cobre o DOM ESTÁTICO. Para wireframes Lovable/v0/bolt isso cobre
 * a quase totalidade da estrutura.
 */

const fs = require('fs');
const path = require('path');
const { output, error } = require('./core.cjs');

function stripComments(src) {
  return src.replace(/<!--[\s\S]*?-->/g, '').replace(/\/\*[\s\S]*?\*\//g, '');
}

function textOf(fragment) {
  return fragment
    .replace(/<[^>]+>/g, ' ')
    .replace(/\{[^}]*\}/g, ' ')      // expressões JSX
    .replace(/\s+/g, ' ')
    .trim();
}

function attr(tag, name) {
  const m = tag.match(new RegExp(`${name}\\s*=\\s*["']([^"']*)["']`, 'i'));
  return m ? m[1] : null;
}

function extractContract(src, sourcePath) {
  const html = stripComments(src);
  const contract = {
    source: sourcePath,
    regions: [],
    headings: [],
    interactive: [],   // { kind: button|link, text, target? }
    forms: [],         // { inputs: [{type,name,placeholder,label?}] , submit? }
    states: [],        // loading | empty | error | success detectados
    colors: [],        // cores literais encontradas (hex/rgb) — candidatas a token
    nav_targets: [],   // hrefs/rotas distintas
  };

  // Regiões semânticas (landmarks)
  for (const region of ['header', 'nav', 'main', 'aside', 'footer', 'section', 'form', 'table', 'dialog']) {
    const count = (html.match(new RegExp(`<${region}[\\s>]`, 'gi')) || []).length;
    if (count > 0) contract.regions.push({ region, count });
  }

  // Headings com texto
  const hMatches = html.matchAll(/<(h[1-6])[^>]*>([\s\S]*?)<\/\1>/gi);
  for (const m of hMatches) {
    const text = textOf(m[2]);
    if (text) contract.headings.push({ level: m[1].toLowerCase(), text: text.slice(0, 80) });
  }

  // Botões (button, input[type=submit|button], role=button)
  const btnMatches = html.matchAll(/<button([^>]*)>([\s\S]*?)<\/button>/gi);
  for (const m of btnMatches) {
    const text = textOf(m[2]) || attr(m[1], 'aria-label') || '(sem texto)';
    contract.interactive.push({ kind: 'button', text: text.slice(0, 60) });
  }
  const inputBtnMatches = html.matchAll(/<input([^>]*type\s*=\s*["'](?:submit|button)["'][^>]*)>/gi);
  for (const m of inputBtnMatches) {
    contract.interactive.push({ kind: 'button', text: attr(m[1], 'value') || '(submit)' });
  }

  // Links com destino
  const aMatches = html.matchAll(/<a([^>]*)>([\s\S]*?)<\/a>/gi);
  for (const m of aMatches) {
    const href = attr(m[1], 'href') || attr(m[1], 'routerLink') || attr(m[1], 'to');
    const text = textOf(m[2]) || attr(m[1], 'aria-label') || '(sem texto)';
    contract.interactive.push({ kind: 'link', text: text.slice(0, 60), target: href || undefined });
    if (href && href !== '#' && !href.startsWith('javascript:')) contract.nav_targets.push(href);
  }

  // Forms e inputs
  const formMatches = html.matchAll(/<form[^>]*>([\s\S]*?)<\/form>/gi);
  for (const fm of formMatches) {
    const inputs = [];
    const inMatches = fm[1].matchAll(/<(input|select|textarea)([^>]*)\/?>(?:[\s\S]*?<\/\1>)?/gi);
    for (const im of inMatches) {
      const t = attr(im[2], 'type');
      if (t === 'submit' || t === 'button' || t === 'hidden') continue;
      inputs.push({
        element: im[1].toLowerCase(),
        type: t || undefined,
        name: attr(im[2], 'name') || attr(im[2], 'formControlName') || undefined,
        placeholder: attr(im[2], 'placeholder') || undefined,
      });
    }
    if (inputs.length) contract.forms.push({ inputs });
  }

  // Estados detectados por convenção de classe/texto
  const stateHints = {
    loading: /loading|spinner|skeleton|shimmer|carregando/i,
    empty: /empty[-_ ]?state|nenhum resultado|no[-_ ]?results|estado vazio/i,
    error: /error[-_ ]?state|alert-danger|mensagem de erro|erro ao/i,
    success: /success|sucesso|toast-success|confirmad/i,
  };
  for (const [state, re] of Object.entries(stateHints)) {
    if (re.test(html)) contract.states.push(state);
  }

  // Cores literais (candidatas a virar/casar com token)
  const colorSet = new Set();
  for (const m of html.matchAll(/#(?:[0-9a-fA-F]{3}){1,2}\b|rgba?\([\d\s.,%]+\)/g)) {
    colorSet.add(m[0].toLowerCase());
    if (colorSet.size >= 24) break;
  }
  contract.colors = [...colorSet];

  // Dedup nav_targets
  contract.nav_targets = [...new Set(contract.nav_targets)];

  // Resumo para o UI-SPEC
  contract.checklist_size =
    contract.regions.length + contract.headings.length +
    contract.interactive.length + contract.forms.reduce((a, f) => a + f.inputs.length, 0);

  return contract;
}

function cmdWireframeContract(cwd, args, raw) {
  const fileArg = args.find(a => !a.startsWith('--'));
  if (!fileArg) {
    error('Usage: gsd-tools wireframe-contract <wireframe.(html|htm|jsx|tsx|vue|svelte)>\nExtrai o contrato estrutural que o UI-SPEC deve cobrir (Dimension 7).');
  }
  const full = path.isAbsolute(fileArg) ? fileArg : path.join(cwd, fileArg);
  if (!fs.existsSync(full)) error(`arquivo não encontrado: ${fileArg}`);

  const ext = path.extname(full).toLowerCase();
  const supported = ['.html', '.htm', '.jsx', '.tsx', '.vue', '.svelte'];
  if (!supported.includes(ext)) {
    error(`extensão ${ext} não suportada para contrato estrutural. Suportadas: ${supported.join(', ')}. ` +
      'Para wireframes em imagem (.png/.jpg/.pdf), a fidelidade é validada visualmente pelo ui-researcher — sem contrato mecânico.');
  }

  const src = fs.readFileSync(full, 'utf-8');
  const contract = extractContract(src, path.relative(cwd, full));
  output(contract, raw, `contrato: ${contract.checklist_size} itens verificáveis`);
}

module.exports = { cmdWireframeContract, extractContract };
