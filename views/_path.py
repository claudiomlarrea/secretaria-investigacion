"""Asegura imports del Gemelo Digital Plan Institucional en cada vista."""

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_GEMELO = _REPO / "gemelo_digital_plan_institucional"
for p in (str(_REPO), str(_GEMELO)):
    if p not in sys.path:
        sys.path.insert(0, p)
