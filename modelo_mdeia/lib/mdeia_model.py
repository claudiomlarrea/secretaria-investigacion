# -*- coding: utf-8 -*-
"""MDeIA UCCuyo — lógica de madurez digital e IA adaptada a UCCuyo."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

_DATA = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def load_framework() -> dict:
    with (_DATA / "framework.json").open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_indicadores() -> list[dict]:
    with (_DATA / "indicadores_udigital_comunes.json").open(encoding="utf-8") as f:
        udigital = json.load(f)
    with (_DATA / "indicadores_ia_mdeia.json").open(encoding="utf-8") as f:
        ia = json.load(f)

    out: list[dict] = []
    objetivos = {o["numero"]: o for o in load_framework()["objetivos"]}
    for idx, row in enumerate(udigital, start=1):
        obj_num = row.get("objetivo_num")
        obj_meta = objetivos.get(obj_num, {})
        prefix = row["codigo"][:3]
        area = _area_from_prefix(prefix)
        out.append(
            {
                "id": f"UD-{idx:03d}",
                "codigo": row["codigo"],
                "texto": row["texto"],
                "objetivo_num": obj_num,
                "objetivo_id": obj_meta.get("id"),
                "objetivo_nombre": row.get("objetivo") or obj_meta.get("nombre", ""),
                "reto_id": obj_meta.get("reto"),
                "area": area,
                "comun": bool(row.get("comun", True)),
                "dimension_ia": bool(row.get("dimension_ia", False)),
                "tipo": "nivel",
                "fuente": "udigital",
            }
        )

    for idx, row in enumerate(ia, start=1):
        obj_num = row.get("objetivo_num")
        obj_meta = objetivos.get(obj_num, {}) if obj_num else {}
        out.append(
            {
                "id": f"IA-{idx:03d}",
                "codigo": row["codigo"],
                "texto": row["texto"],
                "objetivo_num": obj_num,
                "objetivo_id": obj_meta.get("id"),
                "objetivo_nombre": row.get("objetivo", ""),
                "reto_id": obj_meta.get("reto"),
                "area": "ia",
                "comun": False,
                "dimension_ia": True,
                "tipo": row.get("tipo", "nivel"),
                "umbral": row.get("umbral"),
                "unidad": row.get("unidad"),
                "fuente": "mdeia",
            }
        )
    return out


def _area_from_prefix(prefix: str) -> str:
    mapping = {
        "GES": "gestion",
        "GEC": "gestion",
        "GEN": "gestion",
        "GEM": "gestion",
        "GOM": "gobierno",
        "GOS": "gobierno",
        "INM": "innovacion",
        "INN": "innovacion",
        "INS": "innovacion",
        "TDS": "transformacion",
        "TDM": "transformacion",
        "TDN": "transformacion",
        "TDC": "transformacion",
    }
    return mapping.get(prefix, "gestion")


@lru_cache(maxsize=1)
def load_piloto() -> dict:
    with (_DATA / "piloto_fase1.json").open(encoding="utf-8") as f:
        return json.load(f)


def pilot_codigos() -> set[str]:
    return {row["codigo"] for row in load_piloto()["indicadores"]}


def indicadores_piloto_df() -> pd.DataFrame:
    codes = pilot_codigos()
    meta_piloto = {r["codigo"]: r for r in load_piloto()["indicadores"]}
    df = indicadores_df()
    df = df[df["codigo"].isin(codes)].copy()
    df["bloque_piloto"] = df["codigo"].map(lambda c: meta_piloto.get(c, {}).get("bloque", ""))
    df["prioridad_piloto"] = df["codigo"].map(lambda c: meta_piloto.get(c, {}).get("prioridad", ""))
    return df


def respuestas_piloto(respuestas: dict[str, Any]) -> dict[str, Any]:
    codes = pilot_codigos()
    return {k: v for k, v in respuestas.items() if k in codes}


def progreso_piloto(respuestas: dict[str, Any]) -> tuple[int, int]:
    codes = pilot_codigos()
    n = sum(1 for c in codes if c in respuestas)
    return n, len(codes)


def retos_df() -> pd.DataFrame:
    fw = load_framework()
    rows = []
    objetivos = {o["id"]: o for o in fw["objetivos"]}
    for reto in fw["retos"]:
        for oid in reto["objetivos"]:
            o = objetivos[oid]
            rows.append(
                {
                    "reto_id": reto["id"],
                    "reto": reto["nombre"],
                    "objetivo_id": oid,
                    "objetivo_num": o["numero"],
                    "objetivo": o["nombre"],
                    "area": o["area_principal"],
                }
            )
    return pd.DataFrame(rows)


def fases_df() -> pd.DataFrame:
    return pd.DataFrame(load_framework()["fases"])


def areas_df() -> pd.DataFrame:
    return pd.DataFrame(load_framework()["areas"])


def _valor_satisface(ind: dict, valor: Any, umbral: int | None = None) -> bool:
    fw = load_framework()
    umbral_nivel = umbral if umbral is not None else fw["umbral_satisfaccion"]
    tipo = ind.get("tipo", "nivel")

    if valor is None:
        return False
    if tipo == "si_no":
        return str(valor).lower() in {"sí", "si", "yes", "true", "1"}
    if tipo in {"porcentaje", "umbral"}:
        try:
            v = float(valor)
        except (TypeError, ValueError):
            return False
        target = ind.get("umbral") if ind.get("umbral") is not None else 60
        return v >= target
    try:
        return int(valor) >= umbral_nivel
    except (TypeError, ValueError):
        return False


def indicadores_df() -> pd.DataFrame:
    return pd.DataFrame(load_indicadores())


def _filtrar_indicadores(
    indicadores: list[dict],
    *,
    solo_comunes: bool = False,
    codigos: set[str] | None = None,
) -> list[dict]:
    out = indicadores
    if solo_comunes:
        out = [i for i in out if i.get("comun")]
    if codigos is not None:
        out = [i for i in out if i["codigo"] in codigos]
    return out


def calcular_imd(
    respuestas: dict[str, Any],
    *,
    solo_comunes: bool = False,
    codigos: set[str] | None = None,
) -> dict:
    """Calcula IMD global y desgloses por área, reto y dimensión IA."""
    fw = load_framework()
    indicadores = _filtrar_indicadores(
        load_indicadores(), solo_comunes=solo_comunes, codigos=codigos
    )

    evaluados = [i for i in indicadores if i["codigo"] in respuestas]
    satisfechos = [
        i for i in evaluados if _valor_satisface(i, respuestas[i["codigo"]])
    ]
    total_ref = len(indicadores)
    p_tot = len(evaluados) or total_ref
    p_sat = len(satisfechos)
    imd = round((p_sat / p_tot) * 100, 1) if p_tot else 0.0

    por_area = _ratio_grupo(evaluados, satisfechos, "area")
    por_reto = _ratio_grupo(evaluados, satisfechos, "reto_id")
    ia_eval = [i for i in evaluados if i.get("dimension_ia")]
    ia_sat = [i for i in satisfechos if i.get("dimension_ia")]

    return {
        "imd": imd,
        "p_satisfechas": p_sat,
        "p_totales": p_tot,
        "p_referencia_catalogo": total_ref,
        "cobertura_pct": round((p_tot / total_ref) * 100, 1) if total_ref else 0,
        "por_area": por_area,
        "por_reto": por_reto,
        "ia": {
            "evaluados": len(ia_eval),
            "satisfechos": len(ia_sat),
            "ratio_pct": round((len(ia_sat) / len(ia_eval)) * 100, 1) if ia_eval else 0,
        },
        "formula": fw["meta"]["formula_imd"],
        "umbral_regional_objetivo": 60.0,
        "modo": "piloto" if codigos else "completo",
    }


def _ratio_grupo(evaluados: list[dict], satisfechos: list[dict], key: str) -> list[dict]:
    sat_codes = {i["codigo"] for i in satisfechos}
    grupos: dict[str, list[dict]] = {}
    for ind in evaluados:
        k = ind.get(key) or "sin_clasificar"
        grupos.setdefault(k, []).append(ind)
    out = []
    for k, items in sorted(grupos.items()):
        sat = sum(1 for i in items if i["codigo"] in sat_codes)
        out.append(
            {
                "grupo": k,
                "evaluados": len(items),
                "satisfechos": sat,
                "ratio_pct": round((sat / len(items)) * 100, 1) if items else 0,
            }
        )
    return out


def detalle_evaluacion(respuestas: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for ind in load_indicadores():
        if ind["codigo"] not in respuestas:
            continue
        val = respuestas[ind["codigo"]]
        rows.append(
            {
                "Código": ind["codigo"],
                "Indicador": ind["texto"],
                "Área": ind["area"],
                "Reto": ind.get("reto_id") or "—",
                "IA": "Sí" if ind.get("dimension_ia") else "No",
                "Valor": val,
                "Satisface": "Sí" if _valor_satisface(ind, val) else "No",
            }
        )
    return pd.DataFrame(rows)


def brechas_prioritarias(respuestas: dict[str, Any], top_n: int = 10) -> pd.DataFrame:
    rows = []
    for ind in load_indicadores():
        if ind["codigo"] not in respuestas:
            continue
        val = respuestas[ind["codigo"]]
        if _valor_satisface(ind, val):
            continue
        try:
            gap = 3 - int(val) if ind.get("tipo") == "nivel" else 1
        except (TypeError, ValueError):
            gap = 3
        rows.append(
            {
                "Código": ind["codigo"],
                "Indicador": ind["texto"],
                "Área": ind["area"],
                "Reto": ind.get("reto_id") or "—",
                "Prioridad": gap,
                "Valor actual": valor_legible(ind, val),
                "Meta": meta_satisface_texto(ind),
                "Interpretación": interpretacion_brecha(ind, val),
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values("Prioridad", ascending=False).head(top_n)


def meta_satisface_texto(ind: dict) -> str:
    tipo = ind.get("tipo", "nivel")
    if tipo == "si_no":
        return "Sí"
    if tipo in {"porcentaje", "umbral"}:
        umbral = ind.get("umbral", 60 if tipo == "porcentaje" else 70)
        unidad = ind.get("unidad") or "%"
        return f"≥ {umbral} {unidad}".strip()
    return "Nivel ≥ 3 (implementado / referente)"


def valor_legible(ind: dict, valor: Any) -> str:
    if valor is None:
        return "—"
    tipo = ind.get("tipo", "nivel")
    if tipo == "si_no":
        return str(valor)
    if tipo in {"porcentaje", "umbral"}:
        unidad = ind.get("unidad") or "%"
        return f"{valor} {unidad}".strip()
    niveles = {n["valor"]: n["etiqueta"] for n in load_framework()["niveles_madurez"]}
    try:
        n = int(valor)
        return f"{n} — {niveles.get(n, 'nivel ' + str(n))}"
    except (TypeError, ValueError):
        return str(valor)


def interpretacion_brecha(ind: dict, valor: Any) -> str:
    tipo = ind.get("tipo", "nivel")
    meta = meta_satisface_texto(ind)
    actual = valor_legible(ind, valor)
    if tipo == "nivel":
        try:
            n = int(valor)
        except (TypeError, ValueError):
            n = None
        if n is not None and n < 3:
            return (
                f"Madurez insuficiente ({actual}). Para satisfacer el indicador se requiere {meta}."
            )
    if tipo == "si_no":
        return f"No cumple ({actual}). Se requiere {meta}."
    if tipo in {"porcentaje", "umbral"}:
        return f"Por debajo del umbral ({actual}; meta {meta})."
    return f"No alcanza la meta ({actual}; meta {meta})."


def guia_indices(resultado: dict) -> list[dict[str, str]]:
    """Textos interpretativos de los índices principales para informes y UI."""
    total_ref = resultado.get("p_referencia_catalogo") or resultado.get("p_totales") or 0
    umbral = resultado.get("umbral_regional_objetivo", 60)
    ia_eval = resultado.get("ia", {}).get("evaluados", 0)
    return [
        {
            "nombre": "IMD global",
            "valor": f"{resultado['imd']} %",
            "rango": "0 – 100 %",
            "interpretacion": (
                f"Porcentaje de los {resultado['p_totales']} indicadores respondidos "
                f"que alcanzan el umbral de madurez (nivel ≥ 3, Sí, o % sobre umbral). "
                f"Referencia regional MetaRed: {umbral} %. "
                "Con pocos indicadores cargados el IMD es preliminar; completá la línea de base "
                f"({total_ref} indicadores) para un diagnóstico estable."
            ),
        },
        {
            "nombre": "Prácticas satisfechas",
            "valor": f"{resultado['p_satisfechas']} / {resultado['p_totales']}",
            "rango": f"0 – {resultado['p_totales']} (respondidos)",
            "interpretacion": (
                "Cantidad de indicadores que ya cumplen el umbral frente al total "
                "respondido en esta carga. No implica que la línea de base esté completa hasta "
                f"llegar a {total_ref} indicadores."
            ),
        },
        {
            "nombre": "Cobertura",
            "valor": f"{resultado['cobertura_pct']} %",
            "rango": f"0 – 100 % (sobre {total_ref} de la línea de base)",
            "interpretacion": (
                f"Qué parte de la línea de base ya tiene valor ({resultado['p_totales']} de "
                f"{total_ref} indicadores). Baja cobertura = diagnóstico parcial."
            ),
        },
        {
            "nombre": "Dimensión IA",
            "valor": f"{resultado['ia']['ratio_pct']} %",
            "rango": "0 – 100 %",
            "interpretacion": (
                f"IMD aplicado solo a indicadores de IA evaluados "
                f"({resultado['ia']['satisfechos']} satisfechos de {ia_eval}). "
                "0 % si ningún indicador IA cargado satisface el umbral, o si aún no "
                "respondiste indicadores del bloque B8 (Inteligencia Artificial)."
            ),
        },
    ]


def exportar_diagnostico(
    respuestas: dict[str, Any],
    meta: dict | None = None,
    *,
    codigos: set[str] | None = None,
) -> dict:
    resultado = calcular_imd(respuestas, codigos=codigos)
    return {
        "modelo": "MDeIA UCCuyo",
        "version": load_framework()["meta"]["version"],
        "institucion": load_framework()["meta"]["institucion"],
        "meta_encuesta": meta or {},
        "respuestas": respuestas,
        "resultado": resultado,
    }


LEGACY_CODIGOS: dict[str, str] = {
    f"CLJL_IA_{suffix}": f"MDEIA_IA_{suffix}"
    for suffix in (
        "ENCUESTA",
        "GUIA_ETICA",
        "ALFABETIZACION",
        "INTEGRIDAD",
        "EVAL_AUTENTICA",
        "DATAWAREHOUSE",
        "DESERCION",
        "OBSERVATORIO",
        "CIBERSEG",
        "LEARNING_ANALYTICS",
        "EMPRENDIMIENTO",
        "TRANSFERENCIA",
    )
}


def normalizar_respuestas(respuestas: dict[str, Any]) -> dict[str, Any]:
    """Mapea códigos CLJL_IA_* de exportaciones anteriores a MDEIA_IA_*."""
    out = dict(respuestas)
    for old, new in LEGACY_CODIGOS.items():
        if old in out and new not in out:
            out[new] = out.pop(old)
    return out
