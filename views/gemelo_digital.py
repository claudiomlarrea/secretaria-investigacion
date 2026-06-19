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

from lib.pei_consistencia import consistencia_resumen
from lib.pei_sheets import leyenda_conteos_pei, resumen_conteos_planilla
from lib.pei_model import (
    ANIOS_DISPONIBLES,
    anio_anterior,
    contribucion_objetivo_funcion,
    delta_actividades_anio,
    funciones_df,
    guia_por_indicador_df,
    guia_por_objetivo_df,
    indice_equilibrio,
    load_baseline,
    metricas_operativas_por_funcion,
    objetivos_df,
    objetivos_variacion_anual_df,
    sedes_df,
    simular_distribucion,
    simular_impacto_funciones,
)
from lib.styles import apply_plotly_style, render_header
from ui_theme import CHART_SEQUENCE, GREEN, GREEN_MID, estilizar_escala_cantidad, estilizar_variacion_tabla

render_header(
    "Réplica digital del plan institucional para simular escenarios de redistribución "
    "estratégica entre objetivos generales y funciones sustantivas."
)


@st.cache_data(show_spinner=False)
def _baseline_cached(anio: int) -> dict:
    return load_baseline(anio)


@st.cache_data(show_spinner=False)
def _variacion_anual_cached(anio: int) -> pd.DataFrame:
    return objetivos_variacion_anual_df(anio)


@st.cache_data(show_spinner="Calculando consistencia actividad–objetivo…")
def _consistencia_cached(anio: int) -> tuple[float, pd.DataFrame, pd.DataFrame]:
    return consistencia_resumen(anio)

anio_base = st.sidebar.selectbox("Año base", ANIOS_DISPONIBLES, index=ANIOS_DISPONIBLES.index(2025))
if st.sidebar.button("Actualizar planilla", help="Vuelve a leer la planilla Google Sheets."):
    from lib.pei_sheets import fetch_planilla_pei

    fetch_planilla_pei(force=True)
    _baseline_cached.clear()
    _variacion_anual_cached.clear()
    _consistencia_cached.clear()
    st.rerun()

data = _baseline_cached(anio_base)
if data.get("fuente_url"):
    st.sidebar.markdown(f"[Planilla Google Sheets]({data['fuente_url']})")
base = objetivos_df(data)
total_base = data["total_actividades"]
suma_unicas_og = int(data.get("suma_actividades_unicas_og", int(base["actividades"].sum())))
conteos_planilla = resumen_conteos_planilla(anio_base)
funciones = funciones_df(data)

c1, c2, c3 = st.columns(3)
c1.metric(
    "Formularios del plan",
    total_base,
    help="Filas en la planilla del año (1 registro = 1 formulario cargado). Coincide con Looker Studio.",
)
c2.metric("Índice de equilibrio actual", indice_equilibrio(base["pct"].tolist()))
c3.metric("Sedes modeladas", len(data["sedes"]))

st.info(leyenda_conteos_pei(anio_base))

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
            title="Formularios por sede",
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
st.subheader(f"Consistencia actividad–objetivo ({anio_base})")

st.markdown(
    "Mide qué tan relacionado está el **texto de cada actividad** con el **objetivo específico** "
    "bajo el cual fue cargada (similitud TF-IDF + términos en común). "
    "Índice **0–100** (100 = máxima coherencia del año). "
    f"El cálculo usa los **{conteos_planilla['cargas_actividad_og']} registros** en columnas OG "
    f"(ver leyenda arriba); la columna **Actividades** por OG coincide con *Punto de partida*."
)

