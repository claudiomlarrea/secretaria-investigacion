# -*- coding: utf-8 -*-
"""Formulario compartido de autodiagnóstico MDeIA UCCuyo."""

from __future__ import annotations

import html
from typing import Any

import pandas as pd
import streamlit as st


_NIVEL_SLIDER = {
    0: "No implementado",
    1: "Inicial",
    2: "En desarrollo",
    3: "Implementado",
    4: "Optimizado",
}


def render_encuesta(
    df_ind: pd.DataFrame,
    respuestas: dict[str, Any],
    niveles: dict[int, str],
    *,
    agrupar_por: str = "objetivo_num",
    titulo_grupo_fn=None,
    ambito_unidad_id: str | None = None,
) -> None:
    """Renderiza controles de encuesta y actualiza respuestas en session_state."""
    from lib.unidades import texto_indicador_para_ambito

    if df_ind.empty:
        st.warning("No hay indicadores para mostrar con los filtros actuales.")
        return

    grupos = df_ind.groupby(agrupar_por, dropna=False)
    for key, grupo in grupos:
        if titulo_grupo_fn:
            titulo = titulo_grupo_fn(key, grupo)
        else:
            titulo = grupo.iloc[0].get("objetivo_nombre") or "Extensión IA / transversal"
            titulo = f"Objetivo {key or '—'} · {titulo}"

        n_ok = sum(1 for c in grupo["codigo"] if c in respuestas)
        with st.expander(f"{titulo} ({n_ok}/{len(grupo)})", expanded=len(grupo) <= 6):
            grupo_rows = list(grupo.iterrows())
            for idx, (_, row) in enumerate(grupo_rows):
                codigo = row["codigo"]
                tipo = row.get("tipo", "nivel")
                texto = str(row.get("texto", "")).strip()
                if ambito_unidad_id:
                    texto = texto_indicador_para_ambito(texto, ambito_unidad_id)
                st.markdown(
                    f'<div class="mdeia-indicador">'
                    f'<p class="mdeia-indicador-codigo"><code>{html.escape(codigo)}</code></p>'
                    f'<p class="mdeia-indicador-texto">{html.escape(texto)}</p>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
                if tipo == "si_no":
                    val = st.radio(
                        "Respuesta",
                        options=["No", "Sí"],
                        index=0 if respuestas.get(codigo) != "Sí" else 1,
                        key=f"mdeia_{codigo}",
                        horizontal=True,
                        label_visibility="collapsed",
                    )
                    respuestas[codigo] = val
                elif tipo in {"porcentaje", "umbral"}:
                    unidad = row.get("unidad") or "%"
                    default = float(respuestas.get(codigo, 0) or 0)
                    val = st.slider(
                        f"Valor ({unidad})",
                        min_value=0.0,
                        max_value=100.0,
                        value=default,
                        key=f"mdeia_{codigo}",
                        label_visibility="collapsed",
                    )
                    respuestas[codigo] = val
                else:
                    default = int(respuestas.get(codigo, 0) or 0)
                    val = st.select_slider(
                        "Nivel de madurez",
                        options=list(niveles.keys()),
                        format_func=lambda x, n=niveles: f"{x} — {_NIVEL_SLIDER.get(x, n[x])}",
                        value=default,
                        key=f"mdeia_{codigo}",
                        label_visibility="collapsed",
                    )
                    respuestas[codigo] = val
                if idx < len(grupo_rows) - 1:
                    st.markdown("---")
