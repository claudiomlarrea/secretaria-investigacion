# -*- coding: utf-8 -*-
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.pei_model import etiqueta_transversalidad, load_baseline, unidades_df
from lib.styles import render_header, setup_page

setup_page("Vista Decanato", "🎯")
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

st.markdown(f"**Posición institucional:** {pos}ª de {len(rank)} unidades modeladas · **Sede:** {row['sede']}")

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
    st.subheader("Radar comparativo (demo)")
    radar = pd.DataFrame(
        {
            "indicador": ["Intensidad", "Transversalidad", "Vinculación", "Investigación", "Extensión"],
            "unidad": [min(100, row["actividades"] / promedio * 50)] * 5,
            "institución": [50, prom_trans * 33, 48, 42, 46],
        }
    )
    st.dataframe(
        pd.DataFrame(
            {
                "Indicador": radar["indicador"],
                "Tu unidad (índice)": radar["unidad"],
                "Promedio UCCuyo": radar["institución"],
            }
        ),
        hide_index=True,
        use_container_width=True,
    )
    st.caption("En la versión completa, estos índices se calculan desde el Formulario Único PEI por unidad.")

st.subheader("Todas las unidades")
st.dataframe(
    rank[["posicion", "unidad", "sede", "actividades", "transversalidad"]],
    hide_index=True,
    use_container_width=True,
)

st.warning(
    f"**Para decanos:** {sel.split('-')[0].strip()} registra {int(row['actividades'])} actividades. "
    "Usá esta vista en reuniones de decanato para comparar intensidad y transversalidad con el resto de la universidad."
)