try:
    indice_consistencia, consistencia_og, detalle_consistencia = _consistencia_cached(anio_base)

    ic1, ic2, ic3 = st.columns(3)
    ic1.metric("Índice general de consistencia", f"{indice_consistencia:.1f}")
    ic2.metric(
        "Registros evaluados",
        conteos_planilla["cargas_actividad_og"],
        help=(
            f"Total de celdas con actividad en OG1–OG6. "
            f"Incluye {conteos_planilla['registros_extra']} declaraciones adicionales "
            f"respecto de {conteos_planilla['formularios']} formularios."
        ),
    )
    ic3.metric(
        "Objetivo más consistente",
        consistencia_og.loc[consistencia_og["indice_consistencia"].idxmax(), "og"]
        if not consistencia_og.empty
        else "—",
    )

    col_cons_l, col_cons_r = st.columns([3, 2])
    with col_cons_l:
        tabla_cons = consistencia_og[
            ["og", "objetivo_general", "indice_consistencia", "actividades_distintas"]
        ].rename(
            columns={
                "og": "OG",
                "objetivo_general": "Objetivo general",
                "indice_consistencia": "Índice",
                "actividades_distintas": "Actividades",
            }
        )
        st.dataframe(
            estilizar_escala_cantidad(
                tabla_cons,
                ("Índice",),
                referencia_max=float(tabla_cons["Índice"].max()) if not tabla_cons.empty else 100,
                referencia_min=0.0,
                decimales=1,
            ),
            hide_index=True,
            use_container_width=True,
        )
    with col_cons_r:
        fig_cons = apply_plotly_style(
            px.bar(
                consistencia_og,
                x="og",
                y="indice_consistencia",
                text="indice_consistencia",
                labels={"og": "Objetivo", "indice_consistencia": "Índice de consistencia"},
                title="Consistencia por objetivo general",
                color_discrete_sequence=[GREEN],
            )
        )
        fig_cons.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig_cons.update_layout(height=340, yaxis_range=[0, 100])
        st.plotly_chart(fig_cons, use_container_width=True)

    with st.expander("Ver actividades con mayor y menor consistencia"):
        if detalle_consistencia.empty:
            st.caption("No hay actividades para analizar en este año.")
        else:
            cols_det = st.columns(2)
            top = detalle_consistencia.nlargest(8, "consistencia")[
                ["og", "actividad", "objetivo_especifico", "consistencia", "coincidencias"]
            ].rename(
                columns={
                    "og": "OG",
                    "actividad": "Actividad",
                    "objetivo_especifico": "Objetivo específico",
                    "consistencia": "Índice",
                    "coincidencias": "Términos en común",
                }
            )
            low = detalle_consistencia.nsmallest(8, "consistencia")[
                ["og", "actividad", "objetivo_especifico", "consistencia"]
            ].rename(
                columns={
                    "og": "OG",
                    "actividad": "Actividad",
                    "objetivo_especifico": "Objetivo específico",
                    "consistencia": "Índice",
                }
            )
            cols_det[0].markdown("**Mayor consistencia**")
            cols_det[0].dataframe(top, hide_index=True, use_container_width=True)
            cols_det[1].markdown("**Menor consistencia**")
            cols_det[1].dataframe(low, hide_index=True, use_container_width=True)
