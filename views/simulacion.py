# -*- coding: utf-8 -*-
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "_path.py"))

import plotly.express as px
import streamlit as st

from lib.pei_model import indice_equilibrio, load_baseline, objetivos_df, simular_distribucion
from lib.styles import render_header

render_header("Simulación estratégica · escenarios what-if PEI")

data = load_baseline()
base = objetivos_df(data)
total = data["total_actividades"]

st.markdown(
    "Ajustá la **prioridad relativa** de cada objetivo y el **Gemelo Digital Plan Institucional** "
    f"recalcula la distribución de las **{total} actividades**."
)

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

st.caption("Simulación ilustrativa · Gemelo Digital Plan Institucional")
