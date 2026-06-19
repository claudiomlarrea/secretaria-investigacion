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

from lib.pei_consistencia import (
    actividades_consistencia_df,
    indice_consistencia_general,
    indice_consistencia_por_objetivo_df,
)
from lib.pei_sheets import resumen_conteos_planilla
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
suma_unicas_og = int(data.get("suma_actividades_unicas_og", int(base["actividades"].sum())))
conteos_planilla = resumen_conteos_planilla(anio_base)
funciones = funciones_df(data)

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Formularios del plan",
    total_base,
    help="Filas en la planilla del año (1 registro = 1 formulario cargado). Coincide con Looker Studio.",
)
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
st.subheader(f"Consistencia actividad–objetivo ({anio_base})")

st.markdown(
    "Mide qué tan relacionado está el **texto de cada actividad** con el **objetivo específico** "
    "bajo el cual fue cargada en la planilla (similitud textual TF-IDF + solapamiento de términos). "
    "El índice va de **0 a 100** (100 = máxima coherencia observada en el año).\n\n"
    f"**{conteos_planilla['formularios']} formularios** en {anio_base} (total del plan). "
    f"Acá se analizan **{conteos_planilla['cargas_actividad_og']} cargas actividad–objetivo** "
    "(todas las celdas con actividad; el índice se calcula sobre cada una). "
    "En las tablas por OG, **Act. distintas** coincide con el cuadro *Punto de partida* "
    "(nombres únicos, alineado a Looker); **Cargas** incluye nombres repetidos en formularios distintos."
)

try:
    indice_consistencia = indice_consistencia_general(anio_base)
    consistencia_og = indice_consistencia_por_objetivo_df(anio_base)
    detalle_consistencia = actividades_consistencia_df(anio_base)

    ic1, ic2, ic3 = st.columns(3)
    ic1.metric("Índice general de consistencia", f"{indice_consistencia:.1f}")
    ic2.metric(
        "Cargas actividad–objetivo",
        conteos_planilla["cargas_actividad_og"],
        help=(
            f"Celdas con actividad en OG1–OG6 ({conteos_planilla['cargas_actividad_og']}). "
            f"No es el total de formularios ({conteos_planilla['formularios']})."
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
            [
                "og",
                "objetivo_general",
                "indice_consistencia",
                "actividades_distintas",
                "cargas_analizadas",
            ]
        ].rename(
            columns={
                "og": "OG",
                "objetivo_general": "Objetivo general",
                "indice_consistencia": "Índice",
                "actividades_distintas": "Act. distintas",
                "cargas_analizadas": "Cargas",
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

variacion_base = objetivos_variacion_anual_df(anio_base)
prev_anio = anio_anterior(anio_base)
delta_total = delta_actividades_anio(anio_base)

if prev_anio:
    st.markdown(
        f"Actividades reales del PEI en **{anio_base}**. "
        f"**Escala de color:** rojo (menor volumen ese año) → verde (mayor volumen). "
        f"Las columnas de **{prev_anio}** son referencia; la simulación parte del año base.\n\n"
        f"**{total_base} formularios** en el plan. **Act. distintas** cuenta nombres únicos "
        f"por OG (suma {suma_unicas_og}, alineado a Looker). Un formulario puede cargar "
        f"actividad en varios objetivos."
    )
else:
    st.markdown(
        f"Actividades reales del PEI en **{anio_base}** (primer año disponible en la planilla). "
        f"**Escala de color:** rojo (menor volumen) → verde (mayor volumen).\n\n"
        f"**{total_base} formularios** en el plan. **Act. distintas** cuenta nombres únicos "
        f"por OG (suma {suma_unicas_og}, alineado a Looker)."
    )

b1, b2, b3 = st.columns(3)
b1.metric(f"Formularios {anio_base}", total_base)
b2.metric(
    f"Actividades distintas (suma OG)",
    suma_unicas_og,
    help="Suma de actividades únicas en OG1–OG6; puede superar el total de formularios.",
)
b3.metric(
    f"Δ total vs {prev_anio}" if prev_anio else "Δ vs año anterior",
    "—" if delta_total is None else delta_total,
)

tabla_punto = variacion_base[["id", "nombre", "actividades", "pct"]].copy()
if prev_anio:
    tabla_punto["actividades_anterior"] = variacion_base["actividades_anterior"]
    tabla_punto["delta_anterior"] = variacion_base["delta_anterior"]

rename_punto = {
    "id": "OG",
    "nombre": "Objetivo general",
    "actividades": f"Act. distintas {anio_base}",
    "pct": "% del plan",
}
if prev_anio:
    rename_punto["actividades_anterior"] = f"Act. {prev_anio}"
    rename_punto["delta_anterior"] = "Δ vs año ant."

tabla_punto = tabla_punto.rename(columns=rename_punto)
col_act = f"Act. distintas {anio_base}"
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
                f"OG{og_id} · {int(row['actividades'])} act. base{tendencia}",
                min_value=50.0,
                max_value=200.0,
                value=100.0,
                step=5.0,
                format="%.0f%%",
                help=(
                    f"Memoria {anio_base}: {int(row['actividades'])} actividades ({row['pct']}%). "
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
impacto = simular_impacto_funciones(sim, data, solo_incrementos=True)
contrib = contribucion_objetivo_funcion(sim, data)
metricas_por_fn = metricas_operativas_por_funcion(impacto, data)

metric_sim.metric(
    "Actividades simuladas (suma OG)",
    total_sim,
    delta=total_sim - suma_unicas_og,
    help="Suma de actividades simuladas por OG; referencia base = actividades distintas por objetivo.",
)

og2_nivel = niveles_og[1]
og2_act_base = int(base.loc[base["id"] == 2, "actividades"].iloc[0])
og2_act_sim = int(sim.loc[sim["id"] == 2, "actividades_sim"].iloc[0])
ext_imp = impacto.loc[impacto["funcion"] == "Extensión"].iloc[0]
inv_imp = impacto.loc[impacto["funcion"] == "Investigación"].iloc[0]
conv = next(f for f in metricas_por_fn["Extensión"] if f["indicador"] == "Convenios firmados")

st.caption(
    f"Total simulado: **{total_sim}** actividades distintas por OG (base {suma_unicas_og} · "
    f"{total_base} formularios). "
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
