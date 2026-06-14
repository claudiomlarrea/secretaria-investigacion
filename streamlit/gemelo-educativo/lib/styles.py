"""Estilos UCCuyo compartidos entre páginas del gemelo."""

from pathlib import Path

import streamlit as st

from ucc_streamlit_chrome import hide_streamlit_cloud_toolbar

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "assets" / "logo_uccuyo.png"


def setup_page(title: str, icon: str = "🎓") -> None:
    st.set_page_config(page_title=title, page_icon=icon, layout="wide")
    hide_streamlit_cloud_toolbar()
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] { background: #f4f0f1; }
        [data-testid="stSidebar"] { background: #4a0c1f !important; }
        [data-testid="stSidebar"] * { color: #f8f4f5 !important; }
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
    c1, c2 = st.columns([1, 7])
    with c1:
        if LOGO.exists():
            st.image(str(LOGO), width=88)
    with c2:
        st.markdown(
            f"""
            <div class="gemelo-banner">
              <h1>Gemelo digital educativo · UCCuyo</h1>
              <p>{subtitulo}</p>
              <span class="proto-badge">Prototipo interno · no publicado en el sitio web</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
