#!/usr/bin/env bash
# bin/convert-docs.sh
#
# Escaneia docs/ e gera espelhos .md ao lado de arquivos binários
# que o Claude não lê diretamente (xlsx, docx, pptx).
#
# Resultado:
#   docs/research/concorrentes.xlsx     (original, preservado)
#   docs/research/concorrentes.xlsx.md  (gerado, o que Claude lê)
#
# Re-rodar depois que o original mudar.
#
# Dependências:
#   - pandoc (para docx/pptx) — brew install pandoc / apt install pandoc
#   - python3 + openpyxl (para xlsx) — pip install openpyxl
#
# Uso:
#   bin/convert-docs.sh           # escaneia docs/
#   bin/convert-docs.sh --force   # regenera mesmo se .md já existe e está mais novo
#   bin/convert-docs.sh <dir>     # escaneia diretório específico

set -u
cd "$( git rev-parse --show-toplevel 2>/dev/null || pwd )"

FORCE=0
ROOT="docs"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=1; shift ;;
    -*) echo "Flag desconhecida: $1"; exit 1 ;;
    *) ROOT="$1"; shift ;;
  esac
done

if [[ ! -d "$ROOT" ]]; then
  echo "ERRO: diretório '$ROOT' não encontrado"
  exit 1
fi

# Checa dependências
HAS_PANDOC=0
HAS_OPENPYXL=0

if command -v pandoc >/dev/null; then HAS_PANDOC=1; fi
if python3 -c "import openpyxl" 2>/dev/null; then HAS_OPENPYXL=1; fi

GREEN=$(printf '\033[0;32m')
YELLOW=$(printf '\033[1;33m')
RED=$(printf '\033[0;31m')
RESET=$(printf '\033[0m')

if [[ $HAS_PANDOC -eq 0 ]]; then
  echo "${YELLOW}⚠${RESET}  pandoc não encontrado — .docx e .pptx serão pulados"
  echo "    Instalar: brew install pandoc  OU  apt install pandoc"
fi
if [[ $HAS_OPENPYXL -eq 0 ]]; then
  echo "${YELLOW}⚠${RESET}  openpyxl não encontrado — .xlsx serão pulados"
  echo "    Instalar: pip install openpyxl"
fi

echo ""
echo "Escaneando $ROOT/..."
echo ""

CONVERTED=0
SKIPPED=0
FAILED=0

# Retorna 1 se precisa converter (destino não existe ou fonte mais nova)
needs_convert() {
  local src="$1"
  local dst="$2"
  [[ $FORCE -eq 1 ]] && return 0
  [[ ! -f "$dst" ]] && return 0
  # Source mais nova que dest?
  [[ "$src" -nt "$dst" ]] && return 0
  return 1
}

