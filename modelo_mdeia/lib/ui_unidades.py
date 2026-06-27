# -*- coding: utf-8 -*-
"""Vista de unidades académicas — selección única, organizada por sede."""

from __future__ import annotations

from constants import FASE1_CORTO, IMD_FASE1_LABEL
import streamlit as st

from lib.unidades import (
    load_unidades_catalogo,
    resumen_unidad,
    set_unidad_activa,
    unidad_label,
)


def render_panel_unidades() -> None:
    activa = st.session_state.mdeia_unidad_activa

    st.subheader("Unidades académicas")
    st.markdown(
        """
        Misma nomenclatura que el **Consejo de Investigación** y **Producción Científica**.
        Elegí **una sola unidad** para trabajar; el resto del sistema (informe, línea de base, IMD)
        usa únicamente la unidad seleccionada.
        """
    )

    st.markdown("##### Elegir unidad")
    for grupo in load_unidades_catalogo()["grupos"]:
        expanded = any(u["id"] == activa for u in grupo["unidades"])
        with st.expander(grupo["nombre"], expanded=expanded):
            for u in grupo["unidades"]:
                es_activa = u["id"] == activa
                c_nom, c_btn = st.columns([5, 1])
                with c_nom:
                    marca = "**→** " if es_activa else ""
                    st.markdown(f"{marca}{u['label']}")
                with c_btn:
                    if es_activa:
                        st.caption("Activa")
                    elif st.button("Elegir", key=f"pick_unidad_{u['id']}", use_container_width=True):
                        set_unidad_activa(u["id"])
                        st.rerun()

    st.markdown("---")
    st.markdown("### Unidad seleccionada")
    res = resumen_unidad(activa)
    st.info(unidad_label(activa))

    c1, c2, c3 = st.columns(3)
    c1.metric(FASE1_CORTO, f"{res['piloto_n']} / {res['piloto_total']}")
    c2.metric("Catálogo", res["catalogo_n"])
    imd = res["imd_piloto"]
    c3.metric(IMD_FASE1_LABEL, f"{imd} %" if imd is not None else "—")

    if st.button("Continuar con Informe automático", type="primary", use_container_width=True):
        st.session_state.mdeia_seccion = "Informe automático"
        st.rerun()
