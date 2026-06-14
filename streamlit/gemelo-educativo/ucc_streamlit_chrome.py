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
        </style>
        """,
        unsafe_allow_html=True,
    )
