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
    alertas_para_anio,
    delta_actividades_anio,
    funcion_metricas,
    load_baseline,
    planilla_funciones_resumen_df,
    planilla_indicadores_institucionales_por_anio_df,
    planilla_objetivos_df,
    planilla_sedes_df,
    planilla_unidades_df,
)
from lib.styles import apply_plotly_style, render_header
from ui_theme import (
    CHART_SEQUENCE,
    GREEN,
    estilizar_escala_cantidad,
    estilizar_funciones_sustantivas,
    estilizar_variacion_tabla,
)


def _render_funciones_por_sede(data: dict, anio: int) -> None:
    st.markdown(f"##### Detalle por sede · {anio}")
    tabs = st.tabs(["Docencia", "Investigación", "Extensión"])

    with tabs[0]:
        m = funcion_metricas("Docencia", data)
        d1, d2, d3 = st.columns(3)
        d1.metric("Alumnos (total)", f"{m['alumnos']:,}".replace(",", "."))
        d2.metric("Docentes (total)", f"{m['docentes']:,}".replace(",", "."))
        d3.metric("Alumnos por docente", m["ratio_alumnos_docente"])
        por = m["por_sede"].rename(
            columns={"sede": "Sede", "alumnos": "Alumnos", "docentes": "Docentes"}
        )
        por["Alumnos / docente"] = (por["Alumnos"] / por["Docentes"]).round(1)
        st.dataframe(
            estilizar_escala_cantidad(
                por,
                ("Alumnos", "Docentes"),
                referencia_max={
                    "Alumnos": float(por["Alumnos"].max()),
                    "Docentes": float(por["Docentes"].max()),
                },
                referencia_min={
                    "Alumnos": float(por["Alumnos"].min()),
                    "Docentes": float(por["Docentes"].min()),
                },
                decimales=0,
            ),
            hide_index=True,
            use_container_width=True,
            key=f"doc_tabla_{anio}",
        )

    with tabs[1]:
        m = funcion_metricas("Investigación", data)
        i1, i2, i3 = st.columns(3)
        i1.metric("Investigadores", f"{m['investigadores']:,}".replace(",", "."))
        i2.metric("Actividades en investigación", f"{m['actividades']:,}".replace(",", "."))
        i3.metric("Actividades / investigador", m["actividades_por_investigador"])
        por = m["por_sede"].copy()
        por["Actividades / investigador"] = (por["actividades"] / por["investigadores"]).round(2)
        tabla = por.rename(
            columns={
                "sede": "Sede",
                "investigadores": "Investigadores",
                "actividades": "Actividades científicas",
            }
        )
        st.dataframe(
            estilizar_escala_cantidad(
                tabla,
                ("Investigadores", "Actividades científicas"),
                referencia_max={
                    "Investigadores": float(tabla["Investigadores"].max()),
                    "Actividades científicas": float(tabla["Actividades científicas"].max()),
                },
                referencia_min={
                    "Investigadores": float(tabla["Investigadores"].min()),
                    "Actividades científicas": float(tabla["Actividades científicas"].min()),
                },
                decimales=0,
            ),
            hide_index=True,
            use_container_width=True,
            key=f"inv_tabla_{anio}",
        )

    with tabs[2]:
        m = funcion_metricas("Extensión", data)
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Convenios firmados", m["convenios"])
        e2.metric("Actividades de extensión", f"{m['extension']:,}".replace(",", "."))
        e3.metric("Voluntariado y comunidad", m["voluntariado"])
        e4.metric("Actividades en el plan", f"{m['actividades_plan']:,}".replace(",", "."))
        por = m["por_sede"].rename(columns={"sede": "Sede", "actividades": "Actividades de extensión"})
        st.dataframe(
            estilizar_escala_cantidad(
                por,
                ("Actividades de extensión",),
                referencia_max=float(por["Actividades de extensión"].max()),
                referencia_min=float(por["Actividades de extensión"].min()),
                decimales=0,
            ),
            hide_index=True,
            use_container_width=True,
            key=f"ext_tabla_{anio}",
        )

render_header(
    "Actividades del Plan Estratégico Institucional por año, sede y función sustantiva "
    "(Docencia, Investigación y Extensión). Datos de referencia: Memoria Académica 2025."
)

anio = st.sidebar.selectbox("Año", ANIOS_DISPONIBLES, index=ANIOS_DISPONIBLES.index(2025))
if st.sidebar.button("Actualizar planilla", help="Vuelve a leer la planilla Google Sheets."):
    from lib.pei_sheets import fetch_planilla_pei

    fetch_planilla_pei(force=True)
    st.rerun()

