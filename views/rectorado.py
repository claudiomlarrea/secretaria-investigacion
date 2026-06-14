# -*- coding: utf-8 -*-
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "_path.py"))

import pandas as pd
import plotly.express as px
import streamlit as st

from lib.pei_model import indice_equilibrio, load_baseline, objetivos_df
from lib.styles import render_header

render_header("Panorama Rectorado · equilibrio estratégico del PEI 2025")

data = load_baseline()
obj = objetivos_df(data)

st.markdown(
    "Panorama institucional basado en las **805 actividades** registradas en 2025. "
    "Permite detectar concentraciones, brechas y prioridades de conducción."
)

c1, c2, c3 = st.columns(3)
pcts = obj["pct"].tolist()
c1.metric("Índice de equilibrio", indice_equilibrio(pcts))
c2.metric("Objetivo dominante", f"OG{int(obj.loc[obj['pct'].idxmax(), 'id'])}")
c3.metric("Menor intensidad", f"OG{int(obj.loc[obj['pct'].idxmin(), 'id'])}")

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Actividades por objetivo")
    fig = px.bar(
        obj,
        x="id",
        y="actividades",
        text="actividades",
        color="pct",
        color_continuous_scale=["#d4e8df", "#0d6e4f"],
        labels={"id": "Objetivo general", "actividades": "Actividades"},
    )
    fig.update_layout(coloraxis_showscale=False, height=360, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.subheader("Real vs. meta sugerida (%)")
    comp = obj.melt(
        id_vars=["id", "nombre"],
        value_vars=["pct", "meta_sugerida_pct"],
        var_name="serie",
        value_name="valor",
    )
    comp["serie"] = comp["serie"].map(
        {"pct": "2025 real", "meta_sugerida_pct": "Meta equilibrio (demo)"}
    )
    fig2 = px.line(
        comp,
        x="id",
        y="valor",
        color="serie",
        markers=True,
        labels={"id": "Objetivo", "valor": "%"},
        color_discrete_map={"2025 real": "#7a1532", "Meta equilibrio (demo)": "#0d6e4f"},
    )
    fig2.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Ejes temáticos institucionales")
temas = pd.DataFrame(data["ejes_tematicos"])
fig3 = px.treemap(temas, path=["eje"], values="peso", color="peso", color_continuous_scale="RdBu")
fig3.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
st.plotly_chart(fig3, use_container_width=True)

st.info(
    "**Lectura para rectorado:** el patrón 2025 es de equilibrio asimétrico — OG2 concentra más de la mitad "
    "de las acciones. Las metas sugeridas del Gemelo Digital Plan Institucional son ilustrativas para 2026."
)
