# -*- coding: utf-8 -*-
"""Informe ejecutivo HTML de MDeIA UCCuyo (exportable a PDF desde el navegador)."""

from __future__ import annotations

import html
from datetime import date
from typing import Any

import pandas as pd

from constants import FASE1_TITULO
from lib.mdeia_model import (
    areas_df,
    brechas_prioritarias,
    calcular_imd,
    detalle_evaluacion,
    guia_indices,
    load_framework,
    load_piloto,
    pilot_codigos,
)


def _esc(text: Any) -> str:
    return html.escape(str(text) if text is not None else "")


def _tabla_html(df: pd.DataFrame, columnas: list[str] | None = None) -> str:
    if df.empty:
        return "<p><em>Sin datos.</em></p>"
    cols = columnas or list(df.columns)
    head = "".join(f"<th>{_esc(c)}</th>" for c in cols)
    rows = []
    for _, row in df.iterrows():
        cells = "".join(f"<td>{_esc(row[c])}</td>" for c in cols)
        rows.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def generar_informe_html(
    respuestas: dict[str, Any],
    *,
    modo: str = "piloto",
    meta_encuesta: dict | None = None,
) -> str:
    fw = load_framework()
    meta = fw["meta"]
    meta_encuesta = meta_encuesta or {}
    piloto = load_piloto()
    codigos = pilot_codigos() if modo == "piloto" else None
    resultado = calcular_imd(respuestas, codigos=codigos)

    titulo_modo = FASE1_TITULO if modo == "piloto" else "Catálogo completo"
    fecha = meta_encuesta.get("fecha") or date.today().isoformat()
    responsable = meta_encuesta.get("responsable", "Observatorio de IA · UCCuyo")
    unidad = (
        meta_encuesta.get("unidad_label")
        or meta_encuesta.get("sede")
        or "Institucional"
    )

    area_names = {a["id"]: a["nombre"] for a in areas_df().to_dict("records")}
    df_area = pd.DataFrame(resultado["por_area"])
    if not df_area.empty:
        df_area["Área"] = df_area["grupo"].map(area_names).fillna(df_area["grupo"])
        df_area = df_area.rename(columns={"ratio_pct": "IMD (%)", "satisfechos": "Satisfechos", "evaluados": "Evaluados"})
        tabla_area = _tabla_html(df_area, ["Área", "IMD (%)", "Satisfechos", "Evaluados"])
    else:
        tabla_area = "<p><em>Sin desglose por área.</em></p>"

    df_reto = pd.DataFrame(resultado["por_reto"])
    if not df_reto.empty:
        df_reto = df_reto.rename(columns={"grupo": "Reto", "ratio_pct": "IMD (%)", "satisfechos": "Satisfechos", "evaluados": "Evaluados"})
        tabla_reto = _tabla_html(df_reto, ["Reto", "IMD (%)", "Satisfechos", "Evaluados"])
    else:
        tabla_reto = "<p><em>Sin desglose por reto.</em></p>"

    brechas = brechas_prioritarias(respuestas, top_n=10)
    if codigos and not brechas.empty:
        brechas = brechas[brechas["Código"].isin(codigos)]
    tabla_brechas = _tabla_html(
        brechas,
        ["Indicador", "Valor actual", "Meta", "Interpretación", "Área", "Reto"],
    )

    guia = guia_indices(resultado)
    bloque_guia = "".join(
        f"<li><strong>{_esc(g['nombre'])}: {_esc(g['valor'])}</strong> "
        f"<span style='color:#666'>(rango {_esc(g['rango'])})</span><br/>"
        f"{_esc(g['interpretacion'])}</li>"
        for g in guia
    )

    det = detalle_evaluacion(respuestas)
    if codigos:
        det = det[det["Código"].isin(codigos)] if not det.empty else det
    tabla_det = _tabla_html(det, ["Código", "Indicador", "Área", "Satisface", "Valor"])

    umbral = resultado["umbral_regional_objetivo"]
    imd = resultado["imd"]
    if imd >= umbral:
        diag = f"La institución supera el umbral regional de referencia ({umbral}%)."
        diag_class = "ok"
    else:
        diag = f"Por debajo del umbral objetivo ({umbral}%). Se recomienda priorizar acciones de Fase 2."
        diag_class = "warn"

    acciones_fase2 = """
    <ul>
      <li>Sancionar guía de uso responsable de IA generativa (Consejo Superior).</li>
      <li>Desplegar capacitación docente en alfabetización algorítmica.</li>
      <li>Consolidar encuesta OIA de uso de IA con meta de respuesta ≥ 70 %.</li>
    </ul>
    """

    return f"""<!DOCTYPE html>
<html lang="es-AR">
<head>
  <meta charset="utf-8"/>
  <title>Informe IMD — {titulo_modo} — UCCuyo</title>
  <style>
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; color: #1A2E28; max-width: 920px; margin: 2rem auto; padding: 0 1.5rem; line-height: 1.5; }}
    h1 {{ color: #044A30; font-size: 1.6rem; border-bottom: 3px solid #044A30; padding-bottom: 0.4rem; }}
    h2 {{ color: #0A5C3E; font-size: 1.15rem; margin-top: 1.75rem; }}
    .meta {{ color: #666; font-size: 0.92rem; margin-bottom: 1.5rem; }}
    .kpi {{ display: flex; flex-wrap: wrap; gap: 1rem; margin: 1.25rem 0; }}
    .kpi div {{ flex: 1; min-width: 140px; background: #E8F3EF; border-top: 3px solid #044A30; padding: 0.75rem 1rem; border-radius: 8px; }}
    .kpi strong {{ display: block; font-size: 1.5rem; color: #033B26; }}
    .kpi span {{ font-size: 0.85rem; color: #666; }}
    .diag {{ padding: 0.85rem 1rem; border-radius: 8px; margin: 1rem 0; }}
    .diag.ok {{ background: #E8F3EF; border-left: 4px solid #044A30; }}
    .diag.warn {{ background: #FFF8E6; border-left: 4px solid #EAA958; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; margin: 0.75rem 0 1.25rem; }}
    th, td {{ border: 1px solid #C5D9CE; padding: 0.45rem 0.55rem; text-align: left; vertical-align: top; }}
    th {{ background: #044A30; color: #fff; }}
    tr:nth-child(even) {{ background: #F7FAF9; }}
    .footer {{ margin-top: 2.5rem; font-size: 0.8rem; color: #888; border-top: 1px solid #ddd; padding-top: 1rem; }}
    @media print {{ body {{ margin: 0.5rem; }} .no-print {{ display: none; }} }}
  </style>
</head>
<body>
  <p class="no-print" style="background:#E8F3EF;padding:0.6rem 1rem;border-radius:8px;">
    Para guardar como PDF: <strong>Archivo → Imprimir → Guardar como PDF</strong>
  </p>
  <h1>Informe ejecutivo — {meta['nombre']}</h1>
  <p class="meta">
    <strong>{titulo_modo}</strong> · {_esc(meta['institucion'])}<br/>
    Fecha: {_esc(fecha)} · Responsable: {_esc(responsable)}<br/>
    Unidad académica: <strong>{_esc(unidad)}</strong>
  </p>

  <h2>Índices principales — qué significan</h2>
  <ul>{bloque_guia}</ul>

  <div class="kpi">
    <div><strong>{imd}%</strong><span>IMD global</span></div>
    <div><strong>{resultado['p_satisfechas']}/{resultado['p_totales']}</strong><span>Prácticas satisfechas</span></div>
    <div><strong>{resultado['cobertura_pct']}%</strong><span>Cobertura línea de base</span></div>
    <div><strong>{resultado['ia']['ratio_pct']}%</strong><span>Dimensión IA</span></div>
  </div>

  <div class="diag {diag_class}">{_esc(diag)}</div>

  <p>Fórmula: {_esc(resultado['formula'])}</p>

  <h2>IMD por área de madurez</h2>
  {tabla_area}

  <h2>IMD por reto estratégico</h2>
  {tabla_reto}

  <h2>Brechas prioritarias (top 10)</h2>
  <p style="font-size:0.92rem;color:#555">Indicadores respondidos que aún no alcanzan el umbral. Se ordenan por magnitud de la brecha.</p>
  {tabla_brechas}

  <h2>Acciones recomendadas — Fase 2</h2>
  {acciones_fase2}

  <h2>Detalle de indicadores evaluados</h2>
  {tabla_det}

  <div class="footer">
    Generado por MDeIA UCCuyo v{meta['version']} · Referencias: {', '.join(_esc(r) for r in meta['referencias'])}
  </div>
</body>
</html>"""