data = load_baseline(anio)
if data.get("fuente_url"):
    st.sidebar.markdown(f"[Planilla Google Sheets]({data['fuente_url']})")

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Actividades del plan",
    data["total_actividades"],
    help="Formularios cargados en la planilla (mismo total que Looker Studio).",
)
c2.metric("Objetivos generales", len(data["objetivos"]))
c3.metric("Sedes", len(data["sedes"]))
c4.metric(
    "Únicas por objetivo (suma OG)",
    data.get("suma_actividades_unicas_og", sum(o["actividades"] for o in data["objetivos"])),
    help="Suma de actividades distintas en OG1–OG6; puede superar el total de formularios.",
)

st.subheader("Indicadores institucionales · serie histórica")
st.caption(
    "Total del plan = formularios del año (Looker: «Cantidad total de actividades»). "
    "Cada columna OG cuenta actividades únicas por objetivo (Looker: «Actividades Objetivo N»). "
    "Alumnos y docentes se estiman a partir de la memoria académica escalada al volumen del año."
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
st.caption(
    f"{data.get('fuente', 'Memoria Académica y análisis del PEI.')} "
    "Escala de color: rojo (menor), ámbar (intermedio) y verde (mayor). "
    f"Total del plan: {data['total_actividades']} formularios "
    f"({data.get('suma_actividades_unicas_og', sum(o['actividades'] for o in data['objetivos']))} "
    "actividades únicas sumando OG1–OG6)."
)

total_plan = int(data["total_actividades"])

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
    og = planilla_objetivos_df(data)
    st.dataframe(
        estilizar_escala_cantidad(
            og,
            ("Actividades", "% del plan"),
            referencia_max={"Actividades": float(og["Actividades"].max()), "% del plan": 100},
            referencia_min={"Actividades": float(og["Actividades"].min()), "% del plan": 0},
            decimales=1,
        ),
        hide_index=True,
        use_container_width=True,
        key=f"og_{anio}",
    )

with tab_fun:
    fun = planilla_funciones_resumen_df(data)
    st.caption(
        f"Indicadores institucionales del PEI para el año {anio}. "
        "Degradé verde: Docencia (intenso) → Investigación → Extensión (suave)."
    )
    st.dataframe(
        estilizar_funciones_sustantivas(fun),
        hide_index=True,
        use_container_width=True,
        key=f"fun_resumen_{anio}",
    )
    st.divider()
    _render_funciones_por_sede(data, anio)

with tab_sede:
    col_t1, col_t2 = st.columns([3, 2])
    with col_t1:
        sede = planilla_sedes_df(data)
        st.dataframe(
            estilizar_escala_cantidad(
                sede,
                ("Actividades", "% del plan"),
                referencia_max={
                    "Actividades": float(sede["Actividades"].max()),
                    "% del plan": 100,
                },
                referencia_min={
                    "Actividades": float(sede["Actividades"].min()),
                    "% del plan": 0,
                },
                decimales=1,
            ),
            hide_index=True,
            use_container_width=True,
            key=f"sede_{anio}",
        )
    with col_t2:
        fig_sede = apply_plotly_style(
            px.pie(
                sede,
                names="Sede",
                values="Actividades",
                hole=0.4,
                color_discrete_sequence=CHART_SEQUENCE[:3],
                title=f"Distribución por sede · {anio}",
            )
        )
        fig_sede.update_layout(height=300, showlegend=True, title_x=0.5)
        st.plotly_chart(fig_sede, use_container_width=True)

with tab_evol:
    delta = delta_actividades_anio(anio)
    e1, e2 = st.columns(2)
    e1.metric("Actividades del año seleccionado", data["total_actividades"])
    e2.metric("Δ vs año anterior", 0 if delta is None else delta)

    st.markdown(f"##### Desglose por objetivo general · {anio}")
    og_anio = planilla_objetivos_df(data)
    st.dataframe(
        estilizar_escala_cantidad(
            og_anio,
            ("Actividades", "% del plan"),
            referencia_max={
                "Actividades": float(og_anio["Actividades"].max()),
                "% del plan": 100,
            },
            referencia_min={
                "Actividades": float(og_anio["Actividades"].min()),
                "% del plan": 0,
            },
            decimales=1,
        ),
        hide_index=True,
        use_container_width=True,
        key=f"evol_og_{anio}",
    )

with tab_det:
    unidades = planilla_unidades_df(data)
    st.dataframe(
        estilizar_escala_cantidad(
            unidades,
            ("Actividades",),
            referencia_max=float(unidades["Actividades"].max()),
            referencia_min=float(unidades["Actividades"].min()),
            decimales=0,
        ),
        hide_index=True,
        use_container_width=True,
        key=f"det_{anio}",
    )

for alerta in alertas_para_anio(data):
    fn = st.warning if alerta["nivel"] == "atencion" else st.info
    fn(f"**{alerta['titulo']}** — {alerta['detalle']}")
