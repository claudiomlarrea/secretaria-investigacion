# -*- coding: utf-8 -*-
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parent.parent
_GEMELO = _ROOT / "gemelo_digital_plan_institucional"
for _dir in (_GEMELO, _ROOT):
    _s = str(_dir)
    if _s not in sys.path:
        sys.path.insert(0, _s)

import pandas as pd
import plotly.express as px
import streamlit as st

from lib.pei_model import (
    ANIOS_DISPONIBLES,
    contribucion_objetivo_funcion,
    funciones_df,
    guia_por_indicador_df,
    guia_por_objetivo_df,
    indice_equilibrio,
    load_baseline,
    metricas_operativas_por_funcion,
    objetivos_df,
    sedes_df,
    simular_distribucion,
    simular_impacto_funciones,
)
from lib.styles import apply_plotly_style, render_header
from ui_theme import CHART_SEQUENCE, GREEN, GREEN_MID, estilizar_variacion_tabla

render_header(
    "Réplica digital del plan institucional para simular escenarios de redistribución "
    "estratégica entre objetivos generales y funciones sustantivas."
)

anio_base = st.sidebar.selectbox("Año base", ANIOS_DISPONIBLES, index=ANIOS_DISPONIBLES.index(2025))
if st.sidebar.button("Actualizar planilla", help="Vuelve a leer la planilla Google Sheets."):
    from lib.pei_sheets import fetch_planilla_pei

    fetch_planilla_pei(force=True)
    st.rerun()

data = load_baseline(anio_base)
if data.get("fuente_url"):
    st.sidebar.markdown(f"[Planilla Google Sheets]({data['fuente_url']})")
base = objetivos_df(data)
total_base = data["total_actividades"]
funciones = funciones_df(data)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Actividades base", total_base)
metric_sim = c2.empty()
c3.metric("Índice de equilibrio actual", indice_equilibrio(base["pct"].tolist()))
c4.metric("Sedes modeladas", len(data["sedes"]))

st.subheader("Estado actual del gemelo")

left, right = st.columns(2)

with left:
    sede = sedes_df(data)
    fig_sede = apply_plotly_style(
        px.pie(
            sede,
            names="sede",
            values="actividades",
            hole=0.45,
            title="Actividades por sede",
            color_discrete_sequence=CHART_SEQUENCE[:3],
        )
    )
    fig_sede.update_layout(height=340)
    st.plotly_chart(fig_sede, use_container_width=True)

