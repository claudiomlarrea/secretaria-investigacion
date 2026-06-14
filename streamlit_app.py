# -*- coding: utf-8 -*-
"""Gemelo Digital Plan Institucional — entrada Streamlit Cloud."""

import sys
from pathlib import Path

import streamlit as st

REPO = Path(__file__).resolve().parent
GEMELO = REPO / "gemelo_digital_plan_institucional"
VIEWS = REPO / "views"
for p in (str(REPO), str(GEMELO), str(VIEWS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from gemelo_digital_plan_institucional.constants import APP_NAME
from gemelo_digital_plan_institucional.lib.styles import apply_styles

st.set_page_config(page_title=APP_NAME, page_icon="🎓", layout="wide")
apply_styles()

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
