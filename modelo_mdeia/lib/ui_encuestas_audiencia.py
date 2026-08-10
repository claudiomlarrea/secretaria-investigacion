# -*- coding: utf-8 -*-
"""UI Streamlit — encuestas MDeIA por audiencia."""

from __future__ import annotations

from io import BytesIO

import pandas as pd
import streamlit as st

from constants import FASE1_MENU
from lib.encuestas_mdeia import (
    aplicar_encuesta_a_diagnostico,
    audiencia_cfg,
    calcular_indicadores_desde_encuesta,
    generar_plantilla_xlsx,
    listar_audiencias,
    plantilla_filename,
    resumen_encuesta_markdown,
    url_formulario_google,
)
from lib.oia_encuesta import load_uploaded_file
from lib.texto_legible import leyenda_siglas_markdown
from lib.unidades import reemplazar_respuestas_activas, respuestas_activas, unidad_label

_ICONOS = {
    "estudiante": "🎓",
    "docente": "👩‍🏫",
    "autoridad": "🏛️",
    "administracion": "📋",
}


def _init_session() -> None:
    if "mdeia_encuestas_resultados" not in st.session_state:
        st.session_state.mdeia_encuestas_resultados = {}


def _secrets_form_urls() -> dict[str, str]:
    try:
        raw = st.secrets.get("encuestas_forms", {})
        if isinstance(raw, dict):
            return {str(k): str(v).strip() for k, v in raw.items() if v}
    except (FileNotFoundError, AttributeError, TypeError):
        pass
    return {}


def _leer_excel_respuestas(name: str, data: bytes) -> pd.DataFrame:
    df = load_uploaded_file(name, data)
    if name.lower().endswith((".xlsx", ".xls")):
        xl = pd.ExcelFile(BytesIO(data))
        if "Respuestas" in xl.sheet_names:
            return xl.parse("Respuestas")
    return df


def _render_tarjeta_formulario(aud_id: str, nombre: str, descripcion: str, url: str) -> None:
    icono = _ICONOS.get(aud_id, "📝")
    st.markdown(f"#### {icono} {nombre}")
    if descripcion:
        st.caption(descripcion)
    if not url:
        st.warning("Enlace no configurado. Contactá al administrador MDeIA.")
        return
    c1, c2 = st.columns([1, 2])
    with c1:
        st.link_button(
            "Abrir formulario",
            url,
            type="primary",
            use_container_width=True,
            help="Se abre en una pestaña nueva para compartir o previsualizar.",
        )
    with c2:
        st.text_input(
            "Enlace para copiar y compartir",
            value=url,
            key=f"mdeia_form_url_{aud_id}",
            label_visibility="collapsed",
        )
    st.markdown(
        f"[Abrir en ventana nueva]({url}) · "
        "Seleccioná el enlace de la derecha y **Cmd+C** para pegarlo en mail o WhatsApp."
    )
    st.divider()


def render_encuestas_audiencia() -> None:
    _init_session()
    overrides = _secrets_form_urls()
    audiencias = listar_audiencias()
    ids = [a["id"] for a in audiencias]
    labels = {a["id"]: a["nombre"] for a in audiencias}

    st.subheader("Encuestas por audiencia")
    st.caption(f"Ámbito activo en MDeIA: **{unidad_label(st.session_state.mdeia_unidad_activa)}**")
    st.info(leyenda_siglas_markdown())

    st.markdown("### 1 · Compartir encuestas Google (OIA)")
    st.info(
        "**Para el equipo OIA:** hacé clic en **Abrir formulario**, copiá el enlace y compartilo. "
        "No hace falta Apps Script ni script.google.com."
    )
    for aud in audiencias:
        aud_id = aud["id"]
        url = url_formulario_google(aud_id, overrides=overrides)
        _render_tarjeta_formulario(aud_id, aud["nombre"], aud.get("descripcion", ""), url)

    st.markdown("### 2 · Cargar respuestas en MDeIA")
    st.caption(
        "Cuando cierren una ronda: Google Forms → **Respuestas → Descargar (.xlsx)** → subí el archivo abajo."
    )

    tab_cargar, tab_resultado, tab_plantillas = st.tabs(
        ["Cargar respuestas", "Resultado y aplicar", "Plantillas Excel (opcional)"]
    )

    with tab_cargar:
        sel = st.selectbox(
            "Audiencia de la encuesta",
            options=ids,
            format_func=lambda x: labels[x],
            key="mdeia_encuesta_audiencia_sel",
        )
        aud = audiencia_cfg(sel)
        pob = st.number_input(
            "Población convocada (cuántos recibieron el enlace)",
            min_value=0,
            value=0,
            step=50,
            key=f"mdeia_enc_pob_{sel}",
            help=aud.get("poblacion_ejemplo", ""),
        )
        archivo = st.file_uploader(
            "Archivo exportado de Google Forms (.xlsx)",
            type=["xlsx", "xls", "csv"],
            key=f"mdeia_enc_file_{sel}",
        )
        if st.button("Analizar encuesta", type="primary", disabled=archivo is None, key=f"btn_anal_{sel}"):
            try:
                df = _leer_excel_respuestas(archivo.name, archivo.getvalue())
                pob_val = pob if pob > 0 else None
                metricas = calcular_indicadores_desde_encuesta(df, sel, poblacion=pob_val)
                st.session_state.mdeia_encuestas_resultados[sel] = metricas
                st.success("Listo. Andá a **Resultado y aplicar**.")
            except Exception as exc:
                st.error(str(exc))

    with tab_resultado:
        sel_res = st.selectbox(
            "Ver resultado de",
            options=ids,
            format_func=lambda x: labels[x],
            key="mdeia_enc_res_sel",
        )
        metricas = st.session_state.mdeia_encuestas_resultados.get(sel_res)
        if not metricas:
            st.info("Todavía no hay respuestas cargadas para esta audiencia.")
        else:
            st.markdown(resumen_encuesta_markdown(metricas))
            for row in metricas.get("detalle_indicadores") or []:
                st.markdown(f"- `{row['codigo']}` → **{row['valor']}** ({row.get('nota', '')})")
            if st.button("Aplicar al diagnóstico MDeIA", type="primary", key=f"btn_apply_{sel_res}"):
                merged = aplicar_encuesta_a_diagnostico(respuestas_activas(), metricas)
                reemplazar_respuestas_activas(merged)
                n = len(metricas.get("indicadores") or {})
                st.success(
                    f"Se actualizaron **{n}** indicadores. Revisá **{FASE1_MENU}** o **Panel IMD**."
                )

    with tab_plantillas:
        st.caption("Solo si necesitás Excel de referencia; el flujo normal es Google Forms → exportar → cargar arriba.")
        for aud in audiencias:
            aud_id = aud["id"]
            st.download_button(
                f"Plantilla Excel — {aud['nombre']}",
                data=generar_plantilla_xlsx(aud_id),
                file_name=plantilla_filename(aud_id),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_tpl_{aud_id}",
            )