with right:
    st.dataframe(
        funciones[["funcion", "actividades_plan", "descripcion"]].rename(
            columns={
                "funcion": "Función",
                "actividades_plan": "Actividades en el plan",
                "descripcion": "Descripción",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

st.divider()
st.subheader("Qué objetivo impulsa qué indicador")

st.markdown(
    "Referencia para interpretar la simulación. Al **subir el peso** de un objetivo general "
    "en los controles de abajo, crecen los indicadores vinculados según la matriz del PEI."
)

guia_tabs = st.tabs(["Por indicador", "Por objetivo general (OG)"])

with guia_tabs[0]:
    st.caption(
        "Indicadores operativos (proyectados en la simulación) y temáticas del plan "
        "(calidad, identidad católica, educación a distancia, etc.)."
    )
    st.dataframe(guia_por_indicador_df(data), hide_index=True, use_container_width=True)

with guia_tabs[1]:
    st.caption("Resumen de cada uno de los seis objetivos generales del PEI 2023–2027.")
    st.dataframe(guia_por_objetivo_df(data), hide_index=True, use_container_width=True)

st.divider()
st.subheader("Simulación: crecimiento por objetivo")

st.markdown(
    f"Cada control indica el **nivel de actividades** de ese objetivo respecto de la Memoria Académica "
    f"**{anio_base}** (100 = sin cambio). Al **subir OG2**, crecen extensión y convenios. "
    f"**Las demás funciones no se reducen** automáticamente al priorizar un objetivo."
)

_OG_AYUDA = {
    1: "Calidad académica · impulsa docencia e investigación.",
    2: "Vinculación y convenios · principal impulsor de extensión (80% de sus actividades).",
    3: "Educación a distancia · impulsa alumnos y docentes.",
    4: "Recursos humanos · docentes e investigadores.",
    5: "Participación estudiantil · extensión y vinculación.",
    6: "Identidad católica e institucional · extensión y compromiso social.",
}

niveles_og: list[float] = []
cols = st.columns(3)
for i, row in base.iterrows():
    og_id = int(row["id"])
    with cols[i % 3]:
        niveles_og.append(
            st.slider(
                f"OG{og_id} · {int(row['actividades'])} act. base",
                min_value=50.0,
                max_value=200.0,
                value=100.0,
                step=5.0,
                format="%.0f%%",
                help=(
                    f"Memoria {anio_base}: {int(row['actividades'])} actividades ({row['pct']}%). "
                    f"100 % = mantener; 150 % = +50 % de actividades en este objetivo. "
                    f"{_OG_AYUDA.get(og_id, '')}"
                ),
                key=f"sim_og_{og_id}",
            )
        )

sim = simular_distribucion(niveles_og, data=data, en_porcentaje=True, modo="crecimiento")
total_sim = int(sim["actividades_sim"].sum())
impacto = simular_impacto_funciones(sim, data, solo_incrementos=True)
contrib = contribucion_objetivo_funcion(sim, data)
metricas_por_fn = metricas_operativas_por_funcion(impacto, data)

metric_sim.metric("Actividades simuladas", total_sim, delta=total_sim - total_base)

og2_nivel = niveles_og[1]
og2_act_base = int(base.loc[base["id"] == 2, "actividades"].iloc[0])
og2_act_sim = int(sim.loc[sim["id"] == 2, "actividades_sim"].iloc[0])
ext_imp = impacto.loc[impacto["funcion"] == "Extensión"].iloc[0]
inv_imp = impacto.loc[impacto["funcion"] == "Investigación"].iloc[0]
conv = next(f for f in metricas_por_fn["Extensión"] if f["indicador"] == "Convenios firmados")

st.caption(
    f"Total simulado: **{total_sim}** actividades (base {total_base}). "
    f"OG2: {og2_act_base} → **{og2_act_sim}** ({og2_nivel:.0f} % del nivel memoria)."
)

if og2_nivel > 100.5:
    st.success(
        f"OG2 ampliado al **{og2_nivel:.0f} %** del nivel memoria: extensión "
        f"**{ext_imp['actividades_base']} → {ext_imp['actividades_sim']}** "
        f"({ext_imp['delta']:+d}). Investigación: **{inv_imp['actividades_base']} → "
        f"{inv_imp['actividades_sim']}** ({inv_imp['delta']:+d}). "
        f"Convenios: **{conv['base']} → {conv['proyectado']}** ({conv['delta']:+d})."
    )
elif og2_nivel < 99.5:
    st.info(
        f"OG2 por debajo del 100 % ({og2_nivel:.0f} %): no se proyectan incrementos en extensión "
        f"respecto de la base (las demás funciones se mantienen)."
    )

s1, s2, s3 = st.columns(3)
s1.metric("Equilibrio simulado", indice_equilibrio(sim["pct_sim"].tolist()))
s2.metric(
    "Cambio mayor por objetivo",
    f"OG{int(sim.loc[sim['delta_pct'].abs().idxmax(), 'id'])} ({sim['delta_pct'].abs().max():+.1f} pp)",
)
s3.metric(
    "Función más afectada",
    f"{impacto.loc[impacto['delta'].abs().idxmax(), 'funcion']} ({impacto['delta'].abs().max():+d})",
)

tabla_objetivos = sim[
    ["id", "nombre", "actividades", "actividades_ref", "actividades_sim", "delta_actividades", "pct", "pct_sim", "delta_pct"]
].rename(
    columns={
        "id": "OG",
        "actividades": "Act. memoria PEI",
        "actividades_ref": "Act. referencia",
        "actividades_sim": "Act. simuladas",
        "delta_actividades": "Δ actividades",
        "pct": "% PEI",
        "pct_sim": "% simulado",
        "delta_pct": "Δ puntos",
    }
)
st.dataframe(
    estilizar_variacion_tabla(
        tabla_objetivos,
        columnas_delta=("Δ actividades", "Δ puntos"),
        columnas_vinculadas=(("Act. simuladas", "Δ actividades"), ("% simulado", "Δ puntos")),
    ),
    hide_index=True,
    use_container_width=True,
)

st.divider()
st.subheader("Impacto en funciones sustantivas")

st.markdown(
    "Cada cambio en los objetivos se traduce en más o menos actividades de **Docencia**, "
    "**Investigación** y **Extensión**, según la matriz de vinculación del PEI "
    "(p. ej. OG2 impulsa extensión y convenios; OG3 educación a distancia impulsa docencia)."
)

with st.expander("Cómo se calcula el impacto por función"):
    st.markdown(
        """
        - Cada objetivo se escala de forma **independiente** (% del nivel memoria PEI).
        - Solo los objetivos que **crecen** impulsan las funciones vinculadas (matriz del PEI).
        - **Reducir un objetivo no recorta** docencia, investigación ni extensión en otras áreas.
        - Los indicadores operativos (alumnos, investigadores, convenios) se proyectan de forma
          lineal según el crecimiento de cada función.
        - Es una **simulación ilustrativa** para conversar escenarios; no reemplaza el seguimiento real.
        """
    )
    matriz = data["matriz_objetivo_funcion"]
    matriz_df = pd.DataFrame(matriz).T
    matriz_df.index = [f"OG{i}" for i in matriz_df.index]
    st.dataframe(matriz_df.style.format("{:.0%}"), use_container_width=True)

f1, f2, f3 = st.columns(3)
for col, (_, row) in zip((f1, f2, f3), impacto.iterrows()):
    col.metric(
        row["funcion"],
        f"{row['actividades_sim']} actividades",
        delta=f"{row['delta']:+d} ({row['delta_pct']:+.1f} %)",
    )

impacto_long = impacto.melt(
    id_vars=["funcion"],
    value_vars=["actividades_base", "actividades_sim"],
    var_name="escenario",
    value_name="actividades",
)
impacto_long["escenario"] = impacto_long["escenario"].map(
    {"actividades_base": f"{anio_base} real", "actividades_sim": "Simulado"}
)

col_l, col_r = st.columns(2)

with col_l:
    fig_fun_sim = apply_plotly_style(
        px.bar(
            impacto_long,
            x="funcion",
            y="actividades",
            color="escenario",
            barmode="group",
            text="actividades",
            labels={"actividades": "Actividades en el plan", "funcion": ""},
            color_discrete_map={f"{anio_base} real": GREEN, "Simulado": GREEN_MID},
        )
    )
    fig_fun_sim.update_traces(textposition="outside")
    fig_fun_sim.update_layout(height=360, title="Actividades por función sustantiva")
    st.plotly_chart(fig_fun_sim, use_container_width=True)

with col_r:
    contrib_pivot = contrib.pivot_table(
        index="objetivo", columns="funcion", values="contribucion", aggfunc="sum", fill_value=0
    )
    fig_contrib = apply_plotly_style(
        px.imshow(
            contrib_pivot,
            text_auto=True,
            color_continuous_scale=["#E8F3EF", GREEN],
            labels=dict(x="Función", y="Objetivo", color="Δ actividades"),
            title="Contribución de cada objetivo al cambio por función",
        )
    )
    fig_contrib.update_layout(height=360)
    st.plotly_chart(fig_contrib, use_container_width=True)

st.subheader("Proyección de indicadores operativos")

tabs = st.tabs(["Docencia", "Investigación", "Extensión"])

for tab, funcion in zip(tabs, ("Docencia", "Investigación", "Extensión")):
    with tab:
        row_imp = impacto.loc[impacto["funcion"] == funcion].iloc[0]
        filas = metricas_por_fn[funcion]
        st.caption(
            next(f["descripcion"] for f in data["funciones_sustantivas"] if f["funcion"] == funcion)
        )
        mcols = st.columns(min(4, len(filas)))
        for col, fila in zip(mcols, filas):
            delta = fila["delta"]
            if isinstance(delta, float) and delta == int(delta):
                delta = int(delta)
            col.metric(fila["indicador"], fila["proyectado"], delta=delta if delta != 0 else None)

        st.info(
            f"Actividades del plan en **{funcion.lower()}**: "
            f"{row_imp['actividades_base']} → **{row_imp['actividades_sim']}** "
            f"({row_imp['delta']:+d}, {row_imp['delta_pct']:+.1f} %)."
        )

        resumen_tab = pd.DataFrame(filas).rename(
            columns={
                "indicador": "Indicador",
                "base": f"Base {anio_base}",
                "proyectado": "Simulado",
                "delta": "Δ",
            }
        )
        st.dataframe(
            estilizar_variacion_tabla(
                resumen_tab,
                columnas_delta=("Δ",),
                columnas_vinculadas=(("Simulado", "Δ"),),
            ),
            hide_index=True,
            use_container_width=True,
        )

st.markdown("**Resumen comparativo por función**")
filas_todas: list[dict] = []
for funcion in ("Docencia", "Investigación", "Extensión"):
    for fila in metricas_por_fn[funcion]:
        filas_todas.append({"Función": funcion, **fila})

resumen = (
    pd.DataFrame(filas_todas)
    .rename(
        columns={
            "indicador": "Indicador",
            "base": f"Base {anio_base}",
            "proyectado": "Simulado",
            "delta": "Δ",
        }
    )
    [["Función", "Indicador", f"Base {anio_base}", "Simulado", "Δ"]]
)
st.dataframe(
    estilizar_variacion_tabla(
        resumen,
        columnas_delta=("Δ",),
        columnas_vinculadas=(("Simulado", "Δ"),),
    ),
    hide_index=True,
    use_container_width=True,
    column_config={
        "Función": st.column_config.TextColumn("Función", width="small"),
        "Indicador": st.column_config.TextColumn("Indicador", width="large"),
    },
)

st.caption(
    "Act. referencia = Memoria Académica. Modo crecimiento: subir un objetivo amplía sus funciones "
    "vinculadas sin penalizar las demás. Δ = cambio respecto de la base (0 al iniciar con todos en 100 %)."
)
