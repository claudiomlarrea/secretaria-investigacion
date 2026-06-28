#!/usr/bin/env bash
# MDeIA UCCuyo — entorno del proyecto.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
VENV="$ROOT/.venv-gemelo"
if [[ ! -x "$VENV/bin/python" ]]; then
  python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install -q -r requirements.txt -r modelo_mdeia/requirements.txt
exec "$VENV/bin/streamlit" run streamlit_app.py --server.port "${PORT:-8502}" "$@"
