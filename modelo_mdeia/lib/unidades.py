# -*- coding: utf-8 -*-
"""Unidades académicas UCCuyo — misma nomenclatura que Consejo de Investigación."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import streamlit as st

from constants import FASE1_CORTO, IMD_FASE1_LABEL, INSTITUTION_NAME
from lib.mdeia_model import calcular_imd, load_indicadores, normalizar_respuestas, pilot_codigos, progreso_piloto

_DATA = Path(__file__).resolve().parent.parent / "data"
DEFAULT_UNIDAD = "INSTITUCIONAL"
SIN_UNIDAD = "__sin_seleccion__"
_SUFIJO_SEDE = {
    "san_luis": "Sede San Luis",
    "san_juan": "Sede San Juan",
    "mendoza": "Sede Mendoza",
}
_catalog: dict | None = None
_catalog_mtime: float = 0.0


def load_unidades_catalogo() -> dict:
    global _catalog, _catalog_mtime
    path = _DATA / "unidades_academicas.json"
    mtime = path.stat().st_mtime
    if _catalog is None or mtime != _catalog_mtime:
        with path.open(encoding="utf-8") as f:
            _catalog = json.load(f)
        _catalog_mtime = mtime
    return _catalog


SEDES_IMD = ("mendoza", "san_luis", "san_juan")
SEDE_VIRTUAL_PREFIX = "SEDE_"


def id_sede_virtual(grupo_id: str) -> str:
    return f"{SEDE_VIRTUAL_PREFIX}{grupo_id}"


def es_seleccion_sede(unidad_id: str) -> bool:
    return unidad_id.startswith(SEDE_VIRTUAL_PREFIX)


def es_seleccion_institucional(unidad_id: str) -> bool:
    if unidad_id == DEFAULT_UNIDAD:
        return True
    u = unidades_index().get(unidad_id)
    return bool(u and u.get("es_institucional_consolidada"))


def es_ambito_macro(unidad_id: str) -> bool:
    """Sede consolidada o institución completa (diagnóstico con preguntas adaptadas)."""
    return es_seleccion_sede(unidad_id) or es_seleccion_institucional(unidad_id)


def grupo_id_desde_seleccion(unidad_id: str) -> str | None:
    if es_seleccion_sede(unidad_id):
        return unidad_id[len(SEDE_VIRTUAL_PREFIX) :]
    return None


def _entry_sede_consolidada(grupo: dict) -> dict:
    return {
        "id": id_sede_virtual(grupo["id"]),
        "sigla": grupo["nombre"],
        "nombre": f"{grupo['nombre']} (consolidado)",
        "label": f"{grupo['nombre']} (consolidado)",
        "grupo_id": grupo["id"],
        "grupo_nombre": grupo["nombre"],
        "grupo_tipo": "sede_consolidada",
        "es_sede_consolidada": True,
    }


def unidades_index() -> dict[str, dict]:
    idx: dict[str, dict] = {}
    for grupo in load_unidades_catalogo()["grupos"]:
        if grupo.get("tipo") == "sede" and grupo["id"] in SEDES_IMD:
            idx[id_sede_virtual(grupo["id"])] = _entry_sede_consolidada(grupo)
        for u in grupo["unidades"]:
            item = dict(u)
            item["grupo_id"] = grupo["id"]
            item["grupo_nombre"] = grupo["nombre"]
            item["grupo_tipo"] = grupo.get("tipo", "")
            if grupo.get("tipo") == "institucional":
                item["es_institucional_consolidada"] = True
            idx[u["id"]] = item
    return idx


def texto_indicador_para_ambito(texto: str, unidad_id: str) -> str:
    """Adapta el enunciado al ámbito institucional, sede o facultad."""
    u = unidad_por_id(unidad_id)
    if not u:
        return texto
    if u.get("es_institucional_consolidada"):
        return (
            f"Ámbito: {INSTITUTION_NAME} (toda la institución, todas las sedes y unidades). "
            f"{texto}"
        )
    if not u.get("es_sede_consolidada"):
        return texto
    sede = u.get("grupo_nombre", "esta sede")
    t = texto
    for viejo, nuevo in (
        ("la institución", "la sede"),
        ("La institución", "La sede"),
        ("institución", "sede"),
        ("Institución", "Sede"),
    ):
        t = t.replace(viejo, nuevo)
    return (
        f"Ámbito: {sede} (evaluar la sede en su totalidad, no una sola facultad). "
        f"{t}"
    )


def unidad_por_id(unidad_id: str) -> dict | None:
    return unidades_index().get(unidad_id)


def unidad_label(unidad_id: str) -> str:
    if not unidad_id or unidad_id == SIN_UNIDAD:
        return "— Elegí un ámbito —"
    u = unidad_por_id(unidad_id)
    if not u:
        return unidad_id
    return _label_con_sede(u)


def _label_con_sede(u: dict) -> str:
    """Asegura el sufijo de sede al final del label mostrado en la UI."""
    if u.get("es_sede_consolidada") or u.get("es_institucional_consolidada"):
        return u.get("label") or u.get("nombre") or ""
    label = (u.get("label") or u.get("nombre") or "").strip()
    sufijo = _SUFIJO_SEDE.get(u.get("grupo_id", ""))
    if not sufijo or label.endswith(sufijo):
        return label
    if label.endswith("San Juan") and sufijo == "Sede San Juan":
        return f"{label[:-len('San Juan')].rstrip()} {sufijo}"
    if label.endswith("San Luis") and sufijo == "Sede San Luis":
        return f"{label[:-len('San Luis')].rstrip()} {sufijo}"
    return f"{label} {sufijo}"


def _default_meta_informe(unidad_id: str) -> dict:
    u = unidad_por_id(unidad_id)
    if u:
        sede = u.get("grupo_nombre", "Institucional")
    else:
        sede = "Institucional"
    return {
        "fecha": date.today().isoformat(),
        "responsable": "Observatorio de IA · UCCuyo",
        "sede": sede,
        "unidad_id": unidad_id,
        "unidad_label": unidad_label(unidad_id),
    }


def _empty_unidad_data(unidad_id: str) -> dict:
    return {"respuestas": {}, "meta_informe": _default_meta_informe(unidad_id)}


def hay_unidad_activa() -> bool:
    uid = st.session_state.get("mdeia_unidad_activa", SIN_UNIDAD)
    return bool(uid and uid != SIN_UNIDAD and uid in unidades_index())


def _normalizar_unidad_sin_default() -> None:
    """Sin elección explícita, no dejar INSTITUCIONAL marcada vacía como activa."""
    if st.session_state.get("mdeia_unidad_elegida_explicita"):
        return
    uid = st.session_state.get("mdeia_unidad_activa")
    if uid != DEFAULT_UNIDAD:
        return
    store = st.session_state.get("mdeia_unidades_data") or {}
    if not (store.get(DEFAULT_UNIDAD) or {}).get("respuestas"):
        st.session_state.mdeia_unidad_activa = SIN_UNIDAD


def init_session_store() -> None:
    """Inicializa almacenamiento por unidad académica."""
    if "mdeia_unidad_activa" not in st.session_state:
        st.session_state.mdeia_unidad_activa = SIN_UNIDAD

    if "mdeia_unidades_data" not in st.session_state:
        st.session_state.mdeia_unidades_data = {}

    store: dict[str, dict] = st.session_state.mdeia_unidades_data
    for uid in unidades_index():
        store.setdefault(uid, _empty_unidad_data(uid))

    _normalizar_unidad_sin_default()

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
    if uid == SIN_UNIDAD:
        return {"respuestas": {}, "meta_informe": {}}
    if uid not in st.session_state.mdeia_unidades_data:
        st.session_state.mdeia_unidades_data[uid] = _empty_unidad_data(uid)
    return st.session_state.mdeia_unidades_data[uid]


def respuestas_activas() -> dict[str, Any]:
    return _slot()["respuestas"]


def sincronizar_respuestas_widgets() -> None:
    """Actualiza respuestas desde widgets antes del sidebar (Streamlit corre sidebar primero)."""
    from lib.mdeia_model import load_indicadores

    valid = {i["codigo"] for i in load_indicadores()}
    resp = respuestas_activas()
    prefix = "mdeia_"
    for key, val in st.session_state.items():
        if not isinstance(key, str) or not key.startswith(prefix):
            continue
        codigo = key[len(prefix) :]
        if codigo in valid and val is not None:
            resp[codigo] = val


def limpiar_respuestas_activas() -> None:
    """Borra respuestas de la unidad activa y resetea widgets mdeia_<codigo> en sesión."""
    from lib.mdeia_model import load_indicadores

    valid = {i["codigo"] for i in load_indicadores()}
    respuestas_activas().clear()
    prefix = "mdeia_"
    for key in list(st.session_state.keys()):
        if isinstance(key, str) and key.startswith(prefix):
            codigo = key[len(prefix) :]
            if codigo in valid:
                del st.session_state[key]
    for k in ("mdeia_resultado", "mdeia_resultado_piloto", "mdeia_ultima_carga"):
        st.session_state.pop(k, None)


def meta_informe_activa() -> dict:
    return _slot()["meta_informe"]


def set_unidad_activa(unidad_id: str) -> None:
    """Cambia la unidad activa (vía navegación pendiente si el sidebar ya se dibujó)."""
    init_session_store()
    if unidad_id in unidades_index():
        st.session_state.mdeia_nav_unidad = unidad_id
        st.session_state.mdeia_unidad_elegida_explicita = True


def solicitar_seccion(seccion: str) -> None:
    st.session_state.mdeia_nav_seccion = seccion


def aplicar_navegacion_pendiente(*, secciones: list[str] | None = None) -> None:
    """Aplica saltos de menú/unidad antes de instanciar widgets del sidebar."""
    if target := st.session_state.pop("mdeia_nav_seccion", None):
        if secciones is None or target in secciones:
            st.session_state.mdeia_seccion = target
    if uid := st.session_state.pop("mdeia_nav_unidad", None):
        if uid in unidades_index():
            st.session_state.mdeia_unidad_activa = uid
            st.session_state.mdeia_unidad_sidebar = uid
            st.session_state.mdeia_unidad_elegida_explicita = True


def resumen_unidad(unidad_id: str) -> dict[str, Any]:
    resp = _slot(unidad_id)["respuestas"]
    n_piloto, total_piloto = progreso_piloto(resp)
    imd_piloto = None
    if n_piloto:
        imd_piloto = calcular_imd(resp, codigos=pilot_codigos())["imd"]
    out: dict[str, Any] = {
        "unidad_id": unidad_id,
        "label": unidad_label(unidad_id),
        "piloto_n": n_piloto,
        "piloto_total": total_piloto,
        "catalogo_n": len(resp),
        "imd_piloto": imd_piloto,
    }
    if es_seleccion_sede(unidad_id):
        out["es_sede"] = True
    if es_seleccion_institucional(unidad_id):
        out["es_institucional"] = True
    return out


def tabla_resumen_unidades() -> list[dict]:
    rows = []
    for grupo in load_unidades_catalogo()["grupos"]:
        for u in grupo["unidades"]:
            r = resumen_unidad(u["id"])
            r["grupo"] = grupo["nombre"]
            rows.append(r)
    return rows


def unidades_ids_grupo(grupo_id: str) -> list[str]:
    for grupo in load_unidades_catalogo()["grupos"]:
        if grupo["id"] == grupo_id:
            return [u["id"] for u in grupo["unidades"]]
    return []


def unidades_ids_evaluables() -> list[str]:
    """Facultades, departamentos y transversales (excluye sede/institución consolidada)."""
    return [
        uid
        for uid, u in unidades_index().items()
        if not u.get("es_sede_consolidada") and not u.get("es_institucional_consolidada")
    ]


def calcular_imd_pooled(
    unidad_ids: list[str],
    *,
    etiqueta: str = "",
    codigos: set[str] | None = None,
) -> dict:
    """IMD pooled: Σ satisfechos / Σ evaluados sobre una lista de unidades."""
    init_session_store()
    codigos = codigos if codigos is not None else pilot_codigos()
    evaluados = 0
    satisfechos = 0
    unidades_con_datos = 0
    detalle: list[dict[str, Any]] = []
    for uid in unidad_ids:
        resp = _slot(uid)["respuestas"]
        r = calcular_imd(resp, codigos=codigos) if resp else None
        u_eval = r["p_totales"] if r else 0
        u_sat = r["p_satisfechas"] if r else 0
        if u_eval:
            unidades_con_datos += 1
        evaluados += u_eval
        satisfechos += u_sat
        detalle.append(
            {
                "unidad_id": uid,
                "label": unidad_label(uid),
                "evaluados": u_eval,
                "satisfechos": u_sat,
                "imd": r["imd"] if r and u_eval else None,
            }
        )
    imd = round((satisfechos / evaluados) * 100, 1) if evaluados else None
    return {
        "etiqueta": etiqueta,
        "imd": imd,
        "evaluados": evaluados,
        "satisfechos": satisfechos,
        "unidades_total": len(detalle),
        "unidades_con_datos": unidades_con_datos,
        "detalle_unidades": detalle,
    }


def calcular_imd_sede(grupo_id: str, *, codigos: set[str] | None = None) -> dict:
    """IMD pooled por sede: Σ satisfechos / Σ evaluados de sus unidades académicas."""
    grupo_nombre = next(
        (g["nombre"] for g in load_unidades_catalogo()["grupos"] if g["id"] == grupo_id),
        grupo_id,
    )
    out = calcular_imd_pooled(
        unidades_ids_grupo(grupo_id),
        etiqueta=grupo_nombre,
        codigos=codigos,
    )
    return {**out, "grupo_id": grupo_id, "grupo_nombre": grupo_nombre}


def tabla_imd_por_sede(*, codigos: set[str] | None = None) -> list[dict]:
    return [calcular_imd_sede(gid, codigos=codigos) for gid in SEDES_IMD]


def resultado_imd_activo(*, codigos: set[str] | None = None) -> dict:
    """IMD de la unidad activa (facultad, sede o transversal)."""
    init_session_store()
    codigos = codigos if codigos is not None else pilot_codigos()
    return calcular_imd(respuestas_activas(), codigos=codigos)


def metricas_sidebar_activa() -> dict[str, Any]:
    """Métricas del sidebar según la unidad activa."""
    if not hay_unidad_activa():
        total = len(pilot_codigos())
        return {
            "es_sede": False,
            "linea_base": f"0 / {total}",
            "imd": None,
            "catalogo": 0,
            "catalogo_total": len(load_indicadores()),
        }
    res = resumen_unidad(st.session_state.mdeia_unidad_activa)
    return {
        "es_sede": bool(res.get("es_sede")),
        "linea_base": f"{res['piloto_n']} / {res['piloto_total']}",
        "imd": res["imd_piloto"],
        "catalogo": res["catalogo_n"],
        "catalogo_total": len(load_indicadores()),
    }


def render_comparativa_referencia(unidad_id: str | None = None) -> None:
    """Referencia pooled (facultades de la sede o de toda la UCCuyo)."""
    import pandas as pd

    uid = unidad_id or st.session_state.mdeia_unidad_activa

    if es_seleccion_sede(uid):
        gid = grupo_id_desde_seleccion(uid)
        if not gid:
            return
        s = calcular_imd_sede(gid)
        titulo = "Referencia: agregado de facultades de la sede (pooled)"
        ayuda = (
            "Comparación informativa. El IMD oficial de la sede es el que respondés "
            "en este diagnóstico; el pooled suma las respuestas ya cargadas en cada facultad."
        )
        vacio = "Ninguna facultad de esta sede tiene datos cargados todavía."
    elif es_seleccion_institucional(uid):
        s = calcular_imd_pooled(
            unidades_ids_evaluables(),
            etiqueta=INSTITUTION_NAME,
        )
        titulo = "Referencia: agregado de unidades académicas UCCuyo (pooled)"
        ayuda = (
            "Comparación informativa. El IMD institucional oficial es el que respondés "
            "en este diagnóstico; el pooled suma las respuestas ya cargadas en sedes, "
            "facultades y unidades transversales."
        )
        vacio = "Ninguna unidad académica tiene datos cargados todavía."
    else:
        return

    with st.expander(titulo, expanded=False):
        st.caption(ayuda)
        if not s["evaluados"]:
            st.caption(vacio)
            return
        c1, c2, c3 = st.columns(3)
        c1.metric("IMD pooled referencia", f"{s['imd']} %" if s["imd"] is not None else "—")
        c2.metric("Satisfechas", f"{s['satisfechos']}/{s['evaluados']}")
        c3.metric("Unidades con datos", f"{s['unidades_con_datos']}/{s['unidades_total']}")
        df = pd.DataFrame(s["detalle_unidades"])
        if not df.empty:
            df = df.rename(
                columns={
                    "label": "Unidad",
                    "evaluados": "Evaluados",
                    "satisfechos": "Satisfechos",
                    "imd": "IMD (%)",
                }
            )
            st.dataframe(
                df[["Unidad", "Evaluados", "Satisfechos", "IMD (%)"]],
                use_container_width=True,
                hide_index=True,
            )
        if es_seleccion_institucional(uid):
            st.markdown("##### IMD por sede (diagnósticos propios de sede)")
            filas_sede = []
            for row in tabla_imd_por_sede():
                resp_sede = _slot(id_sede_virtual(row["grupo_id"]))["respuestas"]
                imd_propio = None
                if resp_sede:
                    imd_propio = calcular_imd(resp_sede, codigos=pilot_codigos())["imd"]
                filas_sede.append(
                    {
                        "Sede": row["grupo_nombre"],
                        "IMD diagnóstico sede": imd_propio,
                        "IMD pooled facultades": row["imd"],
                    }
                )
            st.dataframe(pd.DataFrame(filas_sede), use_container_width=True, hide_index=True)


def render_comparativa_facultades_sede(unidad_id: str | None = None) -> None:
    """Alias retrocompatible."""
    render_comparativa_referencia(unidad_id)


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
    ids = [SIN_UNIDAD] + list(unidades_index().keys())
    if "mdeia_unidad_sidebar" not in st.session_state:
        st.session_state.mdeia_unidad_sidebar = st.session_state.mdeia_unidad_activa
    if st.session_state.mdeia_unidad_sidebar not in ids:
        st.session_state.mdeia_unidad_sidebar = SIN_UNIDAD

    st.selectbox(
        "Unidad académica",
        options=ids,
        key="mdeia_unidad_sidebar",
        format_func=unidad_label,
    )
    st.session_state.mdeia_unidad_activa = st.session_state.mdeia_unidad_sidebar
    if st.session_state.mdeia_unidad_activa != SIN_UNIDAD:
        st.session_state.mdeia_unidad_elegida_explicita = True

    if not hay_unidad_activa():
        st.caption(f"{FASE1_CORTO}: elegí un ámbito")
        return

    res = resumen_unidad(st.session_state.mdeia_unidad_activa)
    st.caption(f"{FASE1_CORTO}: {res['piloto_n']}/{res['piloto_total']}")
    if res["imd_piloto"] is not None:
        st.caption(f"{IMD_FASE1_LABEL}: {res['imd_piloto']} %")
