# -*- coding: utf-8 -*-
"""Unidades académicas UCCuyo — misma nomenclatura que Consejo de Investigación."""

from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

import streamlit as st

from constants import FASE1_CORTO, IMD_FASE1_LABEL
from lib.mdeia_model import calcular_imd, normalizar_respuestas, pilot_codigos, progreso_piloto

_DATA = Path(__file__).resolve().parent.parent / "data"
DEFAULT_UNIDAD = "INSTITUCIONAL"


@lru_cache(maxsize=1)
def load_unidades_catalogo() -> dict:
    with (_DATA / "unidades_academicas.json").open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def unidades_index() -> dict[str, dict]:
    idx: dict[str, dict] = {}
    for grupo in load_unidades_catalogo()["grupos"]:
        for u in grupo["unidades"]:
            item = dict(u)
            item["grupo_id"] = grupo["id"]
            item["grupo_nombre"] = grupo["nombre"]
            idx[u["id"]] = item
    return idx


def unidad_por_id(unidad_id: str) -> dict | None:
    return unidades_index().get(unidad_id)


def unidad_label(unidad_id: str) -> str:
    u = unidad_por_id(unidad_id)
    return u["label"] if u else unidad_id


def _default_meta_informe(unidad_id: str) -> dict:
    u = unidad_por_id(unidad_id)
    sede = u.get("grupo_nombre", "Institucional") if u else "Institucional"
    return {
        "fecha": date.today().isoformat(),
        "responsable": "Observatorio de IA · UCCuyo",
        "sede": u["nombre"] if u else sede,
        "unidad_id": unidad_id,
        "unidad_label": unidad_label(unidad_id),
    }


def _empty_unidad_data(unidad_id: str) -> dict:
    return {"respuestas": {}, "meta_informe": _default_meta_informe(unidad_id)}


def init_session_store() -> None:
    """Inicializa almacenamiento por unidad académica."""
    if "mdeia_unidad_activa" not in st.session_state:
        st.session_state.mdeia_unidad_activa = DEFAULT_UNIDAD

    if "mdeia_unidades_data" not in st.session_state:
        st.session_state.mdeia_unidades_data = {}

    store: dict[str, dict] = st.session_state.mdeia_unidades_data
    for uid in unidades_index():
        store.setdefault(uid, _empty_unidad_data(uid))

    # Migración desde sesión plana anterior
    if st.session_state.get("mdeia_respuestas"):
        legacy = normalizar_respuestas(dict(st.session_state.mdeia_respuestas))
        store[DEFAULT_UNIDAD]["respuestas"].update(legacy)
        del st.session_state["mdeia_respuestas"]

    if st.session_state.get("mdeia_meta_informe"):
        store[DEFAULT_UNIDAD]["meta_informe"].update(st.session_state.mdeia_meta_informe)
        del st.session_state["mdeia_meta_informe"]


def _slot(unidad_id: str | None = None) -> dict:
    init_session_store()
    uid = unidad_id or st.session_state.mdeia_unidad_activa
    if uid not in st.session_state.mdeia_unidades_data:
        st.session_state.mdeia_unidades_data[uid] = _empty_unidad_data(uid)
    return st.session_state.mdeia_unidades_data[uid]


def respuestas_activas() -> dict[str, Any]:
    return _slot()["respuestas"]


def meta_informe_activa() -> dict:
    return _slot()["meta_informe"]


def set_unidad_activa(unidad_id: str) -> None:
    init_session_store()
    if unidad_id in unidades_index():
        st.session_state.mdeia_unidad_activa = unidad_id


def resumen_unidad(unidad_id: str) -> dict[str, Any]:
    resp = _slot(unidad_id)["respuestas"]
    n_piloto, total_piloto = progreso_piloto(resp)
    imd_piloto = None
    if n_piloto:
        imd_piloto = calcular_imd(resp, codigos=pilot_codigos())["imd"]
    return {
        "unidad_id": unidad_id,
        "label": unidad_label(unidad_id),
        "piloto_n": n_piloto,
        "piloto_total": total_piloto,
        "catalogo_n": len(resp),
        "imd_piloto": imd_piloto,
    }


