# -*- coding: utf-8 -*-
"""Vista de unidades académicas — selección única, organizada por sede."""

from __future__ import annotations

from constants import FASE1_CORTO, FASE1_MENU, IMD_FASE1_LABEL, INSTITUTION_NAME
import streamlit as st

from lib.unidades import (
    DEFAULT_UNIDAD,
    SEDES_IMD,
    SIN_UNIDAD,
    hay_unidad_activa,
    id_sede_virtual,
    load_unidades_catalogo,
    render_comparativa_referencia,
    resumen_unidad,
    set_unidad_activa,
    solicitar_seccion,
    unidad_label,
)


def _fila_elegir(
    unidad_id: str,
    activa: str,
    *,
    key_suffix: str,
    destacado: bool = False,
) -> None:
    es_activa = unidad_id == activa
    c_nom, c_btn = st.columns([5, 1])
    with c_nom:
        marca = "**→** " if es_activa else ""
        texto = unidad_label(unidad_id)
        if destacado:
            texto = f"**{texto}**"
        st.markdown(f"{marca}{texto}")
    with c_btn:
        if es_activa:
            st.caption("Activa")
        elif st.button("Elegir", key=f"pick_{key_suffix}", use_container_width=True):
            set_unidad_activa(unidad_id)
            st.rerun()


def render_panel_unidades() -> None:
    activa = st.session_state.mdeia_unidad_activa

    st.subheader("Unidades académicas")
    st.markdown(
        f"""
        Elegí **{INSTITUTION_NAME} completa**, **una sede** o **una facultad**.
        Cada ámbito tiene su propio diagnóstico (36 indicadores de línea de base)
        con preguntas adaptadas al nivel institucional, de sede o de unidad.
        """
    )

    st.markdown("##### Elegir ámbito de evaluación")
    for grupo in load_unidades_catalogo()["grupos"]:
        tipo = grupo.get("tipo", "")
        es_grupo_inst = tipo == "institucional"
        es_grupo_sede = tipo == "sede" and grupo["id"] in SEDES_IMD
        sede_id = id_sede_virtual(grupo["id"]) if es_grupo_sede else None
        expanded = (
            activa == DEFAULT_UNIDAD
            if es_grupo_inst
            else activa == sede_id or any(u["id"] == activa for u in grupo["unidades"])
        )
        with st.expander(grupo["nombre"], expanded=expanded):
            if es_grupo_inst:
                for u in grupo["unidades"]:
                    _fila_elegir(u["id"], activa, key_suffix=f"inst_{u['id']}", destacado=True)
                    st.caption(
                        "Diagnóstico institucional: evaluá la UCCuyo en su totalidad "
                        "(todas las sedes y unidades)."
                    )
            elif es_grupo_sede and sede_id:
                _fila_elegir(sede_id, activa, key_suffix=f"sede_{grupo['id']}", destacado=True)
                st.caption("Diagnóstico de la sede (36 indicadores, ámbito sede).")
                st.markdown("---")
                for u in grupo["unidades"]:
                    _fila_elegir(u["id"], activa, key_suffix=f"unidad_{u['id']}")
            else:
                for u in grupo["unidades"]:
                    _fila_elegir(u["id"], activa, key_suffix=f"unidad_{u['id']}")

    st.markdown("---")
    st.markdown("### Selección activa")
    if not hay_unidad_activa() or activa == SIN_UNIDAD:
        st.warning("Todavía no elegiste un ámbito. Usá **Elegir** en institución, sede o facultad.")
    else:
        res = resumen_unidad(activa)
        st.info(unidad_label(activa))

        c1, c2, c3 = st.columns(3)
        c1.metric(FASE1_CORTO, f"{res['piloto_n']} / {res['piloto_total']}")
        c2.metric("Catálogo", res["catalogo_n"])
        imd = res["imd_piloto"]
        c3.metric(IMD_FASE1_LABEL, f"{imd} %" if imd is not None else "—")

        if res.get("es_sede") or res.get("es_institucional"):
            render_comparativa_referencia(activa)

    c_pri, c_sec = st.columns(2)
    with c_pri:
        if st.button(
            f"Continuar con {FASE1_MENU}",
            type="primary",
            use_container_width=True,
            disabled=not hay_unidad_activa(),
        ):
            solicitar_seccion(FASE1_MENU)
            st.rerun()
    with c_sec:
        if st.button(
            "Informe automático (Excel)",
            use_container_width=True,
            disabled=not hay_unidad_activa(),
        ):
            solicitar_seccion("Informe automático")
            st.rerun()
