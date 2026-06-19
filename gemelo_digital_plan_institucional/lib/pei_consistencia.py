# -*- coding: utf-8 -*-
"""Índice de consistencia actividad ↔ objetivo del PEI (planilla Google Sheets)."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path

import pandas as pd

from lib.pei_sheets import (
    OG_NOMBRES,
    _celda_con_actividad,
    _columnas_actividades,
    _conteo_por_og,
    _texto_actividad,
    fetch_planilla_pei,
)

ROOT = Path(__file__).resolve().parent.parent
CATALOGO_OE_PATH = ROOT / "data" / "objetivos_especificos_catalogo.json"

SPANISH_STOPWORDS = frozenset(
    """
    a al algo alguna alguno ante antes como con contra cual cuales cuando de del desde donde el
    en entre es esa ese eso esta este esto fue ha han hay he la las le lo los mas me mi mis muy
    ni no nos o os otro para pero por que se si sin sobre su sus te un una uno y ya
    """.split()
)


def _normalize_text(text: str) -> str:
    s = str(text or "").lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9áéíóúñü\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _tokenize(text: str) -> list[str]:
    return [t for t in _normalize_text(text).split() if t not in SPANISH_STOPWORDS and len(t) > 2]


def _overlap_score(left: str, right: str) -> float:
    """Solapamiento léxico normalizado (0–1), alineado a la calculadora de consistencia PEI."""
    a = set(_tokenize(left))
    b = set(_tokenize(right))
    if not a or not b:
        return 0.0
    inter = len(a & b)
    denom = (len(a) * len(b)) ** 0.5
    return inter / denom if denom else 0.0


def _columnas_objetivos_especificos(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if str(c).strip().startswith("Objetivos específicos")]


def _columnas_detalle_actividad(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if str(c).strip().startswith("Detalle de la Actividad Objetivo")]


def _cosine_tfidf(left: str, right: str) -> float:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        return _overlap_score(left, right)
    docs = [_normalize_text(left), _normalize_text(right)]
    if not docs[0] or not docs[1]:
        return 0.0
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95)
    matrix = vectorizer.fit_transform(docs)
    sim = float(cosine_similarity(matrix[0:1], matrix[1:2])[0, 0])
    return max(0.0, min(1.0, sim))


def _score_actividad_objetivo(actividad: str, obj_especifico: str, og_nombre: str) -> float:
    """Puntaje 0–1: relación textual entre actividad y objetivo declarado."""
    scores: list[float] = []
    if obj_especifico.strip():
        scores.append(0.80 * _cosine_tfidf(actividad, obj_especifico) + 0.20 * _overlap_score(actividad, obj_especifico))
    if og_nombre.strip():
        scores.append(0.55 * _cosine_tfidf(actividad, og_nombre) + 0.45 * _overlap_score(actividad, og_nombre))
    if not scores:
        return 0.0
    return max(scores)


@lru_cache(maxsize=1)
def _catalogo_objetivos_especificos() -> dict[int, list[dict]]:
    """Objetivos específicos del PEI agrupados por OG (catálogo institucional)."""
    with open(CATALOGO_OE_PATH, encoding="utf-8") as f:
        data = json.load(f)
    by_og: dict[int, list[dict]] = {}
    for item in data.get("objetivos", []):
        by_og.setdefault(int(item["og_id"]), []).append(item)
    return by_og


def _mejor_match_catalogo(actividad: str, og_id: int, og_nombre: str) -> tuple[float, str]:
    """Mejor puntaje léxico contra cualquier OE del catálogo para el OG dado."""
    subset = _catalogo_objetivos_especificos().get(og_id, [])
    if not subset:
        return 0.0, ""
    og_score = 0.0
    if og_nombre.strip():
        og_score = 0.55 * _cosine_tfidf(actividad, og_nombre) + 0.45 * _overlap_score(actividad, og_nombre)
    best_score = og_score
    best_label = ""
    for item in subset:
        texto = str(item.get("texto", "")).strip()
        if not texto:
            continue
        spec = 0.80 * _cosine_tfidf(actividad, texto) + 0.20 * _overlap_score(actividad, texto)
        score = max(spec, og_score)
        if score > best_score:
            best_score = score
            codigo = str(item.get("codigo", "")).strip()
            best_label = f"{codigo}. {texto}" if codigo else texto
    return best_score, best_label


def _puntaje_consistencia(actividad: str, obj_esp: str, og_id: int, og_nombre: str) -> tuple[float, str]:
    """Combina OE declarado en planilla con mejor match del catálogo por OG."""
    score_decl = _score_actividad_objetivo(actividad, obj_esp, og_nombre)
    score_cat, oe_cat = _mejor_match_catalogo(actividad, og_id, og_nombre)
    if score_cat > score_decl:
        return score_cat, oe_cat
    if obj_esp.strip():
        return score_decl, obj_esp.strip()
    return score_decl, oe_cat


def invalidar_cache_consistencia() -> None:
    """Limpia resultados cacheados (p. ej. tras actualizar la planilla)."""
    actividades_consistencia_df.cache_clear()


@lru_cache(maxsize=8)
def actividades_consistencia_df(anio: int) -> pd.DataFrame:
    """Una fila por actividad con puntaje de consistencia respecto del OG donde se cargó."""
    df = fetch_planilla_pei()
    df = df[df["AÑO"] == anio].copy()
    cols_act = _columnas_actividades(df)
    cols_obj = _columnas_objetivos_especificos(df)
    cols_det = _columnas_detalle_actividad(df)
    if len(cols_act) != 6:
        raise ValueError("La planilla no tiene las 6 columnas de actividades por objetivo.")

    rows: list[dict] = []
    for _, row in df.iterrows():
        for og_id, col_act in enumerate(cols_act, start=1):
            if not _celda_con_actividad(row[col_act]):
                continue
            act = _texto_actividad(row[col_act])
            det = ""
            if og_id - 1 < len(cols_det) and _celda_con_actividad(row.get(cols_det[og_id - 1])):
                det = _texto_actividad(row[cols_det[og_id - 1]])
            actividad = f"{act} {det}".strip()
            obj_esp = ""
            if og_id - 1 < len(cols_obj) and _celda_con_actividad(row.get(cols_obj[og_id - 1])):
                obj_esp = _texto_actividad(row[cols_obj[og_id - 1]])
            og_nombre = OG_NOMBRES[og_id]
            score, oe_correlacionado = _puntaje_consistencia(actividad, obj_esp, og_id, og_nombre)
            tokens_a = _tokenize(actividad)
            tokens_ref = _tokenize(f"{oe_correlacionado} {og_nombre}")
            coincidencias = [t for t in tokens_a if t in set(tokens_ref)]
            top_terms = ", ".join(w for w, _ in Counter(coincidencias).most_common(4))
            rows.append(
                {
                    "og_id": og_id,
                    "og": f"OG{og_id}",
                    "og_nombre": og_nombre,
                    "actividad": act,
                    "objetivo_especifico": obj_esp,
                    "objetivo_especifico_correlacionado": oe_correlacionado,
                    "puntaje_raw": score,
                    "coincidencias": top_terms,
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    pmin = float(out["puntaje_raw"].min())
    pmax = float(out["puntaje_raw"].max())
    if pmax > pmin:
        out["consistencia"] = ((out["puntaje_raw"] - pmin) / (pmax - pmin) * 100).round(1)
    else:
        out["consistencia"] = 50.0
    return out.copy()


def consistencia_resumen(anio: int) -> tuple[float, pd.DataFrame, pd.DataFrame]:
    """Índice global, resumen por OG y detalle (un solo cálculo cacheado)."""
    detalle = actividades_consistencia_df(anio)
    if detalle.empty:
        vacio = pd.DataFrame(
            columns=[
                "og_id",
                "og",
                "objetivo_general",
                "indice_consistencia",
                "actividades_distintas",
                "cargas_analizadas",
            ]
        )
        return 0.0, vacio, detalle
    indice = round(float(detalle["consistencia"].mean()), 1)
    por_og = indice_consistencia_por_objetivo_df(anio)
    return indice, por_og, detalle


def indice_consistencia_por_objetivo_df(anio: int) -> pd.DataFrame:
    """Promedio de consistencia por objetivo general."""
    detalle = actividades_consistencia_df(anio)
    if detalle.empty:
        return pd.DataFrame(
            columns=[
                "og_id",
                "og",
                "objetivo_general",
                "indice_consistencia",
                "actividades_distintas",
                "cargas_analizadas",
            ]
        )
    agg = (
        detalle.groupby(["og_id", "og", "og_nombre"], as_index=False)
        .agg(
            indice_consistencia=("consistencia", "mean"),
            cargas_analizadas=("consistencia", "count"),
        )
        .rename(columns={"og_nombre": "objetivo_general"})
    )
    agg["indice_consistencia"] = agg["indice_consistencia"].round(1)

    df = fetch_planilla_pei()
    df_anio = df[df["AÑO"] == anio]
    cols_act = _columnas_actividades(df_anio)
    conteos_distintos = _conteo_por_og(df_anio, cols_act)
    agg["actividades_distintas"] = [conteos_distintos[int(og) - 1] for og in agg["og_id"]]

    return agg.sort_values("og_id").reset_index(drop=True)


def indice_consistencia_general(anio: int) -> float:
    """Índice global (0–100): promedio ponderado de consistencia de todas las actividades."""
    detalle = actividades_consistencia_df(anio)
    if detalle.empty:
        return 0.0
    return round(float(detalle["consistencia"].mean()), 1)