def tabla_resumen_unidades() -> list[dict]:
    rows = []
    for grupo in load_unidades_catalogo()["grupos"]:
        for u in grupo["unidades"]:
            r = resumen_unidad(u["id"])
            r["grupo"] = grupo["nombre"]
            rows.append(r)
    return rows


def exportar_todas_unidades(*, evaluador: str = "") -> dict:
    init_session_store()
    unidades_out = {}
    for uid, data in st.session_state.mdeia_unidades_data.items():
        meta = dict(data.get("meta_informe") or {})
        if evaluador:
            meta["evaluador"] = evaluador
        unidades_out[uid] = {
            "label": unidad_label(uid),
            "respuestas": data.get("respuestas") or {},
            "meta_encuesta": meta,
        }
    activa = st.session_state.mdeia_unidad_activa
    resp_activas = unidades_out.get(activa, {}).get("respuestas") or _slot(activa)["respuestas"]
    meta_activa = unidades_out.get(activa, {}).get("meta_encuesta") or _slot(activa)["meta_informe"]
    payload = exportar_diagnostico_unidad(resp_activas, meta=meta_activa)
    payload["unidad_activa"] = activa
    payload["unidades"] = unidades_out
    return payload


def exportar_diagnostico_unidad(
    respuestas: dict[str, Any],
    meta: dict | None = None,
    *,
    codigos: set[str] | None = None,
) -> dict:
    from lib.mdeia_model import exportar_diagnostico

    return exportar_diagnostico(respuestas, meta=meta, codigos=codigos)


def fusionar_carga_json(data: dict) -> int:
    """Fusiona JSON exportado (una o todas las unidades). Devuelve cantidad de claves fusionadas."""
    init_session_store()
    merged = 0

    if data.get("unidades"):
        for uid, block in data["unidades"].items():
            if uid not in st.session_state.mdeia_unidades_data:
                st.session_state.mdeia_unidades_data[uid] = _empty_unidad_data(uid)
            incoming = normalizar_respuestas(block.get("respuestas") or {})
            st.session_state.mdeia_unidades_data[uid]["respuestas"].update(incoming)
            if block.get("meta_encuesta"):
                st.session_state.mdeia_unidades_data[uid]["meta_informe"].update(block["meta_encuesta"])
            merged += len(incoming)
        if data.get("unidad_activa"):
            set_unidad_activa(data["unidad_activa"])
    else:
        uid = data.get("unidad_activa") or data.get("meta_encuesta", {}).get("unidad_id") or DEFAULT_UNIDAD
        set_unidad_activa(uid)
        incoming = normalizar_respuestas(data.get("respuestas") or {})
        _slot(uid)["respuestas"].update(incoming)
        if data.get("meta_encuesta"):
            _slot(uid)["meta_informe"].update(data["meta_encuesta"])
        merged = len(incoming)

    return merged


def reemplazar_respuestas_activas(respuestas: dict) -> None:
    _slot()["respuestas"] = dict(respuestas)


def actualizar_meta_informe_activa(meta: dict) -> None:
    _slot()["meta_informe"].update(meta)


def render_selector_unidades_sidebar() -> None:
    """Selector por unidad — misma lista que Consejo de Investigación."""
    init_session_store()
    activa = st.session_state.mdeia_unidad_activa
    ids = list(unidades_index().keys())
    try:
        idx = ids.index(activa)
    except ValueError:
        idx = 0

    # Sin key= en el selectbox: permite cambiar mdeia_unidad_activa desde «Elegir» en Unidades académicas
    elegida = st.selectbox(
        "Unidad académica",
        options=ids,
        index=idx,
        format_func=unidad_label,
    )
    if elegida != st.session_state.mdeia_unidad_activa:
        st.session_state.mdeia_unidad_activa = elegida

    res = resumen_unidad(st.session_state.mdeia_unidad_activa)
    st.caption(f"{FASE1_CORTO}: {res['piloto_n']}/{res['piloto_total']}")
    if res["imd_piloto"] is not None:
        st.caption(f"{IMD_FASE1_LABEL}: {res['imd_piloto']} %")
