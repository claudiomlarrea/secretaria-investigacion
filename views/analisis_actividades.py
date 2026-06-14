# -*- coding: utf-8 -*-
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "_path.py"))

import pandas as pd
import plotly.express as px
import streamlit as st

from constants import APP_SUBTITLE
from lib.pei_model import (
    ANIOS_DISPONIBLES,
    actividades_por_anio_df,
    funciones_df,
    funcion_metricas,
    load_baseline,
    objetivos_df,
    sedes_df,
)
from lib.styles import render_header

render_header(f"Análisis de actividades del plan · {APP_SUBTITLE}")

anio = st.sidebar.selectbox("Año", ANIOS_DISPONIBLES, index=ANIOS_DISPONIBLES.index(2025))
data = load_baseline(anio)
obj = objetivos_df(data)
sede = sedes_df(data)
funciones = funciones_df(data)

st.markdown(
    f"Análisis de las **{data['total_actividades']} actividades** registradas en el Plan Estratégico "
    f"Institucional durante **{anio}**, organizadas por objetivos, sedes y funciones sustantivas."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Actividades del plan", data["total_actividades"])
c2.metric("Objetivos generales", len(obj))
c3.metric("Sedes", len(data["sedes"]))
c4.metric("Funciones sustantivas", len(funciones))

st.subheader("Evolución anual de actividades")
serie = actividades_por_anio_df()
fig_ev = px.line(
    serie,
    x="anio",
    y="total",
    markers=True,
    text="total",
    labels={"anio": "Año", "total": "Actividades registradas"},
    color_discrete_sequence=["#7a1532"],
)
fig_ev.update_traces(textposition="top center")
fig_ev.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig_ev, use_container_width=True)

col_a, col_b = st.columns(2)

with col_a:
    st.subheader(f"Distribución por objetivo ({anio})")
    fig_obj = px.bar(
        obj,
        x="nombre",
        y="pct",
        text="pct",
        color="pct",
        color_continuous_scale=["#e8c4cf", "#7a1532"],
        labels={"nombre": "Objetivo", "pct": "% actividades"},
    )
    fig_obj.update_traces(texttemplate="%{text}%", textposition="outside")
    fig_obj.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        height=360,
        xaxis_tickangle=-20,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig_obj, use_container_width=True)

with col_b:
    st.subheader(f"Intensidad por sede ({anio})")
    fig_sede = px.pie(
        sede,
        names="sede",
        values="actividades",
        hole=0.4,
        color_discrete_sequence=["#7a1532", "#c45c6a", "#e8c4cf"],
    )
    fig_sede.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_sede, use_container_width=True)

st.divider()
st.subheader("Funciones sustantivas de la universidad")

tabs = st.tabs(["Docencia", "Investigación", "Extensión"])

with tabs[0]:
    m = funcion_metricas("Docencia", data)
    d1, d2, d3 = st.columns(3)
    d1.metric("Alumnos (total)", f"{m['alumnos']:,}".replace(",", "."))
    d2.metric("Docentes (total)", m["docentes"])
    d3.metric("Alumnos por docente", m["ratio_alumnos_docente"])
    st.caption("Docencia: cantidad de alumnos y docentes por sede.")
    fig = px.bar(
        m["por_sede"],
        x="sede",
        y=["alumnos", "docentes"],
        barmode="group",
        labels={"value": "Cantidad", "variable": "Indicador"},
        color_discrete_map={"alumnos": "#7a1532", "docentes": "#0d6e4f"},
    )
    fig.for_each_trace(lambda t: t.update(name="Alumnos" if t.name == "alumnos" else "Docentes"))
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with tabs[1]:
    m = funcion_metricas("Investigación", data)
    i1, i2, i3 = st.columns(3)
    i1.metric("Investigadores", m["investigadores"])
    i2.metric("Actividades en investigación", m["actividades"])
    i3.metric("Actividades / investigador", m["actividades_por_investigador"])
    st.caption("Investigación: actividades del plan según cantidad de investigadores activos.")
    por = m["por_sede"].copy()
    por["ratio"] = (por["actividades"] / por["investigadores"]).round(2)
    fig = px.bar(
        por,
        x="sede",
        y="ratio",
        text="ratio",
        labels={"ratio": "Actividades por investigador"},
        color_discrete_sequence=["#7a1532"],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    m = funcion_metricas("Extensión", data)
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Convenios firmados", m["convenios"])
    e2.metric("Actividades de extensión", m["extension"])
    e3.metric("Voluntariado y comunidad", m["voluntariado"])
    e4.metric("Actividades en el plan", m["actividades_plan"])
    st.caption(
        "Extensión: convenios, actividades con la comunidad, voluntariado y otras acciones de vinculación."
    )
    fig = px.bar(
        m["por_sede"],
        x="sede",
        y="actividades",
        text="actividades",
        labels={"actividades": "Actividades de extensión"},
        color_discrete_sequence=["#0d6e4f"],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

for alerta in data["alertas"]:
    fn = st.warning if alerta["nivel"] == "atencion" else st.info
    fn(f"**{alerta['titulo']}** — {alerta['detalle']}")
