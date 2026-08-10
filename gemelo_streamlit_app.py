# -*- coding: utf-8 -*-
"""Gemelo Digital Plan Institucional — PEI · UCCuyo (app separada del MDeIA UCCuyo)."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
GEMELO = REPO / "gemelo_digital_plan_institucional"
VIEWS = REPO / "views"
for p in (str(GEMELO), str(REPO), str(VIEWS)):
    if p not in sys.path:
        sys.path.insert(0, p)


def _require_gemelo_deps() -> None:
    missing = []
    for mod in ("streamlit", "pandas", "plotly"):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if not missing:
        return
    msg = (
        "Faltan dependencias del Gemelo Digital: "
        + ", ".join(missing)
        + ".\n\nEjecutá desde la carpeta del proyecto:\n\n"
        "  ./run-gemelo.sh\n\n"
        "o:\n\n"
        "  .venv-gemelo/bin/pip install -r requirements.txt\n"
        "  .venv-gemelo/bin/streamlit run gemelo_streamlit_app.py\n"
    )
    print(msg, file=sys.stderr)
    try:
        import streamlit as st

        st.error(msg)
        st.stop()
    except ImportError:
        sys.exit(1)


_require_gemelo_deps()

import streamlit as st

from constants import APP_NAME
from lib.app_tour import maybe_auto_start_tour, render_tour_sidebar
from ui_theme import inject_theme

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_theme()
maybe_auto_start_tour()
render_tour_sidebar()

pages = [
    st.Page(
        str(VIEWS / "analisis_actividades.py"),
        title="Análisis de actividades del plan",
        icon="📊",
        default=True,
    ),
    st.Page(
        str(VIEWS / "gemelo_digital.py"),
        title="Gemelo digital",
        icon="🎓",
    ),
]

st.navigation(pages).run()
