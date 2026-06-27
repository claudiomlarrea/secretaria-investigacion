# -*- coding: utf-8 -*-
"""UI del flujo automático: carga → índices → informes."""

from __future__ import annotations

from datetime import date

import streamlit as st

from constants import FASE1_CORTO, FASE1_TITULO, IMD_FASE1_LABEL, PLANTILLA_FASE1_FILENAME
from lib.importar_datos import (
    generar_plantilla_excel,
    load_sheet_indicadores,
    load_uploaded_indicadores,
    parse_google_sheet_url,
)
from lib.mdeia_model import calcular_imd, guia_indices, pilot_codigos, progreso_piloto
from lib.unidades import (
    actualizar_meta_informe_activa,
    meta_informe_activa,
    reemplazar_respuestas_activas,
    respuestas_activas,
    unidad_label,
)


def _panel_resultado_automatico(resp: dict, meta: dict) -> None:
    if not resp:
        st.warning("No hay indicadores cargados todavía.")
        return

    resultado = calcular_imd(resp, codigos=pilot_codigos())
    n, total = progreso_piloto(resp)

    st.success(f"**{n}** indicadores procesados (línea de base: {n}/{total}).")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(IMD_FASE1_LABEL, f"{resultado['imd']} %")
    c2.metric("Satisfechas", f"{resultado['p_satisfechas']}/{resultado['p_totales']}")
    c3.metric("Cobertura", f"{resultado['cobertura_pct']} %")
    c4.metric("Dimensión IA", f"{resultado['ia']['ratio_pct']} %")

    with st.expander("¿Qué significan estos índices?", expanded=True):
        for item in guia_indices(resultado):
            st.markdown(f"**{item['nombre']}:** {item['valor']} *(rango {item['rango']})*")
            st.caption(item["interpretacion"])

    st.markdown("##### Descargar informe")
    slug = meta.get("unidad_id", "uccuyo").replace(" ", "_")
    fecha = date.today().isoformat()

    col_x, col_w, col_h = st.columns(3)
    with col_x:
        st.download_button(
            "Excel (.xlsx)",
            data=generar_excel_bytes(resp, meta=meta, modo="piloto"),
            file_name=f"mdeia-{slug}-{fecha}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary",
        )
    with col_w:
        st.download_button(
            "Word (.docx)",
            data=generar_word_bytes(resp, meta=meta, modo="piloto"),
            file_name=f"mdeia-{slug}-{fecha}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
            type="primary",
        )
    with col_h:
        st.download_button(
            "HTML (PDF)",
            data=generar_html_bytes(resp, meta=meta, modo="piloto"),
            file_name=f"mdeia-{slug}-{fecha}.html",
            mime="text/html",
            use_container_width=True,
        )


def render_informe_automatico() -> None:
    uid = st.session_state.mdeia_unidad_activa
    label = unidad_label(uid)
    meta = dict(meta_informe_activa())
    meta["unidad_id"] = uid
    meta["unidad_label"] = label
    meta["sede"] = label
    actualizar_meta_informe_activa(meta)

    st.warning(
        "Los datos y el informe se guardan para la **unidad activa** del menú lateral. "
        "Elegí FDCSSL (u otra facultad) **antes** de subir el Excel y de descargar el Word."
    )
    st.markdown(
        f"""
        **Unidad activa:** {meta['unidad_label']}

        1. Descargá la **plantilla Excel** y completá solo la columna **valor** (desplegable o número).
           Las columnas `tipo` y `como_completar` explican qué poner; ver también la hoja **Escalas**.
        2. Subí el archivo **.xlsx** o pegá un **Google Sheet** con columnas `codigo` y `valor`.
        3. El sistema calcula el **IMD** al instante y genera informes **Excel** y **Word**.
        """
    )

    st.download_button(
        f"Descargar plantilla Excel ({FASE1_TITULO})",
        data=generar_plantilla_excel(piloto=True),
        file_name=PLANTILLA_FASE1_FILENAME,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    tab_archivo, tab_sheet, tab_resultado = st.tabs(
        ["Subir Excel/CSV", "Google Sheet", "Índices e informes"]
    )

    with tab_archivo:
        archivo = st.file_uploader("Planilla de indicadores", type=["xlsx", "xls", "csv"])
        if st.button("Procesar archivo", type="primary", disabled=archivo is None):
            try:
                incoming = load_uploaded_indicadores(archivo.name, archivo.getvalue())
                reemplazar_respuestas_activas(incoming)
                actualizar_meta_informe_activa(
                    {
                        "unidad_id": uid,
                        "unidad_label": label,
                        "sede": label,
                    }
                )
                st.session_state.mdeia_ultima_carga = len(incoming)
                st.success(
                    f"Listo: {len(incoming)} indicadores importados para **{label}**."
                )
                st.info("Abrí la pestaña **Índices e informes** para ver el IMD y descargar informes.")
            except Exception as exc:
                st.error(str(exc))

    with tab_sheet:
        st.caption(
            "Podés pegar la **URL completa** del Google Sheet o solo el ID. "
            "La planilla debe tener columnas **codigo** y **valor** (como la plantilla Excel)."
        )
        sheet_input = st.text_input(
            "URL o ID de Google Sheet",
            placeholder="https://docs.google.com/spreadsheets/d/1abc…xyz/edit#gid=0",
        )
        gid_manual = st.text_input(
            "GID (solo si pegaste solo el ID, sin URL)",
            value="0",
            help="Número de pestaña. Si pegás la URL completa, se detecta solo.",
        )
        if sheet_input.strip():
            try:
                sid, gid_auto = parse_google_sheet_url(sheet_input.strip())
                gid = gid_auto if gid_auto != "0" or "#gid=" in sheet_input or "gid=" in sheet_input else gid_manual
                st.caption(f"ID detectado: `{sid}` · GID: `{gid}`")
            except ValueError:
                sid, gid = "", gid_manual
        if st.button("Procesar Sheet", type="primary", disabled=not sheet_input.strip()):
            try:
                sid, gid_auto = parse_google_sheet_url(sheet_input.strip())
                gid = gid_auto if gid_auto != "0" or "gid=" in sheet_input else gid_manual
                incoming = load_sheet_indicadores(sid, gid)
                reemplazar_respuestas_activas(incoming)
                actualizar_meta_informe_activa(
                    {
                        "unidad_id": uid,
                        "unidad_label": label,
                        "sede": label,
                    }
                )
                st.session_state.mdeia_ultima_carga = len(incoming)
                st.success(
                    f"Listo: {len(incoming)} indicadores importados para **{label}**."
                )
            except Exception as exc:
                st.error(str(exc))

    with tab_resultado:
        _panel_resultado_automatico(respuestas_activas(), meta)
