# -*- coding: utf-8 -*-
"""Conexión MDeIA UCCuyo ↔ encuesta estudiantil (Google Sheets o export Forms → Excel)."""

from __future__ import annotations

import json
import re
import time
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

import pandas as pd

_DATA = Path(__file__).resolve().parent.parent / "data"

FREQ_HIGH_TERMS = frozenset(
    {
        "frecuentemente",
        "siempre",
        "habitualmente",
        "a diario",
        "casi siempre",
        "muchas veces",
        "muy frecuentemente",
    }
)

_TIMESTAMP_HINTS = ("marca temporal", "timestamp", "fecha y hora", "fecha/hora")


def _normalize_cell(val: Any) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return re.sub(r"\s+", " ", str(val).strip().lower())


def load_oia_config() -> dict:
    with (_DATA / "oia_encuesta.json").open(encoding="utf-8") as f:
        return json.load(f)


def sheet_export_url(sheet_id: str, gid: str | int = "0") -> str:
    return (
        f"https://docs.google.com/spreadsheets/d/{sheet_id.strip()}/export"
        f"?format=csv&gid={gid}"
    )


def is_timestamp_column(name: str) -> bool:
    lc = str(name).lower()
    return any(h in lc for h in _TIMESTAMP_HINTS)


def _usage_frequency_columns(df: pd.DataFrame) -> list[str]:
    out: list[str] = []
    for c in df.columns:
        if is_timestamp_column(c):
            continue
        lc = str(c).lower().replace("\n", " ")
        if "frecuencia" in lc and "inteligencia artificial" in lc:
            out.append(str(c))
        elif "indicá con qué frecuencia" in lc or "indica con qué frecuencia" in lc:
            out.append(str(c))
        elif "usos posibles" in lc and "[" in str(c):
            out.append(str(c))
    return out


def _filas_validas(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    data_cols = [c for c in df.columns if not is_timestamp_column(c)]
    if not data_cols:
        return df.iloc[0:0]
    mask = df[data_cols].notna().any(axis=1)
    for c in data_cols:
        mask |= df[c].astype(str).str.strip().astype(bool)
    return df.loc[mask].copy()


def _pct_uso_ia_alto(df: pd.DataFrame) -> float | None:
    cols = _usage_frequency_columns(df)
    grid = [
        c
        for c in df.columns
        if not is_timestamp_column(c)
        and ("usos posibles" in str(c).lower() or "indicá con qué frecuencia" in str(c).lower())
        and "[" in str(c)
    ]
    if not grid:
        grid = [c for c in cols if "[" in str(c)]
    if not grid:
        grid = cols
    if not grid:
        return None

    any_high = pd.Series(False, index=df.index)
    for c in grid:
        s = df[c]
        text_high = s.map(_normalize_cell).isin(FREQ_HIGH_TERMS)
        any_high |= text_high
    if not len(df):
        return None
    return round(float(any_high.mean()) * 100, 1)


def fetch_sheet_csv(sheet_id: str, gid: str | int = "0", *, timeout: int = 30) -> pd.DataFrame:
    url = sheet_export_url(sheet_id, gid)
    try:
        with urlopen(url, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except URLError as exc:
        raise ConnectionError(
            "No se pudo leer la planilla. Verificá que esté publicada "
            "(Anyone with the link → Viewer) o usá export Excel desde Forms."
        ) from exc
    return pd.read_csv(StringIO(raw), low_memory=False)


def load_uploaded_file(name: str, data: bytes) -> pd.DataFrame:
    lower = name.lower()
    if lower.endswith((".xlsx", ".xls")):
        return pd.read_excel(BytesIO(data))
    if lower.endswith(".csv"):
        return pd.read_csv(BytesIO(data))
    raise ValueError("Formato no soportado. Usá .xlsx (Google Forms) o .csv")


def metricas_desde_cifras(
    *,
    n_respuestas: int,
    poblacion: int | None = None,
    tasa_pct: float | None = None,
) -> dict[str, Any]:
    """Construye métricas OIA a partir de cifras conocidas (sin archivo ni Sheet)."""
    n = max(0, int(n_respuestas))
    tasa = tasa_pct
    if tasa is None and poblacion and poblacion > 0:
        tasa = round(min(100.0, (n / poblacion) * 100), 1)
    return {
        "n_respuestas": n,
        "poblacion_objetivo": poblacion,
        "tasa_respuesta_pct": tasa,
        "columnas_ia_detectadas": 0,
        "pct_uso_ia_alto": None,
        "fecha_analisis": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "origen": "manual",
    }


def analizar_encuesta(df: pd.DataFrame, *, poblacion: int | None = None) -> dict[str, Any]:
    """Resume la encuesta para alimentar indicadores MDeIA."""
    df = _filas_validas(df)
    n = len(df)
    cols_ia = _usage_frequency_columns(df)
    pct_alto = _pct_uso_ia_alto(df)

    tasa: float | None = None
    if poblacion and poblacion > 0:
        tasa = round(min(100.0, (n / poblacion) * 100), 1)

    return {
        "n_respuestas": n,
        "poblacion_objetivo": poblacion,
        "tasa_respuesta_pct": tasa,
        "columnas_ia_detectadas": len(cols_ia),
        "pct_uso_ia_alto": pct_alto,
        "fecha_analisis": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "origen": "archivo",
    }


def nivel_observatorio(n_respuestas: int) -> int:
    if n_respuestas >= 50:
        return 4
    if n_respuestas >= 10:
        return 3
    if n_respuestas >= 1:
        return 2
    return 0


def aplicar_metricas_mdeia(
    metricas: dict[str, Any],
    respuestas: dict[str, Any],
    *,
    config: dict | None = None,
) -> dict[str, Any]:
    """Precarga indicadores MDeIA desde métricas de la encuesta estudiantil."""
    cfg = config or load_oia_config()
    mapping = cfg.get("indicadores_mdeia", cfg.get("indicadores_cljl", {}))
    out = dict(respuestas)
    n = int(metricas.get("n_respuestas") or 0)

    cod_obs = mapping.get("observatorio_activo", "MDEIA_IA_OBSERVATORIO")
    out[cod_obs] = nivel_observatorio(n)

    cod_tasa = mapping.get("tasa_respuesta", "MDEIA_IA_ENCUESTA")
    tasa = metricas.get("tasa_respuesta_pct")
    if tasa is not None:
        out[cod_tasa] = float(tasa)
    elif n > 0:
        # Sin población declarada: registrar cantidad como referencia (cap 100)
        out[cod_tasa] = float(min(100, n))

    return out


def resumen_markdown(metricas: dict[str, Any]) -> str:
    lines = [
        f"- **Respuestas válidas:** {metricas.get('n_respuestas', 0)}",
    ]
    if metricas.get("poblacion_objetivo"):
        lines.append(f"- **Población objetivo:** {metricas['poblacion_objetivo']}")
    if metricas.get("tasa_respuesta_pct") is not None:
        lines.append(f"- **Tasa de respuesta:** {metricas['tasa_respuesta_pct']} %")
    else:
        lines.append("- **Tasa de respuesta:** definí población objetivo para calcularla")
    if metricas.get("pct_uso_ia_alto") is not None:
        lines.append(f"- **Uso frecuente de IA (heurística):** {metricas['pct_uso_ia_alto']} %")
    lines.append(f"- **Columnas IA detectadas:** {metricas.get('columnas_ia_detectadas', 0)}")
    return "\n".join(lines)
