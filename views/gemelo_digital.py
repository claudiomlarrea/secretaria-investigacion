# -*- coding: utf-8 -*-
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "_path.py"))

import plotly.express as px
import streamlit as st

from lib.pei_model import (
    ANIOS_DISPONIBLES,
    funciones_df,
    indice_equilibrio,
    load_baseline,
    objetivos_df,
    sedes_df,
    simular_distribucion,
)
from lib.styles import apply_plotly_style, render_header
from ui_theme import CHART_SEQUENCE, GREEN, GREEN_MID, ORANGE

render_header(
    "Réplica digital del plan institucional para simular escenarios de redistribución "
    "estratégica entre objetivos generales y funciones sustantivas."
)

anio_base = st.sidebar.selectbox("Año base", ANIOS_DISPONIBLES, index=ANIOS_DISPONIBLES.index(2025))
data = load_baseline(anio_base)
base = objetivos_df(data)
total = data["total_actividades"]
funciones = funciones_df(data)

c1, c2, c3 = st.columns(3)
c1.metric("Actividades base", total)
c2.metric("Índice de equilibrio actual", indice_equilibrio(base["pct"].tolist()))
c3.metric("Sedes modeladas", len(data["sedes"]))

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
    fig_fun = apply_plotly_style(
        px.bar(
            funciones,
            x="funcion",
            y="actividades_plan",
            text="actividades_plan",
            title="Actividades por función sustantiva",
            labels={"actividades_plan": "Actividades", "funcion": ""},
            color="funcion",
            color_discrete_map={
                "Docencia": GREEN,
                "Investigación": GREEN_MID,
                "Extensión": ORANGE,
            },
        )
    )
    fig_fun.update_layout(showlegend=False, height=340)
    st.plotly_chart(fig_fun, use_container_width=True)

st.divider()
st.subheader("Simulación: redistribución por objetivo")

st.markdown(
    f"Ajustá la prioridad relativa de cada objetivo. El gemelo recalcula las **{total} actividades** "
    f"como si el plan {anio_base} hubiera tenido otra distribución estratégica."
)

pesos = []
cols = st.columns(3)
for i, row in base.iterrows():
    with cols[i % 3]:
        pesos.append(
            st.slider(
                f"OG{int(row['id'])}",
                min_value=1,
                max_value=100,
                value=max(1, int(row["pct"])),
                key=f"sim_og_{row['id']}",
            )
        )

sim = simular_distribucion(pesos, total=total)

s1, s2, s3 = st.columns(3)
s1.metric("Equilibrio simulado", indice_equilibrio(sim["pct_sim"].tolist()))
s2.metric(
    "Cambio mayor",
    f"OG{int(sim.loc[sim['delta_pct'].abs().idxmax(), 'id'])} ({sim['delta_pct'].abs().max():+.1f} pp)",
)
s3.metric("OG2 simulado", f"{sim.loc[sim['id'] == 2, 'pct_sim'].iloc[0]} %")

fig = apply_plotly_style(
    px.bar(
        sim,
        x="id",
        y=["pct", "pct_sim"],
        barmode="group",
        labels={"value": "%", "id": "Objetivo", "variable": "Escenario"},
        color_discrete_map={"pct": GREEN, "pct_sim": GREEN_MID},
    )
)
fig.for_each_trace(lambda t: t.update(name=f"{anio_base} real" if t.name == "pct" else "Simulado"))
fig.update_layout(height=380)
st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    sim[["id", "nombre", "pct", "pct_sim", "delta_pct"]].rename(
        columns={"id": "OG", "pct": "% real", "pct_sim": "% simulado", "delta_pct": "Δ puntos"}
    ),
    hide_index=True,
    use_container_width=True,
)

st.caption("Simulación ilustrativa · Observatorio de Inteligencia Artificial · UCCuyo")
