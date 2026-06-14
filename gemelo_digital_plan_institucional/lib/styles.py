"""Estilos UCCuyo — Gemelo Digital Plan Institucional."""

from pathlib import Path

import streamlit as st

from constants import APP_NAME
from ucc_streamlit_chrome import hide_streamlit_cloud_toolbar

ROOT = Path(__file__).resolve().parent.parent
LOGO_UCCUYO = ROOT / "assets" / "logo_uccuyo.png"
LOGO_OIA = ROOT / "assets" / "logo-observatorio-ia.png"


def apply_styles() -> None:
    hide_streamlit_cloud_toolbar()
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] { background: #f4f0f1; }
        [data-testid="stSidebar"] { background: #4a0c1f !important; }

        /* Texto de navegación y etiquetas en sidebar */
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebarNav"] a,
        [data-testid="stSidebarNav"] span {
            color: #f8f4f5 !important;
        }

        /* Selectores e inputs: fondo claro y texto oscuro legible */
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] [data-baseweb="input"] {
            background-color: #ffffff !important;
            color: #1f1418 !important;
            border-color: #ddd5d8 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] span,
        [data-testid="stSidebar"] [data-baseweb="select"] input,
        [data-testid="stSidebar"] [data-baseweb="input"] input {
            color: #1f1418 !important;
            -webkit-text-fill-color: #1f1418 !important;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] svg {
            fill: #1f1418 !important;
        }

        .gemelo-banner {
            background: linear-gradient(90deg, #7a1532, #4a0c1f);
            color: #fff;
            padding: 1rem 1.25rem;
            border-radius: 12px;
            margin-bottom: 1rem;
        }
        .gemelo-banner h1 { margin: 0; font-size: 1.35rem; }
        .gemelo-banner p { margin: 0.35rem 0 0; opacity: 0.92; font-size: 0.95rem; }
        .proto-badge {
            display: inline-block;
            margin-top: 0.5rem;
            padding: 0.15rem 0.55rem;
            border-radius: 999px;
            font-size: 0.78rem;
            background: rgba(255,255,255,0.15);
            border: 1px solid rgba(255,255,255,0.25);
        }
        .alert-atencion {
            border-left: 4px solid #c45c00;
            background: #fff7ef;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
        }
        .alert-info {
            border-left: 4px solid #0d6e4f;
            background: #e8f5f0;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(subtitulo: str) -> None:
    apply_styles()
    c1, c2, c3 = st.columns([1, 1, 6])
    with c1:
        if LOGO_UCCUYO.exists():
            st.image(str(LOGO_UCCUYO), width=72)
    with c2:
        if LOGO_OIA.exists():
            st.image(str(LOGO_OIA), width=72)
        else:
            st.caption("Observatorio de IA")
    with c3:
        st.markdown(
            f"""
            <div class="gemelo-banner">
              <h1>{APP_NAME}</h1>
              <p>{subtitulo}</p>
              <span class="proto-badge">Prototipo interno · Observatorio de IA · UCCuyo</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
