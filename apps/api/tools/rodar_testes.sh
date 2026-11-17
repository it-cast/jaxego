#!/usr/bin/env bash
# Roda a suíte da API num container descartável da imagem do Jaxegô (Python com SQLite; o Python
# local pode não ter o módulo _sqlite3). Não mexe no container em execução nem no banco: os testes
# usam SQLite em memória. Testes que pedem MySQL real (-m mysql) ficam de fora.
#   tools/rodar_testes.sh                 # suíte inteira
#   tools/rodar_testes.sh tests/api_public -x
set -euo pipefail
cd "$(dirname "$0")/.."
IMAGEM="${JAXEGO_IMAGEM:-jaxego-api}"
docker run --rm -v "$PWD":/app -w /app -e INNGEST_DEV=1 -e COLUMNS="${COLUMNS:-200}" "$IMAGEM" sh -c '
  pip install -q "pytest>=8.2,<9" "pytest-asyncio>=0.23,<1" "aiosqlite>=0.20,<1" "fakeredis>=2.36.1" "piexif>=1.1.3,<2" >/dev/null 2>&1
  python -m pytest -m "not mysql" -p no:cacheprovider "$@"
' sh "$@"
