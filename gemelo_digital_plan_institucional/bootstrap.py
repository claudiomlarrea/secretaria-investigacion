"""Inicializa el path del paquete Gemelo Digital Plan Institucional."""

from __future__ import annotations

import sys
from pathlib import Path

GEMELO_ROOT = Path(__file__).resolve().parent
if str(GEMELO_ROOT) not in sys.path:
    sys.path.insert(0, str(GEMELO_ROOT))
