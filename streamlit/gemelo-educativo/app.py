# -*- coding: utf-8 -*-
"""Gemelo digital educativo UCCuyo — prototipo para autoridades (no enlazado al sitio público)."""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from lib.pei_model import load_baseline, objetivos_df, unidades_df
from lib.styles import render_header, setup_page

setup_page("Gemelo digital educativo · UCCuyo", "🎓")
render_header("Secretaría de Investigación · Memoria Académica 2025 · PEI 2023–2027")

data = load_baseline()
obj = objetivos_df(data)
uni = unidades_df(data)

st.markdown(
    """
    Prototipo interactivo para **rectorado, decanos y secretarías**: integra el estado del
    **Plan Estratégico Institucional** (805 actividades 2025), la **producción científica**
    (OpenAlex) y escenarios de **simulación estratégica**.
    """
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Actividades PEI 2025", data["total_actividades"])
c2.metric("Objetivos generales", len(obj))
c3.metric("Unidades modeladas", len(uni))
c4.metric("Año base", data["anio"])

left, right = st.columns([1.1, 1])

with left:
    st.subheader("Distribución por objetivo (2025)")
    fig = px.bar(
        obj,
        x="nombre",
        y="pct",
        text="pct",
        color="pct",
        color_continuous_scale=["#e8c4cf", "#7a1532"],
        labels={"nombre": "Objetivo", "pct": "% actividades"},
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=10, b=10),
        height=360,
        xaxis_tickangle=-18,
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Alertas del gemelo")
    for alerta in data["alertas"]:
        cls = "alert-atencion" if alerta["nivel"] == "atencion" else "alert-info"
        st.markdown(
            f'<div class="{cls}"><strong>{alerta["titulo"]}</strong><br>{alerta["detalle"]}</div>',
            unsafe_allow_html=True,
        )

st.subheader("Intensidad por sede")
sede = uni.groupby("sede", as_index=False)["actividades"].sum()
fig2 = px.pie(sede, names="sede", values="actividades", hole=0.45, color_discrete_sequence=px.colors.sequential.RdBu)
fig2.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.markdown("### Navegación del prototipo")
st.markdown(
    """
| Vista | Para quién | Qué muestra |
|-------|------------|-------------|
| **Panorama Rectorado** | Rectorado / Consejo Superior | Equilibrio estratégico, ejes temáticos, alertas |
| **Vista Decanato** | Decanos y directores | Benchmark de la unidad vs. institución |
| **Producción científica** | Secretaría de Investigación | Publicaciones UCCuyo vía OpenAlex |
| **Simulación PEI** | Planificación estratégica | Escenarios what-if sobre distribución de actividades |
"""
)

with st.expander("Fuentes de datos del prototipo"):
    st.markdown(
        """
- **PEI 2025:** Memoria Académica y Análisis cuantitativo/cualitativo (805 actividades).
- **Publicaciones:** API OpenAlex, afiliación UCCuyo (`I4210121591`), mismo criterio que Looker.
- **Próxima etapa:** carga del Formulario Único PEI y vínculo con planilla Looker / SIU WICHI.
        """
    )

st.caption("Prototipo interno · Universidad Católica de Cuyo · Secretaría de Investigación")
