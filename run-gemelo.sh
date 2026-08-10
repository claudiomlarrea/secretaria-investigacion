#!/usr/bin/env bash
# Gemelo Digital PEI — siempre usa el entorno del proyecto (incluye plotly).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
VENV="$ROOT/.venv-gemelo"
if [[ ! -x "$VENV/bin/python" ]]; then
  python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install -q plotly pandas openpyxl scikit-learn python-docx 2>/dev/null || true
# Si el venv ya tiene streamlit, no reinstalar (requirements pide >=1.52; Python 3.9 del venv puede tener 1.50).
if ! "$VENV/bin/python" -c "import streamlit" 2>/dev/null; then
  "$VENV/bin/pip" install -q "streamlit>=1.48"
fi
exec "$VENV/bin/streamlit" run gemelo_streamlit_app.py --server.port "${PORT:-8501}" "$@"
