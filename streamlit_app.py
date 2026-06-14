# -*- coding: utf-8 -*-
"""Gemelo Digital Plan Institucional — Observatorio de IA · UCCuyo."""

import sys
from pathlib import Path

import streamlit as st

REPO = Path(__file__).resolve().parent
GEMELO = REPO / "gemelo_digital_plan_institucional"
VIEWS = REPO / "views"
for p in (str(GEMELO), str(REPO), str(VIEWS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from constants import APP_NAME
from ui_theme import inject_theme

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_theme()

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
