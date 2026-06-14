# -*- coding: utf-8 -*-
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parent.parent
_GEMELO = _ROOT / "gemelo_digital_plan_institucional"
for _dir in (_GEMELO, _ROOT):
    _s = str(_dir)
    if _s not in sys.path:
        sys.path.insert(0, _s)

import plotly.express as px
import streamlit as st

from lib.pei_model import (
    ANIOS_DISPONIBLES,
    funcion_metricas,
    load_baseline,
    planilla_evolucion_anual_df,
    planilla_funciones_resumen_df,
    planilla_indicadores_institucionales_por_anio_df,
    planilla_objetivos_df,
    planilla_sedes_df,
    planilla_unidades_df,
)
from lib.styles import apply_plotly_style, render_header
from ui_theme import CHART_SEQUENCE, GREEN, estilizar_variacion_tabla

render_header(
    "Actividades del Plan Estratégico Institucional por año, sede y función sustantiva "
    "(Docencia, Investigación y Extensión). Datos de referencia: Memoria Académica 2025."
)

anio = st.sidebar.selectbox("Año", ANIOS_DISPONIBLES, index=ANIOS_DISPONIBLES.index(2025))
data = load_baseline(anio)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Actividades del plan", data["total_actividades"])
c2.metric("Objetivos generales", len(data["objetivos"]))
c3.metric("Sedes", len(data["sedes"]))
c4.metric("Funciones sustantivas", len(data["funciones_sustantivas"]))

st.subheader("Indicadores institucionales · serie histórica")
st.caption(
    "Actividades reales del PEI según Memoria Académica y análisis cuantitativo. "
    "Los valores 2023–2024 se estiman a partir del volumen de actividades del plan de cada año."
)

planilla_hist = planilla_indicadores_institucionales_por_anio_df()
st.dataframe(
    estilizar_variacion_tabla(planilla_hist, columnas_delta=("Δ último año",)),
    hide_index=True,
    use_container_width=True,
    column_config={
        "Área": st.column_config.TextColumn("Área", width="medium"),
        "Indicador": st.column_config.TextColumn("Indicador", width="large"),
    },
)

st.subheader(f"Planillas del PEI · {anio}")
st.caption(data.get("fuente", "Memoria Académica y análisis del PEI."))

tab_og, tab_fun, tab_sede, tab_evol, tab_det = st.tabs(
    [
        "Objetivos generales",
        "Funciones sustantivas",
        "Sedes",
        "Evolución anual",
        "Detalle por unidad",
    ]
)

with tab_og:
    st.dataframe(planilla_objetivos_df(data), hide_index=True, use_container_width=True)

with tab_fun:
    st.dataframe(planilla_funciones_resumen_df(data), hide_index=True, use_container_width=True)

with tab_sede:
    col_t1, col_t2 = st.columns([3, 2])
    with col_t1:
        st.dataframe(planilla_sedes_df(data), hide_index=True, use_container_width=True)
    with col_t2:
        sede = planilla_sedes_df(data)
        fig_sede = apply_plotly_style(
            px.pie(
                sede,
                names="Sede",
                values="Actividades",
                hole=0.4,
                color_discrete_sequence=CHART_SEQUENCE[:3],
            )
        )
        fig_sede.update_layout(height=300, showlegend=True)
        st.plotly_chart(fig_sede, use_container_width=True)

with tab_evol:
    st.dataframe(planilla_evolucion_anual_df(), hide_index=True, use_container_width=True)

with tab_det:
    st.dataframe(planilla_unidades_df(data), hide_index=True, use_container_width=True)

st.divider()
st.subheader("Funciones sustantivas por sede")

tabs = st.tabs(["Docencia", "Investigación", "Extensión"])

with tabs[0]:
    m = funcion_metricas("Docencia", data)
    d1, d2, d3 = st.columns(3)
    d1.metric("Alumnos (total)", f"{m['alumnos']:,}".replace(",", "."))
    d2.metric("Docentes (total)", m["docentes"])
    d3.metric("Alumnos por docente", m["ratio_alumnos_docente"])
    por = m["por_sede"].rename(
        columns={"sede": "Sede", "alumnos": "Alumnos", "docentes": "Docentes"}
    )
    por["Alumnos / docente"] = (por["Alumnos"] / por["Docentes"]).round(1)
    st.dataframe(por, hide_index=True, use_container_width=True)

with tabs[1]:
    m = funcion_metricas("Investigación", data)
    i1, i2, i3 = st.columns(3)
    i1.metric("Investigadores", m["investigadores"])
    i2.metric("Actividades en investigación", m["actividades"])
    i3.metric("Actividades / investigador", m["actividades_por_investigador"])
    por = m["por_sede"].copy()
    por["Actividades / investigador"] = (por["actividades"] / por["investigadores"]).round(2)
    st.dataframe(
        por.rename(
            columns={
                "sede": "Sede",
                "investigadores": "Investigadores",
                "actividades": "Actividades científicas",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

with tabs[2]:
    m = funcion_metricas("Extensión", data)
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Convenios firmados", m["convenios"])
    e2.metric("Actividades de extensión", m["extension"])
    e3.metric("Voluntariado y comunidad", m["voluntariado"])
    e4.metric("Actividades en el plan", m["actividades_plan"])
    st.dataframe(
        m["por_sede"].rename(columns={"sede": "Sede", "actividades": "Actividades de extensión"}),
        hide_index=True,
        use_container_width=True,
    )

for alerta in data["alertas"]:
    fn = st.warning if alerta["nivel"] == "atencion" else st.info
    fn(f"**{alerta['titulo']}** — {alerta['detalle']}")
