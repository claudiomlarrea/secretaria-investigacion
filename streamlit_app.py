# -*- coding: utf-8 -*-
"""MDeIA UCCuyo — Madurez digital e IA · UCCuyo.

Ejecutar:
    streamlit run streamlit_app.py

(Gemelo Digital del PEI: streamlit run gemelo_streamlit_app.py)
"""

from pathlib import Path
import runpy

_APP = Path(__file__).resolve().parent / "modelo_mdeia" / "app.py"
runpy.run_path(str(_APP), run_name="__main__")
