# -*- coding: utf-8 -*-
"""Formulario compartido de autodiagnóstico MDeIA UCCuyo."""

from __future__ import annotations

import html
from typing import Any

import pandas as pd
import streamlit as st

from lib.unidades import widget_key_respuesta
from lib.texto_legible import leyenda_siglas_markdown, legibilizar_siglas_udigital

_NIVEL_SLIDER = {
    0: "No implementado",
    1: "Inicial",
    2: "En desarrollo",
    3: "Implementado",
    4: "Optimizado",
}


def _init_widget_desde_respuesta(
    widget_key: str,
    codigo: str,
    respuestas: dict[str, Any],
) -> bool:
    """Prepara session_state; devuelve True si hay respuesta guardada."""
    if codigo in respuestas:
        st.session_state[widget_key] = respuestas[codigo]
        return True
    st.session_state.pop(widget_key, None)
    return False


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

    st.info(leyenda_siglas_markdown())

    grupos = df_ind.groupby(agrupar_por, dropna=False)
    for key, grupo in grupos:
        if titulo_grupo_fn:
            titulo = titulo_grupo_fn(key, grupo)
        else:
            titulo = grupo.iloc[0].get("objetivo_nombre") or "Extensión IA / transversal"
            titulo = f"Objetivo {key or '—'} · {titulo}"

        n_ok = sum(1 for c in grupo["codigo"] if c in respuestas)
        with st.expander(f"{titulo} ({n_ok}/{len(grupo)})", expanded=len(grupo) <= 6):
            st.caption(
                "Escala: 0 No implementado · 1 Inicial · 2 En desarrollo · "
                "3 Implementado · 4 Optimizado"
            )
            grupo_rows = list(grupo.iterrows())
            for idx, (_, row) in enumerate(grupo_rows):
                codigo = row["codigo"]
                tipo = row.get("tipo", "nivel")
                wkey = widget_key_respuesta(codigo, ambito_unidad_id)
                texto = str(row.get("texto", "")).strip()
                if ambito_unidad_id:
                    texto = texto_indicador_para_ambito(texto, ambito_unidad_id)
                else:
                    texto = legibilizar_siglas_udigital(texto)
                st.markdown(
                    f'<div class="mdeia-indicador">'
                    f'<p class="mdeia-indicador-codigo"><code>{html.escape(codigo)}</code></p>'
                    f'<p class="mdeia-indicador-texto">{html.escape(texto)}</p>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
                if tipo == "si_no":
                    tiene = _init_widget_desde_respuesta(wkey, codigo, respuestas)
                    radio_kw = dict(
                        label="Respuesta",
                        options=["No", "Sí"],
                        key=wkey,
                        horizontal=True,
                        label_visibility="collapsed",
                    )
                    if not tiene:
                        radio_kw["index"] = 0
                    val = st.radio(**radio_kw)
                    respuestas[codigo] = val
                elif tipo in {"porcentaje", "umbral"}:
                    tiene = _init_widget_desde_respuesta(wkey, codigo, respuestas)
                    slider_kw = dict(
                        label=f"Valor ({row.get('unidad') or '%'})",
                        min_value=0.0,
                        max_value=100.0,
                        key=wkey,
                        label_visibility="collapsed",
                    )
                    if not tiene:
                        slider_kw["value"] = 0.0
                    val = st.slider(**slider_kw)
                    respuestas[codigo] = val
                else:
                    opciones = list(niveles.keys())
                    tiene = _init_widget_desde_respuesta(wkey, codigo, respuestas)
                    radio_kw = dict(
                        label="Nivel de madurez",
                        options=opciones,
                        format_func=lambda x: str(x),
                        key=wkey,
                        label_visibility="collapsed",
                        horizontal=True,
                    )
                    if not tiene:
                        radio_kw["index"] = 0
                    val = st.radio(**radio_kw)
                    st.caption(
                        f"Nivel elegido: **{val} — {_NIVEL_SLIDER.get(val, niveles.get(val, ''))}**"
                    )
                    respuestas[codigo] = val
                if idx < len(grupo_rows) - 1:
                    st.markdown("---")
