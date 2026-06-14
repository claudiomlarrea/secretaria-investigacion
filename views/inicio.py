# -*- coding: utf-8 -*-
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "_path.py"))

import pandas as pd
import plotly.express as px
import streamlit as st

from constants import APP_SUBTITLE
from lib.pei_model import load_baseline, objetivos_df, unidades_df
from lib.styles import render_header

render_header(f"Secretaría de Investigación · {APP_SUBTITLE}")

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
fig2 = px.pie(
    sede,
    names="sede",
    values="actividades",
    hole=0.45,
    color_discrete_sequence=px.colors.sequential.RdBu,
)
fig2.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
st.plotly_chart(fig2, use_container_width=True)

with st.expander("Fuentes de datos del Gemelo Digital Plan Institucional"):
    st.markdown(
        """
- **PEI 2025:** Memoria Académica y Análisis cuantitativo/cualitativo (805 actividades).
- **Publicaciones:** API OpenAlex, afiliación UCCuyo (`I4210121591`), mismo criterio que Looker.
- **Próxima etapa:** Formulario Único PEI y vínculo con planilla Looker / SIU WICHI.
        """
    )

st.caption("Gemelo Digital Plan Institucional · Universidad Católica de Cuyo · Secretaría de Investigación")
