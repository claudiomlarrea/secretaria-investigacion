# -*- coding: utf-8 -*-
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "_path.py"))

import pandas as pd
import plotly.express as px
import streamlit as st

from lib.pei_model import etiqueta_transversalidad, load_baseline, unidades_df
from lib.styles import render_header

render_header("Vista Decanato · benchmark por unidad académica")

data = load_baseline()
uni = unidades_df(data)
promedio = round(uni["actividades"].mean(), 1)
prom_trans = round(uni["transversalidad"].mean(), 2)

unidades = uni["unidad"].tolist()
sel = st.selectbox("Unidad académica", unidades, index=0)
row = uni[uni["unidad"] == sel].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Actividades 2025", int(row["actividades"]))
c2.metric("vs. promedio institucional", f"{row['actividades'] - promedio:+.1f}")
c3.metric("Transversalidad", f"{row['transversalidad']:.2f}")
c4.metric("Nivel", etiqueta_transversalidad(row["transversalidad"]).capitalize())

rank = uni.sort_values("actividades", ascending=False).reset_index(drop=True)
rank["posicion"] = range(1, len(rank) + 1)
pos = int(rank.loc[rank["unidad"] == sel, "posicion"].iloc[0])

st.markdown(f"**Posición institucional:** {pos}ª de {len(rank)} unidades · **Sede:** {row['sede']}")

left, right = st.columns([1.2, 1])

with left:
    st.subheader("Ranking de intensidad institucional")
    fig = px.bar(
        rank.head(12),
        x="actividades",
        y="unidad",
        orientation="h",
        color="sede",
        labels={"actividades": "Actividades", "unidad": ""},
    )
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Comparación con el promedio UCCuyo")
    st.dataframe(
        pd.DataFrame(
            {
                "Indicador": ["Intensidad", "Transversalidad", "Vinculación", "Investigación", "Extensión"],
                "Tu unidad (índice)": [min(100, row["actividades"] / promedio * 50)] * 5,
                "Promedio UCCuyo": [50, prom_trans * 33, 48, 42, 46],
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

st.dataframe(
    rank[["posicion", "unidad", "sede", "actividades", "transversalidad"]],
    hide_index=True,
    use_container_width=True,
)
