# -*- coding: utf-8 -*-
"""MDeIA UCCuyo — sistema de medición de madurez digital e IA · UCCuyo."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

from constants import (
    APP_NAME,
    APP_SUBTITLE,
    FASE1_CORTO,
    FASE1_MENU,
    FASE1_N_INDICADORES,
    FASE1_TITULO,
    IMD_FASE1_LABEL,
    PLANTILLA_FASE1_FILENAME,
)
from lib.mdeia_model import (
    areas_df,
    brechas_prioritarias,
    calcular_imd,
    detalle_evaluacion,
    exportar_diagnostico,
    fases_df,
    indicadores_df,
    indicadores_piloto_df,
    load_framework,
    load_indicadores,
    load_piloto,
    normalizar_respuestas,
    pilot_codigos,
    progreso_piloto,
    respuestas_piloto,
    retos_df,
)
from lib.informe import generar_informe_html
from lib.oia_encuesta import (
    analizar_encuesta,
    aplicar_metricas_mdeia,
    fetch_sheet_csv,
    load_oia_config,
    load_uploaded_file,
    metricas_desde_cifras,
    resumen_markdown,
    sheet_export_url,
)
from lib.ui_encuesta import render_encuesta
from lib.ui_informe_auto import render_informe_automatico
from lib.ui_unidades import render_panel_unidades
from lib.unidades import (
    actualizar_meta_informe_activa,
    aplicar_navegacion_pendiente,
    exportar_todas_unidades,
    es_ambito_macro,
    es_seleccion_institucional,
    fusionar_carga_json,
    hay_unidad_activa,
    init_session_store,
    limpiar_respuestas_activas,
    meta_informe_activa,
    metricas_sidebar_activa,
    render_comparativa_referencia,
    render_comparativa_facultades_sede,
    reemplazar_respuestas_activas,
    solicitar_seccion,
    render_selector_unidades_sidebar,
    respuestas_activas,
    resumen_unidad,
    sincronizar_respuestas_widgets,
    unidad_label,
)
from ui_theme import estilizar_escala_cantidad, inject_theme, render_header

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_theme()

fw = load_framework()
meta = fw["meta"]
piloto = load_piloto()
niveles = {n["valor"]: n["etiqueta"] for n in fw["niveles_madurez"]}

render_header(
    "Índice de Madurez Digital e Inteligencia Artificial (IMD) para la UCCuyo. "
    "Adaptación del framework UDigital madurez (MetaRed) con extensión IA del Observatorio."
)

init_session_store()
sincronizar_respuestas_widgets()

SECCIONES = [
    "Informe automático",
    "Guía del diagnóstico",
    "Unidades académicas",
    "Encuesta estudiantil",
    FASE1_MENU,
    "Autodiagnóstico completo",
    "Panel IMD",
    "Marco MDeIA",
    "Plan por fases",
]

if "mdeia_evaluador" not in st.session_state:
    st.session_state.mdeia_evaluador = ""

if "mdeia_seccion" not in st.session_state:
    st.session_state.mdeia_seccion = SECCIONES[0]
elif st.session_state.mdeia_seccion == "Piloto Fase 1":
    st.session_state.mdeia_seccion = FASE1_MENU

aplicar_navegacion_pendiente(secciones=SECCIONES)

res_ctx = (
    resumen_unidad(st.session_state.mdeia_unidad_activa)
    if hay_unidad_activa()
    else {"piloto_n": 0, "piloto_total": len(pilot_codigos())}
)
if hay_unidad_activa():
    n_piloto, total_piloto = progreso_piloto(respuestas_activas())
else:
    n_piloto, total_piloto = 0, len(pilot_codigos())

with st.sidebar:
    st.markdown(f"### {APP_NAME}")
    st.caption(APP_SUBTITLE)
    st.markdown("---")
    st.radio(
        "Secciones",
        SECCIONES,
        key="mdeia_seccion",
        label_visibility="collapsed",
    )
    st.markdown("---")
    m = metricas_sidebar_activa()
    st.metric(FASE1_CORTO, m["linea_base"])
    if m["imd"] is not None:
        st.metric(IMD_FASE1_LABEL, f"{m['imd']} %")
    st.metric("Catálogo completo", f"{m['catalogo']} / {m['catalogo_total']}")
    n_piloto, total_piloto = progreso_piloto(respuestas_activas())
    if n_piloto == total_piloto and total_piloto:
        st.success("Línea de base completa. Exportá el informe ejecutivo.")

    st.markdown("---")
    render_selector_unidades_sidebar()

    st.markdown("---")
    st.markdown("**Evaluador**")
    st.session_state.mdeia_evaluador = st.text_input(
        "Tu nombre (evaluador)",
        value=st.session_state.mdeia_evaluador,
        placeholder="Ej.: Claudio Larrea",
    )

    with st.expander("Guardar / cargar trabajo"):
        st.caption(
            "Las respuestas viven en esta sesión del navegador. "
            "Exportá JSON para compartir con el equipo o retomar después."
        )
        payload = exportar_todas_unidades(evaluador=st.session_state.mdeia_evaluador)
        st.download_button(
            "Descargar progreso JSON",
            data=json.dumps(payload, ensure_ascii=False, indent=2),
            file_name=f"mdeia-progreso-{date.today().isoformat()}.json",
            mime="application/json",
            use_container_width=True,
        )
        uploaded = st.file_uploader("Cargar JSON del equipo", type="json", label_visibility="collapsed")
        if uploaded is not None:
            try:
                data = json.load(uploaded)
                merged = fusionar_carga_json(data)
                if data.get("meta_encuesta", {}).get("evaluador"):
                    st.session_state.mdeia_evaluador = data["meta_encuesta"]["evaluador"]
                st.success(
                    f"Fusionado: +{merged} indicadores "
                    f"(unidad activa: {unidad_label(st.session_state.mdeia_unidad_activa)})."
                )
                st.rerun()
            except (json.JSONDecodeError, KeyError) as exc:
                st.error(f"No se pudo leer el archivo: {exc}")

seccion = st.session_state.mdeia_seccion


def _meta_informe_widgets() -> dict:
    m = dict(meta_informe_activa())
    c1, c2, c3 = st.columns(3)
    with c1:
        m["fecha"] = st.date_input("Fecha del informe", value=date.fromisoformat(m["fecha"])).isoformat()
    with c2:
        m["responsable"] = st.text_input("Responsable", value=m["responsable"])
    with c3:
        m["sede"] = st.text_input("Ámbito / unidad", value=m.get("sede") or unidad_label(st.session_state.mdeia_unidad_activa))
    actualizar_meta_informe_activa(m)
    return m


def _panel_imd(resp: dict, *, modo_piloto: bool = False) -> None:
    codes = pilot_codigos() if modo_piloto else None
    if modo_piloto:
        resp = respuestas_piloto(resp)
    if not resp:
        n_pil, tot_pil = progreso_piloto(respuestas_activas())
        st.warning(
            "El Panel IMD muestra resultados **después** de cargar respuestas. "
            "Todavía no hay indicadores en el ámbito activo."
        )
        st.markdown("#### Pasos para ver el IMD")
        st.markdown(
            f"""
            1. **Unidades académicas** — elegí el ámbito (UCCuyo completa, una sede o una facultad) con **Elegir**.
            2. **{FASE1_MENU}** — respondé los **36 indicadores** (sesión ~90 min con el equipo).
               - Opcional: en **Encuesta estudiantil** subí el Excel de alumnos y **Aplicar al diagnóstico** (bloque B8 · IA).
            3. Volvé a **Panel IMD** para ver el índice, gráficos por área/reto y brechas.
            """
        )
        if not hay_unidad_activa():
            st.error("Paso pendiente: todavía no elegiste un ámbito de evaluación.")
        elif n_pil == 0:
            st.info(
                f"Ámbito activo: **{unidad_label(st.session_state.mdeia_unidad_activa)}**. "
                f"Falta completar indicadores ({n_pil}/{tot_pil} en línea de base)."
            )
        if st.session_state.get("mdeia_oia_metricas"):
            st.warning(
                "Hay una encuesta de alumnos **analizada** pero no aplicada al diagnóstico. "
                "Andá a **Encuesta estudiantil → Resultado y aplicar → Aplicar al diagnóstico MDeIA**."
            )
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("1 · Unidades académicas", use_container_width=True):
                solicitar_seccion("Unidades académicas")
                st.rerun()
        with c2:
            if st.button(f"2 · {FASE1_MENU}", type="primary", use_container_width=True):
                solicitar_seccion(FASE1_MENU)
                st.rerun()
        with c3:
            if st.button("Encuesta estudiantil", use_container_width=True):
                solicitar_seccion("Encuesta estudiantil")
                st.rerun()
        return

    resultado = calcular_imd(resp, codigos=codes)
    st.session_state.mdeia_resultado = resultado
    titulo = IMD_FASE1_LABEL if modo_piloto else "IMD catálogo evaluado"

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(titulo, f"{resultado['imd']}%")
    m2.metric("Prácticas satisfechas", f"{resultado['p_satisfechas']} / {resultado['p_totales']}")
    m3.metric("Cobertura", f"{resultado['cobertura_pct']}%")
    m4.metric("Dimensión IA", f"{resultado['ia']['ratio_pct']}%")

    umbral = resultado["umbral_regional_objetivo"]
    if resultado["imd"] >= umbral:
        st.success(f"Por encima del umbral regional ({umbral}%).")
    else:
        st.warning(f"Por debajo del umbral objetivo ({umbral}%). Priorizar Fase 2.")

    col_l, col_r = st.columns(2)
    with col_l:
        df_area = pd.DataFrame(resultado["por_area"])
        if not df_area.empty:
            area_names = {a["id"]: a["nombre"] for a in fw["areas"]}
            df_area["Área"] = df_area["grupo"].map(area_names).fillna(df_area["grupo"])
            st.markdown("**IMD por área**")
            st.bar_chart(
                df_area.set_index("Área")[["ratio_pct"]].rename(columns={"ratio_pct": "IMD (%)"}),
                height=300,
            )
    with col_r:
        df_reto = pd.DataFrame(resultado["por_reto"])
        if not df_reto.empty:
            st.markdown("**IMD por reto**")
            st.bar_chart(
                df_reto.set_index("grupo")[["ratio_pct"]].rename(columns={"ratio_pct": "IMD (%)"}),
                height=300,
            )

    det = detalle_evaluacion(resp)
    if codes is not None and not det.empty:
        det = det[det["Código"].isin(codes)]
    if not det.empty:
        st.markdown("##### Detalle")
        st.dataframe(
            estilizar_escala_cantidad(det, columnas_cantidad=["Valor"]),
            use_container_width=True,
            hide_index=True,
        )

    brechas = brechas_prioritarias(resp)
    if codes is not None and not brechas.empty:
        brechas = brechas[brechas["Código"].isin(codes)]
    st.markdown("##### Brechas prioritarias")
    if brechas.empty:
        st.success("No hay brechas entre los indicadores evaluados.")
    else:
        st.dataframe(brechas, use_container_width=True, hide_index=True)


if "mdeia_oia_metricas" not in st.session_state:
    st.session_state.mdeia_oia_metricas = None

if seccion == "Informe automático":
    render_informe_automatico()

elif seccion == "Encuesta estudiantil":
    oia_cfg = load_oia_config()
    st.subheader("Encuesta estudiantil de IA")
    st.info(
        "**No necesitás Google Sheet.** Si todavía no hay planilla vinculada al formulario, "
        "usá **Carga manual** con las cifras que tenga el equipo o completá el bloque **B8** "
        "en **Línea de base IMD**."
    )
    st.markdown(
        f"""
        Cuando existan respuestas exportables, podés subir el Excel de Google Forms
        ([Encuesta Clara]({oia_cfg['encuesta_clara_url']})). Google Sheet es **opcional**
        y solo aplica si alguien del OIA comparte el ID de la planilla de respuestas.
        """
    )

    try:
        secret_sheet = st.secrets.get("oia", {}).get("google_sheet_id", "")
        secret_gid = st.secrets.get("oia", {}).get("google_sheet_gid", oia_cfg.get("google_sheet_gid", "0"))
        secret_pob = st.secrets.get("oia", {}).get("poblacion_objetivo_estudiantes")
    except (FileNotFoundError, AttributeError):
        secret_sheet, secret_gid, secret_pob = "", oia_cfg.get("google_sheet_gid", "0"), None

    default_sheet = secret_sheet or oia_cfg.get("google_sheet_id", "")
    default_pob = int(secret_pob or oia_cfg.get("poblacion_objetivo_estudiantes") or 0)

    tab_manual, tab_upload, tab_sheet, tab_result = st.tabs(
        ["Carga manual", "Subir Excel/CSV", "Google Sheet (opcional)", "Resultado y aplicar"]
    )

    with tab_manual:
        st.markdown(
            "Ingresá lo que sepas de la encuesta estudiantil del OIA. "
            "Con **respuestas + población** calculamos la tasa (meta MDeIA ≥ 70 %)."
        )
        c1, c2 = st.columns(2)
        with c1:
            n_manual = st.number_input(
                "Respuestas recibidas",
                min_value=0,
                value=0,
                step=1,
                key="oia_n_manual",
            )
        with c2:
            pob_manual = st.number_input(
                "Estudiantes convocados (población)",
                min_value=0,
                value=default_pob,
                step=100,
                key="oia_pob_manual",
                help="Ej.: matrícula o lista de difusión de la encuesta.",
            )
        usar_tasa_directa = st.checkbox(
            "Ya conozco la tasa de respuesta (%) y no tengo el desglose",
            key="oia_tasa_directa",
        )
        tasa_directa: float | None = None
        if usar_tasa_directa:
            tasa_directa = st.slider(
                "Tasa de respuesta (%)",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                key="oia_tasa_slider",
            )

        if n_manual > 0 or tasa_directa is not None:
            pob_prev = pob_manual if pob_manual > 0 else None
            preview = metricas_desde_cifras(
                n_respuestas=n_manual,
                poblacion=pob_prev,
                tasa_pct=tasa_directa if usar_tasa_directa else None,
            )
            st.markdown(resumen_markdown(preview))

        if st.button("Usar estas cifras", type="primary", key="oia_btn_manual"):
            pob_prev = pob_manual if pob_manual > 0 else None
            st.session_state.mdeia_oia_metricas = metricas_desde_cifras(
                n_respuestas=n_manual,
                poblacion=pob_prev,
                tasa_pct=tasa_directa if usar_tasa_directa else None,
            )
            st.success("Cifras guardadas. Revisá **Resultado y aplicar**.")

        st.markdown("---")
        st.caption(
            f"También podés cargar B8 a mano en **{FASE1_MENU} → Autodiagnóstico (36 ind.)**. "
            f"Observatorio: [{oia_cfg['observatorio_url']}]({oia_cfg['observatorio_url']})"
        )
        if st.button("Aplicar cifras al diagnóstico MDeIA", key="oia_aplicar_manual"):
            pob_prev = pob_manual if pob_manual > 0 else None
            metricas = metricas_desde_cifras(
                n_respuestas=n_manual,
                poblacion=pob_prev,
                tasa_pct=tasa_directa if usar_tasa_directa else None,
            )
            st.session_state.mdeia_oia_metricas = metricas
            reemplazar_respuestas_activas(
                aplicar_metricas_mdeia(
                    metricas,
                    respuestas_activas(),
                    config=oia_cfg,
                )
            )
            st.success(
                "Indicadores OIA aplicados. Revisá **Línea de base IMD → Autodiagnóstico (36 ind.)** (B8) "
                "o el **Panel IMD**."
            )

    with tab_upload:
        st.caption("En Google Forms: Respuestas → Descargar (.xlsx)")
        archivo = st.file_uploader("Archivo de respuestas", type=["xlsx", "xls", "csv"])
        pob_upload = st.number_input(
            "Población objetivo (estudiantes convocados)",
            min_value=0,
            value=default_pob,
            step=100,
            key="oia_pob_upload",
            help="Necesario para calcular la tasa de respuesta (meta MDeIA ≥ 70 %).",
        )
        if st.button("Analizar archivo", type="primary", disabled=archivo is None):
            try:
                df = load_uploaded_file(archivo.name, archivo.getvalue())
                pob = pob_upload if pob_upload > 0 else None
                st.session_state.mdeia_oia_metricas = analizar_encuesta(df, poblacion=pob)
                st.session_state.mdeia_oia_df_rows = len(df)
                st.success("Encuesta analizada. Revisá la pestaña **Resultado y aplicar**.")
            except Exception as exc:
                st.error(str(exc))

    with tab_sheet:
        st.caption(
            "Solo si el equipo OIA tiene una planilla de Google vinculada al formulario "
            "y puede compartir el ID (o publicarla con link de lectura)."
        )
        sheet_id = st.text_input(
            "ID de Google Sheet (respuestas del formulario)",
            value=default_sheet,
            placeholder="1abc…xyz en docs.google.com/spreadsheets/d/ID/edit",
        )
        gid = st.text_input("GID de la pestaña", value=str(secret_gid or "0"))
        pob_sheet = st.number_input(
            "Población objetivo",
            min_value=0,
            value=default_pob,
            step=100,
            key="oia_pob_sheet",
        )
        if sheet_id:
            st.caption(f"URL de export: `{sheet_export_url(sheet_id, gid)}`")
        if st.button("Sincronizar desde Sheet", type="primary", disabled=not sheet_id.strip()):
            try:
                df = fetch_sheet_csv(sheet_id.strip(), gid)
                pob = pob_sheet if pob_sheet > 0 else None
                st.session_state.mdeia_oia_metricas = analizar_encuesta(df, poblacion=pob)
                st.session_state.mdeia_oia_df_rows = len(df)
                st.success("Sheet leído. Revisá **Resultado y aplicar**.")
            except Exception as exc:
                st.error(str(exc))

        with st.expander("Configuración permanente (Streamlit secrets)"):
            st.code(
                '[oia]\ngoogle_sheet_id = "TU_ID_AQUI"\ngoogle_sheet_gid = "0"\n'
                "poblacion_objetivo_estudiantes = 5000",
                language="toml",
            )

    with tab_result:
        metricas = st.session_state.mdeia_oia_metricas
        if not metricas:
            st.info(
                "Usá **Carga manual**, subí un Excel o (opcional) sincronizá un Google Sheet."
            )
        else:
            st.markdown("#### Resumen de la encuesta")
            st.markdown(resumen_markdown(metricas))

            c1, c2, c3 = st.columns(3)
            c1.metric("Respuestas", metricas["n_respuestas"])
            tasa = metricas.get("tasa_respuesta_pct")
            c2.metric("Tasa respuesta", f"{tasa} %" if tasa is not None else "—")
            alto = metricas.get("pct_uso_ia_alto")
            c3.metric("Uso IA frecuente", f"{alto} %" if alto is not None else "—")

            st.markdown("#### Indicadores MDeIA que se actualizarán")
            st.markdown(
                """
                | Indicador | Valor automático |
                |-----------|------------------|
                | `MDEIA_IA_ENCUESTA` | Tasa de respuesta (%) o N respuestas si falta población |
                | `MDEIA_IA_OBSERVATORIO` | Nivel 0–4 según volumen de respuestas |
                """
            )

            if st.button("Aplicar al diagnóstico MDeIA", type="primary"):
                reemplazar_respuestas_activas(
                    aplicar_metricas_mdeia(
                        metricas,
                        respuestas_activas(),
                        config=oia_cfg,
                    )
                )
                st.success(
                    f"Indicadores OIA aplicados. Revisá **{FASE1_MENU} → Autodiagnóstico (36 ind.)** "
                    "bloque B8 o el **Panel IMD**."
                )

            if metricas.get("n_respuestas", 0) > 0:
                enc = respuestas_activas().get("MDEIA_IA_ENCUESTA")
                obs = respuestas_activas().get("MDEIA_IA_OBSERVATORIO")
                st.caption(f"Valores actuales en sesión: ENCUESTA={enc}, OBSERVATORIO={obs}")

elif seccion == "Unidades académicas":
    render_panel_unidades()

elif seccion == "Guía del diagnóstico":
    st.subheader("Guía del diagnóstico MDeIA")
    st.markdown(
        f"""
        El **MDeIA UCCuyo** no se conecta automáticamente a SIU ni a bases externas (por ahora).
        Los integrantes del Observatorio **cargan los datos manualmente** en la encuesta, a partir
        de evidencia institucional, entrevistas con TI y resultados de las encuestas del OIA.

        ### Flujo automático (recomendado)

        1. Elegí la **unidad académica** en la barra lateral.
        2. Andá a **Informe automático** → descargá plantilla Excel o subí tu Google Sheet.
        3. El sistema calcula el **IMD** y permite descargar informes **Excel** y **Word**.

        ### Flujo manual (complementario)

        ### Cómo responder cada indicador

        | Tipo | Qué hacer | Ejemplo |
        |------|-----------|---------|
        | **Nivel 0–4** | Escala UDigital: 0 = no existe, 3 = implementado, 4 = optimizado | Estrategia digital formal |
        | **Sí / No** | Evidencia documental o normativa | ¿Existe guía ética de IA? |
        | **Porcentaje / umbral** | Dato numérico real o estimado en sala | Tasa respuesta encuesta OIA (meta ≥ 70 %) |

        ### Fuentes de datos sugeridas

        - **TI / Sistemas:** presupuesto TI, personal, seguridad, LMS, servicios digitalizados.
        - **OIA:** encuesta estudiantil de IA, observatorio, propuestas de guía ética.
        - **Secretaría / Rectorado:** estrategia institucional, planes de formación docente.
        - **Sesión conjunta (90 min):** consensuar niveles cuando no hay dato exacto.

        ### Importante

        - Los datos **no se guardan solos** al cerrar el navegador: exportá JSON con frecuencia.
        - Para la **línea de base oficial**, usá **{FASE1_MENU}** ({FASE1_N_INDICADORES} indicadores).
        - El catálogo completo (129) es para diagnósticos posteriores, no para la primera sesión.
        """
    )
    st.info(
        "Próximo paso: andá a **Informe automático**, cargá tu Excel o Sheet y descargá el informe."
    )

elif seccion == FASE1_MENU:
    st.subheader(FASE1_TITULO)
    st.caption(f"Unidad activa: **{unidad_label(st.session_state.mdeia_unidad_activa)}**")
    if es_seleccion_institucional(st.session_state.mdeia_unidad_activa):
        st.info(
            "Respondé los **36 indicadores** evaluando **toda la Universidad Católica de Cuyo** "
            "(políticas, servicios y recursos institucionales en todas las sedes)."
        )
    elif es_ambito_macro(st.session_state.mdeia_unidad_activa):
        st.info(
            "Respondé los **36 indicadores** evaluando **toda la sede** "
            "(políticas, servicios y recursos compartidos de la sede, no una sola facultad)."
        )
    st.markdown(piloto["descripcion"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Indicadores (línea de base)", len(piloto["indicadores"]))
    c2.metric("Duración sesión", f"{piloto['duracion_sesion_minutos']} min")
    c3.metric("Progreso", f"{n_piloto}/{total_piloto}")

    tab_guia, tab_encuesta, tab_informe = st.tabs(
        ["Guía de sesión", "Autodiagnóstico (36 ind.)", "Informe ejecutivo"]
    )

    with tab_guia:
        st.markdown("#### Participantes sugeridos")
        for p in piloto["participantes_sugeridos"]:
            st.markdown(f"- {p}")
        st.markdown("#### Materiales")
        for item in piloto["materiales"]:
            st.markdown(f"- {item}")
        st.markdown("#### Agenda (90 minutos)")
        st.dataframe(pd.DataFrame(piloto["agenda"]), use_container_width=True, hide_index=True)
        st.markdown("#### Bloques de la línea de base")
        bloques = {b["id"]: b["titulo"] for b in piloto["bloques"]}
        for bid, titulo in bloques.items():
            n = len([i for i in piloto["indicadores"] if i["bloque"] == bid])
            st.markdown(f"- **{bid}** · {titulo} ({n} indicadores)")

    with tab_encuesta:
        st.markdown(
            "**Instrucciones:** expandí cada bloque (B1–B8), leé el indicador y elegí el nivel "
            "según la evidencia. Si no hay dato, dejá **0 — No implementado** y anotá la brecha."
        )
        st.caption(f"Respondé los {FASE1_N_INDICADORES} indicadores de la línea de base.")
        bloques = {b["id"]: b["titulo"] for b in piloto["bloques"]}
        df_piloto = indicadores_piloto_df().sort_values(["bloque_piloto", "prioridad_piloto"])
        st.progress(
            n_piloto / max(total_piloto, 1),
            text=f"{n_piloto} de {total_piloto} indicadores (línea de base)",
        )
        render_encuesta(
            df_piloto,
            respuestas_activas(),
            niveles,
            agrupar_por="bloque_piloto",
            titulo_grupo_fn=lambda k, _g: f"{k} · {bloques.get(k, k)}",
            ambito_unidad_id=st.session_state.mdeia_unidad_activa,
        )
        render_comparativa_referencia()
        st.divider()
        if st.button(f"Calcular {IMD_FASE1_LABEL}", type="primary"):
            st.session_state.mdeia_resultado_piloto = calcular_imd(
                respuestas_activas(), codigos=pilot_codigos()
            )
            st.success(f"{IMD_FASE1_LABEL} calculado. Revisá la pestaña Informe ejecutivo.")

    with tab_informe:
        meta_inf = _meta_informe_widgets()
        if st.session_state.mdeia_evaluador:
            meta_inf["evaluador"] = st.session_state.mdeia_evaluador
        resp_p = respuestas_piloto(respuestas_activas())
        if not resp_p:
            st.info(
                "Todavía no hay respuestas. Completá el autodiagnóstico en la pestaña "
                "**Autodiagnóstico (36 ind.)** (mínimo un indicador para ver vista previa)."
            )
        elif len(resp_p) < total_piloto:
            st.warning(
                f"Faltan {total_piloto - len(resp_p)} indicadores para el informe completo "
                f"de la línea de base."
            )
        if resp_p:
            _panel_imd(respuestas_activas(), modo_piloto=True)
            render_comparativa_referencia()
            html_inf = generar_informe_html(
                respuestas_activas(), modo="piloto", meta_encuesta=meta_inf
            )
            st.download_button(
                "Descargar informe HTML (→ PDF)",
                data=html_inf,
                file_name=f"informe-imd-linea-base-{meta_inf['fecha']}.html",
                mime="text/html",
                type="primary",
            )
            st.caption("Abrí el HTML en el navegador y usá **Imprimir → Guardar como PDF**.")

elif seccion == "Autodiagnóstico completo":
    st.subheader("Autodiagnóstico — catálogo completo")
    col_filtro, col_modo = st.columns([2, 1])
    with col_filtro:
        filtro_area = st.multiselect("Filtrar por área", options=sorted(indicadores_df()["area"].unique()))
    with col_modo:
        solo_ia = st.checkbox("Solo dimensión IA")
        solo_comunes = st.checkbox("Solo indicadores comunes UDigital")

    df_ind = indicadores_df()
    if filtro_area:
        df_ind = df_ind[df_ind["area"].isin(filtro_area)]
    if solo_ia:
        df_ind = df_ind[df_ind["dimension_ia"]]
    if solo_comunes:
        df_ind = df_ind[df_ind["comun"]]

    n_total = len(load_indicadores())
    st.progress(
        min(1.0, len(respuestas_activas()) / max(n_total, 1)),
        text=f"{len(respuestas_activas())} indicadores respondidos",
    )
    render_encuesta(
        df_ind,
        respuestas_activas(),
        niveles,
        ambito_unidad_id=st.session_state.mdeia_unidad_activa,
    )
    render_comparativa_facultades_sede()

    st.divider()
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("Calcular IMD completo", type="primary"):
            st.session_state.mdeia_resultado = calcular_imd(respuestas_activas())
            st.success("IMD calculado. Ver **Panel IMD**.")
    with b2:
        if st.button("Limpiar respuestas"):
            limpiar_respuestas_activas()
            st.rerun()
    with b3:
        payload = exportar_diagnostico(respuestas_activas())
        st.download_button(
            "Exportar JSON",
            data=json.dumps(payload, ensure_ascii=False, indent=2),
            file_name="diagnostico-mdeia-uccuyo.json",
            mime="application/json",
        )

elif seccion == "Panel IMD":
    st.subheader("Panel IMD")
    st.caption(
        "Visualizá el IMD, gráficos y brechas del ámbito elegido en el sidebar. "
        "Requiere respuestas cargadas en Línea de base o catálogo completo."
    )
    modo = st.radio("Modo", [FASE1_MENU, "Catálogo completo"], horizontal=True)
    _panel_imd(respuestas_activas(), modo_piloto=(modo == FASE1_MENU))
    render_comparativa_facultades_sede()
    if respuestas_activas():
        meta_inf = _meta_informe_widgets()
        html_inf = generar_informe_html(
            respuestas_activas(),
            modo="piloto" if modo == FASE1_MENU else "completo",
            meta_encuesta=meta_inf,
        )
        st.download_button(
            "Descargar informe HTML",
            data=html_inf,
            file_name=f"informe-imd-{date.today().isoformat()}.html",
            mime="text/html",
        )

elif seccion == "Marco MDeIA":
    st.subheader("Origen y propósito")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Retos estratégicos", "7")
    c2.metric("Objetivos", "16")
    c3.metric("Indicadores catálogo", meta["indicadores_catalogo_udigital"] + meta["indicadores_ia_extension"])
    c4.metric(FASE1_CORTO, len(piloto["indicadores"]))
    st.markdown(f"El **{meta['nombre']}** mide madurez digital e IA. Fórmula: **{meta['formula_imd']}**.")
    st.dataframe(areas_df().rename(columns={"id": "ID", "nombre": "Área", "color": "Color"}), use_container_width=True, hide_index=True)
    st.dataframe(
        retos_df().rename(columns={"reto_id": "Reto", "reto": "Descripción", "objetivo_num": "N.º", "objetivo": "Objetivo", "area": "Área"}),
        use_container_width=True,
        hide_index=True,
    )

else:
    st.subheader("Plan de evolución MDeIA")
    for _, fase in fases_df().iterrows():
        with st.container(border=True):
            st.markdown(f"### {fase['id']}: {fase['nombre']} ({fase['meses']})")
            fc1, fc2 = st.columns(2)
            with fc1:
                st.markdown("**Madurez digital e IA**")
                st.write(fase["enfoque_udigital"])
            with fc2:
                st.markdown("**Emprendimiento (MetaRed X)**")
                st.write(fase["enfoque_emprendimiento"])
            for m in fase["metricas"]:
                st.markdown(f"- {m}")
