"""Estética alineada a Encuesta Clara y al Observatorio de IA · UCCuyo."""
from __future__ import annotations

import base64
import html
from pathlib import Path

import pandas as pd
import streamlit as st

from constants import APP_NAME
from ucc_streamlit_chrome import hide_streamlit_cloud_toolbar

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
OBSERVATORIO_NAME = "Observatorio de Inteligencia Artificial"
INSTITUTION_NAME = "Universidad Católica de Cuyo"
OBSERVATORIO_SITE_URL = "https://claudiomlarrea.github.io/observatorio-ia/"


def inject_theme() -> None:
    hide_streamlit_cloud_toolbar()
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Montserrat', system-ui, -apple-system, sans-serif;
        }}

        [data-testid="stAppViewContainer"] {{
            background-color: {GRAY_INST};
        }}
        [data-testid="stHeader"] {{
            background-color: {GRAY_INST_SOFT};
        }}

        [data-testid="stAppViewContainer"] [data-testid="stMain"] .block-container {{
            padding-top: 2.75rem;
            padding-bottom: 2.5rem;
            max-width: 1180px;
        }}

        .ec-header-box {{
            box-sizing: border-box;
            width: 100%;
            margin: 0.5rem 0 0.85rem 0;
            padding: 0.65rem 0 0.85rem 0;
            border-bottom: 3px solid {GREEN};
        }}
        .ec-header-inner {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        .ec-header-logo img {{
            display: block;
            width: 84px;
            height: 84px;
            object-fit: contain;
        }}
        .ec-institutional-title {{
            margin: 0.15rem 0 0;
            font-size: 1.22rem;
            font-weight: 700;
            color: {GREEN};
            line-height: 1.25;
        }}
        .ec-institutional-sub {{
            margin: 0.25rem 0 0;
            font-size: 0.88rem;
            font-weight: 600;
            color: {TEXT_MUTED};
        }}

        .ec-hero {{
            background: linear-gradient(135deg, {SURFACE} 0%, {GREEN_LIGHT} 45%, {GRAY_INST_SOFT} 100%);
            border: 1px solid #B8D4C8;
            border-left: 5px solid {GREEN};
            border-radius: 14px;
            padding: 1.2rem 1.5rem 1.1rem;
            margin-bottom: 1.25rem;
            box-shadow: 0 4px 20px rgba(4, 74, 48, 0.07);
        }}
        .ec-hero h1 {{
            margin: 0 0 0.35rem 0;
            font-size: 1.65rem;
            font-weight: 700;
            color: {GREEN_DARK};
        }}
        .ec-hero p {{
            margin: 0;
            font-size: 0.98rem;
            line-height: 1.55;
            color: {TEXT_MUTED};
        }}
        .ec-hero .ec-badge {{
            display: inline-block;
            background: {GREEN};
            color: {SURFACE};
            font-size: 0.72rem;
            font-weight: 600;
            padding: 0.18rem 0.6rem;
            border-radius: 999px;
            margin-bottom: 0.5rem;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {GRAY_INST_SOFT} 0%, {GRAY_INST} 100%);
            border-right: 1px solid #C8C8C8;
        }}
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stMarkdown p {{
            color: {TEXT} !important;
        }}
        [data-testid="stSidebarNav"] a,
        [data-testid="stSidebarNav"] span {{
            color: {GREEN_DARK} !important;
        }}
        [data-testid="stSidebarNav"] a[aria-current="page"] {{
            background: {GREEN_LIGHT} !important;
        }}

        [data-testid="stMetric"] {{
            background: {SURFACE};
            border: 1px solid #C5D9CE;
            border-top: 3px solid {GREEN};
            border-radius: 12px;
            padding: 0.65rem 0.85rem;
        }}
        [data-testid="stMetric"] label {{
            color: {TEXT_MUTED} !important;
        }}
        [data-testid="stMetric"] [data-testid="stMetricValue"] {{
            color: {GREEN_DARK} !important;
        }}

        h2, h3, h4 {{
            color: {GREEN_DARK} !important;
        }}
        .stCaption {{
            color: {TEXT_MUTED} !important;
        }}

        .ec-site-links {{
            margin: 0 0 0.85rem 0;
            font-size: 0.92rem;
        }}
        .ec-site-links a {{
            color: {GREEN};
            font-weight: 600;
            text-decoration: none;
            border-bottom: 1px solid rgba(4, 74, 48, 0.35);
        }}
        .ec-site-links a:hover {{
            color: {GREEN_MID};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _logo_base64() -> str:
    if not LOGO_PATH.is_file():
        return ""
    return base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")


def render_site_links() -> None:
    obs = html.escape(OBSERVATORIO_SITE_URL)
    st.markdown(
        f"""
        <nav class="ec-site-links" aria-label="Sitio del Observatorio">
            <a href="{obs}" target="_blank" rel="noopener noreferrer">← Sitio del Observatorio de IA</a>
        </nav>
        """,
        unsafe_allow_html=True,
    )


def render_institutional_header() -> None:
    name = html.escape(OBSERVATORIO_NAME)
    inst = html.escape(INSTITUTION_NAME)
    b64 = _logo_base64()
    logo_html = f'<img src="data:image/png;base64,{b64}" alt="Logo {name}" />' if b64 else ""
    st.markdown(
        f"""
        <div class="ec-header-box">
            <div class="ec-header-inner">
                <div class="ec-header-logo">{logo_html}</div>
                <div class="ec-header-text">
                    <p class="ec-institutional-title">{name}</p>
                    <p class="ec-institutional-sub">{inst}</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_brand_header(subtitle: str) -> None:
    safe_name = html.escape(APP_NAME)
    safe_sub = html.escape(subtitle)
    st.markdown(
        f"""
        <div class="ec-hero">
            <span class="ec-badge">Herramienta de análisis</span>
            <h1>{safe_name}</h1>
            <p>{safe_sub}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page(subtitle: str) -> None:
    render_site_links()
    render_institutional_header()
    render_brand_header(subtitle)


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


SIM_SUBE_STYLE = "background-color: #E8F3EF; color: #044A30; font-weight: 600"
SIM_BAJA_STYLE = "background-color: #FCE8E8; color: #B42318; font-weight: 600"

# Escala continua: rojo (menor ponderación) → verde (mayor ponderación)
_ESCALA_ROJO_BG = (252, 232, 232)
_ESCALA_ROJO_FG = (180, 35, 24)
_ESCALA_VERDE_BG = (232, 243, 239)
_ESCALA_VERDE_FG = (4, 74, 48)


def _lerp(a: int, b: int, t: float) -> int:
    return int(round(a + (b - a) * t))


def _css_escala_cantidad(val, vmin: float, vmax: float) -> str:  # noqa: ANN001
    if not isinstance(val, (int, float)) or pd.isna(val):
        return ""
    if vmax <= vmin:
        t = 0.5
    else:
        t = max(0.0, min(1.0, (float(val) - vmin) / (vmax - vmin)))
    bg = (
        _lerp(_ESCALA_ROJO_BG[0], _ESCALA_VERDE_BG[0], t),
        _lerp(_ESCALA_ROJO_BG[1], _ESCALA_VERDE_BG[1], t),
        _lerp(_ESCALA_ROJO_BG[2], _ESCALA_VERDE_BG[2], t),
    )
    fg = (
        _lerp(_ESCALA_ROJO_FG[0], _ESCALA_VERDE_FG[0], t),
        _lerp(_ESCALA_ROJO_FG[1], _ESCALA_VERDE_FG[1], t),
        _lerp(_ESCALA_ROJO_FG[2], _ESCALA_VERDE_FG[2], t),
    )
    return (
        f"background-color: rgb({bg[0]},{bg[1]},{bg[2]}); "
        f"color: rgb({fg[0]},{fg[1]},{fg[2]}); font-weight: 600"
    )


def _resolver_referencia(
    referencia: float | dict[str, float] | None,
    columna: str,
    serie: pd.Series,
) -> float:
    if isinstance(referencia, dict):
        if columna in referencia:
            return float(referencia[columna])
        return float(serie.max()) if len(serie) else 1.0
    if referencia is not None:
        return float(referencia)
    return float(serie.max()) if len(serie) else 1.0


def estilizar_escala_cantidad(
    df: pd.DataFrame,
    columnas: tuple[str, ...],
    *,
    referencia_max: float | dict[str, float] | None = None,
    referencia_min: float | dict[str, float] = 0,
    decimales: int = 1,
) -> pd.io.formats.style.Styler:
    """Colorea celdas en escala rojo→verde según ponderación respecto al máximo de referencia."""
    tabla = df.copy()
    numericas = [c for c in tabla.columns if pd.api.types.is_numeric_dtype(tabla[c])]
    for col in numericas:
        tabla[col] = tabla[col].apply(
            lambda x: round(float(x), decimales) if pd.notna(x) and isinstance(x, (int, float)) else x
        )

    styled = tabla.style
    presentes = [c for c in columnas if c in tabla.columns]
    for col in presentes:
        vmin = (
            float(referencia_min[col])
            if isinstance(referencia_min, dict) and col in referencia_min
            else float(referencia_min)
        )
        vmax = _resolver_referencia(referencia_max, col, tabla[col])
        styled = styled.map(
            lambda v, vmin=vmin, vmax=vmax: _css_escala_cantidad(v, vmin, vmax),
            subset=[col],
        )

    if numericas:
        fmt = {col: f"{{:.{decimales}f}}" for col in numericas}
        styled = styled.format(fmt, na_rep="")

    return styled


def _css_variacion(val) -> str:  # noqa: ANN001
    if isinstance(val, (int, float)) and not pd.isna(val):
        if val > 0:
            return SIM_SUBE_STYLE
        if val < 0:
            return SIM_BAJA_STYLE
    return ""


def estilizar_variacion_tabla(
    df: pd.DataFrame,
    columnas_delta: tuple[str, ...],
    columnas_vinculadas: tuple[tuple[str, str], ...] = (),
    decimales: int = 1,
) -> pd.io.formats.style.Styler:
    """Colorea en verde las subas y en rojo las bajas según columnas Δ."""
    tabla = df.copy()
    numericas = [c for c in tabla.columns if pd.api.types.is_numeric_dtype(tabla[c])]
    for col in numericas:
        tabla[col] = tabla[col].apply(
            lambda x: round(float(x), decimales) if pd.notna(x) and isinstance(x, (int, float)) else x
        )

    styled = tabla.style
    presentes = [c for c in columnas_delta if c in tabla.columns]
    if presentes:
        styled = styled.map(_css_variacion, subset=presentes)

    if columnas_vinculadas:
        def _fila(row):  # noqa: ANN001
            estilos = [""] * len(row)
            idx = {nombre: i for i, nombre in enumerate(row.index)}
            for col_valor, col_delta in columnas_vinculadas:
                if col_valor not in idx or col_delta not in idx:
                    continue
                css = _css_variacion(row[col_delta])
                if css:
                    estilos[idx[col_valor]] = css
            return estilos

        styled = styled.apply(_fila, axis=1)

    if numericas:
        fmt = {col: f"{{:.{decimales}f}}" for col in numericas}
        styled = styled.format(fmt, na_rep="")

    return styled
