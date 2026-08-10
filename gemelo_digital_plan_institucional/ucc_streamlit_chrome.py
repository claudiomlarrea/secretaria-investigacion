"""Oculta la barra superior de Streamlit Cloud en demos institucionales."""

from __future__ import annotations

import streamlit as st


def hide_streamlit_cloud_toolbar() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stHeader"] [data-testid="stToolbar"] {
            display: none !important;
        }

        /* Panel lateral siempre visible (ignora estado colapsado en el navegador) */
        [data-testid="stSidebar"] {
            transform: none !important;
            translate: none !important;
            min-width: 16.5rem !important;
            max-width: 22rem !important;
            visibility: visible !important;
        }

        [data-testid="stSidebarCollapseButton"],
        [data-testid="stExpandSidebarButton"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
