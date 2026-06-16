# -*- coding: utf-8 -*-
"""Analizador automático EPH — inclusión digital y movilidad social (Streamlit)."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_EPH = _ROOT / "eph_analisis"
_GEMELO = _ROOT / "gemelo_digital_plan_institucional"
for _p in (_ROOT, _EPH, _GEMELO):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

os.environ.setdefault("MPLCONFIGDIR", tempfile.mkdtemp(prefix="eph_mpl_"))

import matplotlib

matplotlib.use("Agg")

import pandas as pd
import plotly.express as px
import streamlit as st

from lib.styles import apply_plotly_style, render_header
from ui_theme import CHART_SEQUENCE, GREEN

from src.analyze import ejecutar_analisis
from src.config import ANALISIS_DISPONIBLES, YEARS_TIC
from src.download import download_panel_tic
from src.prepare import build_analysis_frame, validate_microdata
from src.report import exportar_excel_bytes, exportar_word_bytes
from src.request import SolicitudAnalisis

ANALISIS_UI = [a for a in ANALISIS_DISPONIBLES if a != "todos"]

render_header(
    "Analizador automático EPH — microdatos INDEC (hogar, individuo y TIC). "
    "Generá reportes en Excel y Word."
)

st.caption(
    "Fuente: INDEC — EPH + MAUTIC (módulo TIC, 4.º trimestre). "
    "Los microdatos se descargan en tiempo de ejecución desde repositorios públicos."
)


@st.cache_data(show_spinner="Descargando microdatos INDEC (hogar + individuo + TIC)…", ttl=86400)
def cargar_microdatos(years: tuple[int, ...], trimestre: int, force: bool) -> tuple[pd.DataFrame, pd.DataFrame]:
    hogar, individual = download_panel_tic(
        years=list(years),
        trimester=trimestre,
        force=force,
    )
    return hogar, individual


def _construir_solicitud() -> SolicitudAnalisis:
    with st.sidebar:
        st.subheader("Pedido de análisis")
        titulo = st.text_input("Título del informe", "Analizador automático EPH")
        ambito = st.selectbox(
            "Ámbito geográfico",
            options=["nacional", "san_juan", "aglomerado"],
            format_func=lambda x: {
                "nacional": "Argentina (31 aglomerados)",
                "san_juan": "Gran San Juan",
                "aglomerado": "Aglomerado EPH (código)",
            }[x],
        )
        aglomerado = None
        if ambito == "aglomerado":
            aglomerado = st.number_input("Código aglomerado INDEC", min_value=1, max_value=99, value=27)

        y_min, y_max = st.select_slider(
            "Años (4.º trimestre / módulo TIC)",
            options=YEARS_TIC,
            value=(YEARS_TIC[0], YEARS_TIC[-1]),
        )
        trimestre = st.selectbox("Trimestre", [4], index=0, help="El módulo TIC se releva en el 4T.")

        st.markdown("**Análisis a incluir**")
        todos = st.checkbox("Todos los análisis", value=True)
        if todos:
            analisis = ["todos"]
        else:
            analisis = st.multiselect(
                "Seleccionar",
                ANALISIS_UI,
                default=["descriptivos", "logistica", "shap"],
            )

        fmt_excel = st.checkbox("Generar Excel", value=True)
        fmt_word = st.checkbox("Generar Word", value=True)
        force = st.checkbox("Forzar nueva descarga", value=False)

        ejecutar = st.button("Ejecutar análisis", type="primary", use_container_width=True)

    return ejecutar, SolicitudAnalisis(
        titulo=titulo,
        years=list(range(y_min, y_max + 1)),
        trimestre=trimestre,
        ambito=ambito,
        aglomerado=int(aglomerado) if aglomerado is not None else None,
        analisis=analisis if analisis else ["todos"],
        excel=fmt_excel,
        word=fmt_word,
        force_download=force,
    )


ejecutar, solicitud = _construir_solicitud()

if ejecutar:
    with st.status("Procesando solicitud…", expanded=True) as status:
        st.write(f"Ámbito: **{solicitud.label}** · Período: **{solicitud.periodo_texto()}**")
        hogar, individual = cargar_microdatos(
            tuple(solicitud.years),
            solicitud.trimestre,
            solicitud.force_download,
        )
        df = build_analysis_frame(hogar, individual, aglomerado=solicitud.aglomerado_filtro)
        val = validate_microdata(df)
        st.write(f"Registros analizados: **{len(df):,}**")
        st.json(val)

        resultado = ejecutar_analisis(
            df,
            tipos=solicitud.analisis_resueltos,
            label=solicitud.label,
        )
        resultado["meta"] = {
            "titulo": solicitud.titulo,
            "ambito": solicitud.label,
            "periodo": solicitud.periodo_texto(),
            "registros": len(df),
            "validacion": val,
            "fuente": "INDEC — EPH (hogar, individuo, módulo TIC)",
        }
        st.session_state["eph_resultado"] = resultado
        st.session_state["eph_solicitud"] = solicitud
        status.update(label="Análisis completado", state="complete")

resultado = st.session_state.get("eph_resultado")
solicitud_guardada: SolicitudAnalisis | None = st.session_state.get("eph_solicitud")

if resultado and solicitud_guardada:
    tablas = resultado.get("tablas", {})
    st.success(
        f"Resultados listos — {resultado['meta'].get('registros', 0):,} registros · "
        f"correlación exclusión↔movilidad: {resultado.get('correlacion_destacada', 0):.3f}"
    )

    c1, c2, c3 = st.columns(3)
    slug = solicitud_guardada.label
    if solicitud_guardada.excel:
        c1.download_button(
            "Descargar Excel",
            data=exportar_excel_bytes(resultado),
            file_name=f"reporte_eph_{slug}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    if solicitud_guardada.word:
        c2.download_button(
            "Descargar Word",
            data=exportar_word_bytes(
                resultado,
                titulo=solicitud_guardada.titulo,
                periodo=solicitud_guardada.periodo_texto(),
                ambito=solicitud_guardada.label,
            ),
            file_name=f"informe_eph_{slug}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )

    graf = resultado.get("grafico_shap")
    if graf and Path(graf).exists():
        c3.image(graf, caption="Importancia SHAP / evolución")

    desc = tablas.get("descriptivos_anuales")
    if desc is not None and not desc.empty:
        st.subheader("Evolución anual")
        fig = px.line(
            desc,
            x="anio",
            y=["idx_exclusion_digital", "score_movilidad_proxy"],
            markers=True,
            color_discrete_sequence=CHART_SEQUENCE[:2],
            labels={"value": "Índice", "anio": "Año", "variable": "Indicador"},
        )
        apply_plotly_style(fig, title="Exclusión digital y movilidad social (proxy)")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(desc, use_container_width=True, hide_index=True)

    shap_df = tablas.get("shap_importancia")
    if shap_df is not None and not shap_df.empty:
        st.subheader("Peso relativo de variables (SHAP)")
        fig2 = px.bar(
            shap_df.head(10),
            x="peso_relativo_pct",
            y="variable",
            orientation="h",
            color_discrete_sequence=[GREEN],
        )
        apply_plotly_style(fig2)
        st.plotly_chart(fig2, use_container_width=True)

    for titulo_tab, clave in [
        ("Frecuencias", "frecuencias"),
        ("Correlaciones", "correlaciones"),
        ("Logística — coeficientes", "logistica_coeficientes"),
        ("Clústeres — perfiles", "cluster_perfiles"),
    ]:
        tdf = tablas.get(clave)
        if tdf is not None and not tdf.empty:
            with st.expander(titulo_tab, expanded=False):
                st.dataframe(tdf, use_container_width=True, hide_index=True)

else:
    st.info(
        "Configurá el pedido en la barra lateral y presioná **Ejecutar análisis**. "
        "La app descargará los microdatos públicos del INDEC y generará los reportes."
    )

    with st.expander("Cómo publicar en Streamlit Cloud (GitHub)"):
        st.markdown(
            """
1. Subí este repositorio a **GitHub** (`main`).
2. Entrá a [share.streamlit.io](https://share.streamlit.io) e iniciá sesión con GitHub.
3. **New app** → elegí tu repositorio en GitHub → archivo principal: `streamlit_app.py`.
4. En **App name** (nombre visible en Streamlit Cloud): **Analizador automático EPH**.
5. Python 3.11 · dependencias: `requirements.txt` en la raíz.
6. Deploy. Cada `push` a `main` actualiza la app automáticamente.
            """
        )
