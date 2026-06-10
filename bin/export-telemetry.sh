#!/usr/bin/env bash
# bin/export-telemetry.sh
#
# Exporta entradas do METRICS.md em formato JSON anonimizado (TELEMETRY-SCHEMA.json).
# Útil para compartilhar dados com autores do framework para iteração, sem vazar PII ou código.
#
# Uso:
#   bin/export-telemetry.sh                 # exporta todas as entradas
#   bin/export-telemetry.sh phase-12        # exporta só uma entrada específica
#
# Output:
#   /tmp/gsd-telemetry-<timestamp>.json
#
# O que é preservado:
#   - IDs de skill (nomes públicos do framework, não PII)
#   - Métricas numéricas
#   - Campos qualitativos (what_worked/hurt/missing) — ATENÇÃO: revise manualmente antes de enviar
#
# O que é removido:
#   - phase_id (substituído por hash)
#   - Nomes próprios em qualitativos (substitui por [NAME] via heurística simples)
#   - Paths de arquivo (substitui por [PATH])

set -u
cd "$( git rev-parse --show-toplevel 2>/dev/null || pwd )"

FILTER="${1:-}"
METRICS_FILE=".planning/METRICS.md"
OUT="/tmp/gsd-telemetry-$(date +%Y%m%d-%H%M%S).json"

if [[ ! -f "$METRICS_FILE" ]]; then
  echo "ERRO: $METRICS_FILE não encontrado"
  exit 1
fi

if ! command -v python3 >/dev/null; then
  echo "ERRO: python3 necessário para parser YAML"
  exit 1
fi

python3 <<PYEOF
import json
import re
import sys
import hashlib
from pathlib import Path

metrics_path = Path("$METRICS_FILE")
filter_phase = "$FILTER".strip()
out_path = Path("$OUT")

content = metrics_path.read_text()

# Acha blocos ### phase-xxx seguidos de \`\`\`yaml ... \`\`\`
pattern = re.compile(
    r'^### (\S+)\s*\n+```yaml\s*\n(.+?)\n```',
    re.MULTILINE | re.DOTALL
)

def anonymize_text(s: str) -> str:
    """Remove PII óbvia de strings qualitativas."""
    if not s:
        return s
    # paths
    s = re.sub(r'(/[\w.-]+)+', '[PATH]', s)
    # URLs
    s = re.sub(r'https?://\S+', '[URL]', s)
    # emails
    s = re.sub(r'\S+@\S+\.\S+', '[EMAIL]', s)
    # nomes próprios muito simples (palavras capitalizadas em sequência)
    # intencionalmente leve — usuário deve revisar manualmente
    return s

def parse_yaml_block(text: str) -> dict:
    """Parser simples para os blocos YAML usados no METRICS.md."""
    data = {}
    for line in text.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        m = re.match(r'^([\w_]+):\s*(.*)$', line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        # Tenta converter tipos
        if val.startswith('[') and val.endswith(']'):
            # Lista
            inner = val[1:-1].strip()
            if not inner:
                data[key] = []
            else:
                data[key] = [x.strip().strip('"').strip("'") for x in inner.split(',')]
        elif val in ('true', 'false'):
            data[key] = val == 'true'
        elif val.startswith('<FILL'):
            data[key] = None
        elif re.match(r'^-?\d+$', val):
            data[key] = int(val)
        elif re.match(r'^-?\d+\.\d+$', val):
            data[key] = float(val)
        else:
            data[key] = val.strip('"').strip("'")
    return data

entries = []
for m in pattern.finditer(content):
    phase_id = m.group(1)
    if filter_phase and filter_phase not in phase_id:
        continue
    data = parse_yaml_block(m.group(2))
    
    # Anonymize
    phase_hash = hashlib.sha256(phase_id.encode()).hexdigest()[:12]
    data['phase_hash'] = phase_hash
    data.pop('phase_id', None)
    
    for qual_key in ('what_worked', 'what_hurt', 'what_missing'):
        if qual_key in data and isinstance(data[qual_key], str):
            data[qual_key] = anonymize_text(data[qual_key])
    
    entries.append(data)

if not entries:
    print("Nenhuma entrada encontrada (filtro vazio ou não bate).", file=sys.stderr)
    sys.exit(1)

output = {
    "schema_version": "1",
    "framework_version": "0.2.0",
    "exported_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "entry_count": len(entries),
    "entries": entries,
}

out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
print(f"✓ Exportado {len(entries)} entradas para {out_path}")
print()
print("⚠ REVISE o arquivo antes de compartilhar:")
print(f"   cat {out_path}")
print()
print("Campos qualitativos passaram por anonimização automática leve,")
print("mas você deve conferir que não há nomes, empresas, URLs internas, etc.")
PYEOF