convert_xlsx() {
  local src="$1"
  local dst="${src}.md"
  
  if [[ $HAS_OPENPYXL -eq 0 ]]; then
    echo "${YELLOW}⏭${RESET}  $src (openpyxl ausente)"
    SKIPPED=$((SKIPPED + 1))
    return
  fi
  
  if ! needs_convert "$src" "$dst"; then
    echo "${GREEN}✓${RESET}  $dst (já atual)"
    SKIPPED=$((SKIPPED + 1))
    return
  fi
  
  if python3 <<PYEOF
import openpyxl
from pathlib import Path
import sys

try:
    wb = openpyxl.load_workbook('$src', data_only=True, read_only=True)
    out = Path('$dst')
    
    lines = [f"# {Path('$src').name}", ""]
    lines.append(f"> Gerado automaticamente de {Path('$src').name} por bin/convert-docs.sh")
    lines.append(f"> Re-gerar após editar o .xlsx: rodar o script de novo")
    lines.append("")
    
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        lines.append(f"## Aba: {sheet_name}")
        lines.append("")
        
        # Coleta linhas (limite para evitar explosão)
        rows = []
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i >= 1000:
                lines.append(f"_(truncado após 1000 linhas)_")
                break
            rows.append(row)
        
        if not rows:
            lines.append("_(aba vazia)_")
            lines.append("")
            continue
        
        # Primeira linha = header
        header = [str(c) if c is not None else "" for c in rows[0]]
        if not any(header):
            lines.append("_(sem header identificável — renderizando como tabela bruta)_")
            lines.append("")
            continue
        
        # Limita a 30 colunas (senão Markdown fica ilegível)
        if len(header) > 30:
            lines.append(f"_(tabela com {len(header)} colunas, truncada em 30)_")
            header = header[:30]
        
        lines.append("| " + " | ".join(h or "—" for h in header) + " |")
        lines.append("|" + "|".join("---" for _ in header) + "|")
        
        for row in rows[1:]:
            cells = [str(c) if c is not None else "" for c in row[:len(header)]]
            # Escapa pipes no conteúdo
            cells = [c.replace("|", "\\\\|").replace("\n", " ") for c in cells]
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
    
    out.write_text("\n".join(lines))
    sys.exit(0)
except Exception as e:
    print(f"Erro: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
  then
    echo "${GREEN}✓${RESET}  gerado: $dst"
    CONVERTED=$((CONVERTED + 1))
  else
    echo "${RED}✗${RESET}  falhou: $src"
    FAILED=$((FAILED + 1))
  fi
}

convert_docx() {
  local src="$1"
  local dst="${src}.md"
  
  if [[ $HAS_PANDOC -eq 0 ]]; then
    echo "${YELLOW}⏭${RESET}  $src (pandoc ausente)"
    SKIPPED=$((SKIPPED + 1))
    return
  fi
  
  if ! needs_convert "$src" "$dst"; then
    echo "${GREEN}✓${RESET}  $dst (já atual)"
    SKIPPED=$((SKIPPED + 1))
    return
  fi
  
  if pandoc "$src" -f docx -t gfm -o "$dst.tmp" 2>/dev/null; then
    {
      echo "# $(basename "$src")"
      echo ""
      echo "> Gerado automaticamente de $(basename "$src") por bin/convert-docs.sh"
      echo "> Re-gerar após editar o .docx: rodar o script de novo"
      echo ""
      cat "$dst.tmp"
    } > "$dst"
    rm -f "$dst.tmp"
    echo "${GREEN}✓${RESET}  gerado: $dst"
    CONVERTED=$((CONVERTED + 1))
  else
    rm -f "$dst.tmp"
    echo "${RED}✗${RESET}  falhou: $src"
    FAILED=$((FAILED + 1))
  fi
}

convert_pptx() {
  local src="$1"
  local dst="${src}.md"
  
  if [[ $HAS_PANDOC -eq 0 ]]; then
    echo "${YELLOW}⏭${RESET}  $src (pandoc ausente)"
    SKIPPED=$((SKIPPED + 1))
    return
  fi
  
  if ! needs_convert "$src" "$dst"; then
    echo "${GREEN}✓${RESET}  $dst (já atual)"
    SKIPPED=$((SKIPPED + 1))
    return
  fi
  
  # pandoc lê pptx diretamente
  if pandoc "$src" -f pptx -t gfm -o "$dst.tmp" 2>/dev/null; then
    {
      echo "# $(basename "$src")"
      echo ""
      echo "> Gerado automaticamente de $(basename "$src") por bin/convert-docs.sh"
      echo "> Para imagens/slides, abrir o original."
      echo ""
      cat "$dst.tmp"
    } > "$dst"
    rm -f "$dst.tmp"
    echo "${GREEN}✓${RESET}  gerado: $dst"
    CONVERTED=$((CONVERTED + 1))
  else
    rm -f "$dst.tmp"
    echo "${RED}✗${RESET}  falhou: $src"
    FAILED=$((FAILED + 1))
  fi
}

# Encontrar e processar
while IFS= read -r -d '' file; do
  case "$file" in
    *.xlsx|*.xls) convert_xlsx "$file" ;;
    *.docx|*.doc) convert_docx "$file" ;;
    *.pptx|*.ppt) convert_pptx "$file" ;;
  esac
done < <(find "$ROOT" -type f \( -name "*.xlsx" -o -name "*.xls" -o -name "*.docx" -o -name "*.doc" -o -name "*.pptx" -o -name "*.ppt" \) -print0 2>/dev/null)

echo ""
echo "==============================="
echo "Convertidos:  $CONVERTED"
echo "Já atuais:    $SKIPPED"
echo "Falhados:     $FAILED"

if [[ $FAILED -gt 0 ]]; then
  exit 1
fi
