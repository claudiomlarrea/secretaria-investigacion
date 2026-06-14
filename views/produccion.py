# -*- coding: utf-8 -*-
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "_path.py"))

import pandas as pd
import plotly.express as px
import streamlit as st

from lib.openalex import fetch_works, resumen_por_anio
from lib.styles import render_header

render_header("Producción científica UCCuyo · OpenAlex")

st.markdown(
    "Índice en tiempo casi real de publicaciones con afiliación **Universidad Católica de Cuyo**. "
    "Misma lógica que el sync diario hacia Looker (`indice_openalex`)."
)

year_from = st.sidebar.slider("Desde año", 2018, 2026, 2020)
max_pages = st.sidebar.slider("Páginas a consultar", 1, 8, 3)

with st.spinner("Consultando OpenAlex…"):
    rows = fetch_works(year_from=year_from, max_pages=max_pages)

if not rows:
    st.error("No se obtuvieron publicaciones. Reintentá en unos segundos.")
    st.stop()

df = pd.DataFrame(rows)
por_anio = resumen_por_anio(rows)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Publicaciones cargadas", len(df))
c2.metric("Con acceso abierto", int(df["oa"].sum()))
c3.metric("Años con producción", len(por_anio))
c4.metric("Último año", max(por_anio) if por_anio else "—")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Producción por año")
    serie = pd.DataFrame({"anio": list(por_anio.keys()), "publicaciones": list(por_anio.values())})
    fig = px.bar(serie, x="anio", y="publicaciones", text="publicaciones", color_discrete_sequence=["#7a1532"])
    fig.update_traces(textposition="outside")
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Tipos de obra")
    tipos = df["tipo"].value_counts().reset_index()
    tipos.columns = ["tipo", "cantidad"]
    fig2 = px.pie(tipos, names="tipo", values="cantidad", hole=0.35)
    fig2.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig2, use_container_width=True)

st.dataframe(
    df[["anio", "titulo", "autores", "tipo", "oa", "doi"]].head(40),
    hide_index=True,
    use_container_width=True,
)