except Exception as exc:
    st.info(
        "El índice de consistencia requiere la planilla Google Sheets con actividades y "
        f"objetivos específicos. Detalle: {exc}"
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
st.subheader(f"Punto de partida · objetivos generales ({anio_base})")

variacion_base = _variacion_anual_cached(anio_base)
prev_anio = anio_anterior(anio_base)
delta_total = delta_actividades_anio(anio_base)

if prev_anio:
    st.markdown(
        f"Distribución por objetivo en **{anio_base}**. "
        f"**Escala de color:** rojo (menor volumen) → verde (mayor volumen). "
        f"Referencia **{prev_anio}** en columnas comparativas."
    )
else:
    st.markdown(
        f"Distribución por objetivo en **{anio_base}** (primer año en la planilla). "
        f"**Escala de color:** rojo (menor volumen) → verde (mayor volumen)."
    )

b1, b2 = st.columns(2)
b1.metric(f"Formularios {anio_base}", total_base)
b2.metric(
    f"Δ formularios vs {prev_anio}" if prev_anio else "Δ vs año anterior",
    "—" if delta_total is None else delta_total,
)

tabla_punto = variacion_base[["id", "nombre", "actividades", "pct"]].copy()
if prev_anio:
    tabla_punto["actividades_anterior"] = variacion_base["actividades_anterior"]
    tabla_punto["delta_anterior"] = variacion_base["delta_anterior"]

rename_punto = {
    "id": "OG",
    "nombre": "Objetivo general",
    "actividades": "Actividades",
    "pct": "% del plan",
}
if prev_anio:
    rename_punto["actividades_anterior"] = f"Act. {prev_anio}"
    rename_punto["delta_anterior"] = "Δ vs año ant."

tabla_punto = tabla_punto.rename(columns=rename_punto)
col_act = "Actividades"
estilo_base = estilizar_escala_cantidad(
    tabla_punto,
    (col_act, "% del plan"),
    referencia_max={
        col_act: float(tabla_punto[col_act].max()),
        "% del plan": 100.0,
    },
    referencia_min={
        col_act: float(tabla_punto[col_act].min()),
        "% del plan": 0.0,
    },
    decimales=0,
)

st.dataframe(
    estilo_base,
    hide_index=True,
    use_container_width=True,
)

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
variacion_por_og = variacion_base.set_index("id")
for i, row in base.iterrows():
    og_id = int(row["id"])
    var = variacion_por_og.loc[og_id]
    delta_prev = int(var["delta_anterior"])
    if prev_anio and delta_prev > 0:
        tendencia = f" · ↑ {delta_prev:+d} vs {prev_anio}"
    elif prev_anio and delta_prev < 0:
        tendencia = f" · ↓ {delta_prev:+d} vs {prev_anio}"
    else:
        tendencia = ""
    with cols[i % 3]:
        niveles_og.append(
            st.slider(
                f"OG{og_id} · {int(row['actividades'])} act. · {int(row['pct'])} % del plan{tendencia}",
                min_value=50.0,
                max_value=200.0,
                value=100.0,
                step=5.0,
                format="%.0f%%",
                help=(
                    f"Memoria {anio_base}: {int(row['actividades'])} actividades distintas ({row['pct']} % del plan). "
                    + (
                        f"Vs {prev_anio}: {delta_prev:+d} actividades ({var['delta_pct_anterior']:+.1f} %). "
                        if prev_anio
                        else ""
                    )
                    + f"100 % = mantener; 150 % = +50 % de actividades en este objetivo. "
                    f"{_OG_AYUDA.get(og_id, '')}"
                ),
                key=f"sim_og_{og_id}",
            )
        )

sim = simular_distribucion(niveles_og, data=data, en_porcentaje=True, modo="crecimiento")
total_sim = int(sim["actividades_sim"].sum())
delta_sim_og = total_sim - suma_unicas_og
impacto = simular_impacto_funciones(sim, data, solo_incrementos=True)
contrib = contribucion_objetivo_funcion(sim, data)
metricas_por_fn = metricas_operativas_por_funcion(impacto, data)

if delta_sim_og == 0:
    st.caption(
        f"Escenario base: todos los objetivos al **100 %** de {anio_base} "
        f"({total_base} formularios). Mové un control para simular cambios."
    )
else:
    st.caption(
        f"Cambio simulado: **{delta_sim_og:+d}** actividades distintas en total por OG "
        f"(respecto del reparto base de {anio_base}). Formularios del plan: **{total_base}**."
    )

og2_nivel = niveles_og[1]
og2_act_base = int(base.loc[base["id"] == 2, "actividades"].iloc[0])
og2_act_sim = int(sim.loc[sim["id"] == 2, "actividades_sim"].iloc[0])
ext_imp = impacto.loc[impacto["funcion"] == "Extensión"].iloc[0]
inv_imp = impacto.loc[impacto["funcion"] == "Investigación"].iloc[0]
conv = next(f for f in metricas_por_fn["Extensión"] if f["indicador"] == "Convenios firmados")

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
    "Función con mayor incremento",
    f"{impacto.loc[impacto['delta'].abs().idxmax(), 'funcion']} ({impacto['delta'].abs().max():+d})",
    help=(
        "Función sustantiva donde la simulación proyecta más actividades adicionales "
        "(p. ej. subir OG3 impulsa principalmente docencia)."
    ),
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
