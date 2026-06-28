# -*- coding: utf-8 -*-
"""Tema visual MDeIA UCCuyo · Observatorio de IA · UCCuyo."""

from __future__ import annotations

import base64
import html
from pathlib import Path

import pandas as pd
import streamlit as st

from constants import APP_NAME, APP_SUBTITLE, INSTITUTION_NAME, OBSERVATORIO_SITE_URL, UNIT_NAME

GREEN = "#044A30"
GREEN_DARK = "#033B26"
GREEN_LIGHT = "#E8F3EF"
GREEN_MID = "#0A5C3E"
ORANGE = "#EAA958"
MAROON = "#934B3F"
TEXT = "#1A2E28"
TEXT_MUTED = "#666666"
GRAY_INST = "#E8E8E8"
GRAY_INST_SOFT = "#F0F0F0"
SURFACE = "#FFFFFF"

CHART_SEQUENCE = [GREEN, ORANGE, MAROON, GREEN_MID, "#6B9080", "#C9A227", "#2D6A4F"]

LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logo-observatorio-ia.png"


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


def inject_theme() -> None:
    hide_streamlit_cloud_toolbar()
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] {{
            font-family: 'Montserrat', system-ui, -apple-system, sans-serif;
        }}
        [data-testid="stAppViewContainer"] {{ background-color: {GRAY_INST}; }}
        [data-testid="stAppViewContainer"] [data-testid="stMain"] .block-container {{
            padding-top: 2.75rem; padding-bottom: 2.5rem; max-width: 1180px;
        }}
        .mdeia-header-box {{
            border-bottom: 3px solid {GREEN}; margin: 0.5rem 0 0.85rem 0; padding-bottom: 0.85rem;
        }}
        .mdeia-header-inner {{ display: flex; align-items: center; gap: 1rem; }}
        .mdeia-header-inner img {{ width: 84px; height: 84px; object-fit: contain; }}
        .mdeia-title {{ margin: 0; font-size: 1.22rem; font-weight: 700; color: {GREEN}; }}
        .mdeia-sub {{ margin: 0.25rem 0 0; font-size: 0.88rem; color: {TEXT_MUTED}; font-weight: 600; }}
        .mdeia-hero {{
            background: linear-gradient(135deg, {SURFACE} 0%, {GREEN_LIGHT} 45%, {GRAY_INST_SOFT} 100%);
            border: 1px solid #B8D4C8; border-left: 5px solid {GREEN}; border-radius: 14px;
            padding: 1.2rem 1.5rem; margin-bottom: 1.25rem;
        }}
        .mdeia-hero h1 {{ margin: 0 0 0.35rem; font-size: 1.65rem; color: {GREEN_DARK}; }}
        .mdeia-hero p {{ margin: 0; color: {TEXT_MUTED}; line-height: 1.55; }}
        [data-testid="stMetric"] {{
            background: {SURFACE}; border: 1px solid #C5D9CE; border-top: 3px solid {GREEN};
            border-radius: 12px; padding: 0.65rem 0.85rem;
        }}
        h2, h3, h4 {{ color: {GREEN_DARK} !important; }}
        .mdeia-indicador {{ margin-bottom: 0.35rem; }}
        .mdeia-indicador-codigo {{
            margin: 0 0 0.25rem 0; font-size: 0.82rem; color: {TEXT_MUTED};
        }}
        .mdeia-indicador-codigo code {{
            background: {GREEN_LIGHT}; padding: 0.1rem 0.35rem; border-radius: 4px;
            white-space: nowrap;
        }}
        .mdeia-indicador-texto {{
            margin: 0 0 0.5rem 0; color: {TEXT}; font-size: 0.95rem; line-height: 1.55;
            white-space: normal !important; overflow: visible !important;
            word-wrap: break-word; overflow-wrap: anywhere;
        }}
        [data-testid="stExpanderDetails"] [data-testid="stMarkdownContainer"] p {{
            white-space: normal !important; overflow: visible !important;
            text-overflow: unset !important;
        }}
        [data-testid="stSlider"] [data-baseweb="slider"] div {{
            white-space: normal !important; overflow: visible !important;
            font-size: 0.78rem !important; line-height: 1.3 !important;
        }}
        [data-testid="stSlider"] {{
            overflow: visible !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _logo_base64() -> str:
    if not LOGO_PATH.is_file():
        return ""
    return base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")


def render_header(subtitle: str) -> None:
    b64 = _logo_base64()
    logo = f'<img src="data:image/png;base64,{b64}" alt="Logo OIA" />' if b64 else ""
    obs = html.escape(OBSERVATORIO_SITE_URL)
    st.markdown(
        f"""
        <nav style="margin-bottom:0.85rem;font-size:0.92rem;">
            <a href="{obs}" target="_blank" rel="noopener noreferrer"
               style="color:{GREEN};font-weight:600;text-decoration:none;">← Observatorio de IA</a>
        </nav>
        <div class="mdeia-header-box">
            <div class="mdeia-header-inner">
                <div>{logo}</div>
                <div>
                    <p class="mdeia-title">{html.escape(APP_NAME)}</p>
                    <p class="mdeia-sub">{html.escape(UNIT_NAME)} · {html.escape(INSTITUTION_NAME)}</p>
                </div>
            </div>
        </div>
        <div class="mdeia-hero">
            <h1>{html.escape(APP_SUBTITLE)}</h1>
            <p>{html.escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_plotly_style(fig):  # noqa: ANN001
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Montserrat, system-ui, sans-serif", color=TEXT, size=13),
        title_font=dict(size=16, color=GREEN_DARK),
        margin=dict(l=16, r=16, t=48, b=16),
        colorway=CHART_SEQUENCE,
    )
    fig.update_xaxes(gridcolor="#D4E4DB", linecolor="#B8CFC4")
    fig.update_yaxes(gridcolor="#D4E4DB", linecolor="#B8CFC4")
    return fig


def estilizar_escala_cantidad(df: pd.DataFrame, columnas_cantidad: list[str] | None = None):
    cols = columnas_cantidad or [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    styled = df.style
    for col in cols:
        if col not in df.columns:
            continue
        serie = pd.to_numeric(df[col], errors="coerce").dropna()
        if serie.empty:
            continue
        vmax = float(serie.max())
        vmin = float(serie.min())

        def _css(val, vmin=vmin, vmax=vmax):  # noqa: ANN001
            num = pd.to_numeric(val, errors="coerce")
            if pd.isna(num):
                return ""
            t = 0.5 if vmax <= vmin else (float(num) - vmin) / (vmax - vmin)
            t = max(0.0, min(1.0, t))
            r = int(252 + (110 - 252) * t)
            g = int(165 + (231 - 165) * t)
            b = int(165 + (183 - 165) * t)
            return f"background-color: rgb({r},{g},{b}); font-weight: 600"

        styled = styled.map(_css, subset=[col])
    return styled
