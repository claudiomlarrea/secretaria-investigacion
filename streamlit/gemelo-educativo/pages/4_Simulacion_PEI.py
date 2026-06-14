# -*- coding: utf-8 -*-
import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.pei_model import indice_equilibrio, load_baseline, objetivos_df, simular_distribucion
from lib.styles import render_header, setup_page

setup_page("Simulación PEI", "⚖️")
render_header("Simulación estratégica · escenarios what-if PEI")

data = load_baseline()
base = objetivos_df(data)
total = data["total_actividades"]

st.markdown(
    "Ajustá la **prioridad relativa** de cada objetivo y el gemelo recalcula cómo quedaría "
    f"la distribución de las **{total} actividades** institucionales."
)

st.subheader("Prioridades estratégicas (pesos relativos)")
pesos = []
cols = st.columns(3)
for i, row in base.iterrows():
    with cols[i % 3]:
        pesos.append(
            st.slider(
                f"OG{int(row['id'])} · {row['nombre'][:28]}…",
                min_value=1,
                max_value=100,
                value=max(1, int(row["pct"])),
                key=f"og_{row['id']}",
            )
        )

sim = simular_distribucion(pesos, total=total)

c1, c2, c3 = st.columns(3)
c1.metric("Índice equilibrio actual", indice_equilibrio(base["pct"].tolist()))
c2.metric("Índice equilibrio simulado", indice_equilibrio(sim["pct_sim"].tolist()))
c3.metric("Mayor cambio", f"OG{int(sim.loc[sim['delta_pct'].abs().idxmax(), 'id'])}")

left, right = st.columns(2)

with left:
    fig = px.bar(
        sim,
        x="id",
        y=["pct", "pct_sim"],
        barmode="group",
        labels={"value": "%", "id": "Objetivo", "variable": "Escenario"},
        color_discrete_map={"pct": "#7a1532", "pct_sim": "#0d6e4f"},
    )
    fig.for_each_trace(lambda t: t.update(name="2025 real" if t.name == "pct" else "Simulado"))
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Cambios por objetivo")
    st.dataframe(
        sim[["id", "nombre", "pct", "pct_sim", "delta_pct"]].rename(
            columns={
                "id": "OG",
                "pct": "% 2025",
                "pct_sim": "% simulado",
                "delta_pct": "Δ puntos",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

preset = st.radio(
    "Escenarios rápidos",
    ["Personalizado", "Reequilibrar OG3/4/6", "Mantener foco vinculación (OG2)"],
    horizontal=True,
)

if preset == "Reequilibrar OG3/4/6":
    st.success(
        "Escenario sugerido: subir Educación a distancia, RR.HH. e identidad institucional "
        "sin reducir por debajo del 15 % la calidad (OG1) ni la participación (OG5)."
    )
elif preset == "Mantener foco vinculación (OG2)":
    st.warning(
        "Escenario conservador: mantiene la lógica 2025 donde OG2 concentra más del 50 % "
        "de las actividades institucionales."
    )

st.caption(
    "Simulación ilustrativa para conversaciones de planificación. No modifica el PEI real "
    "hasta integrar el Formulario Único institucional."
)
