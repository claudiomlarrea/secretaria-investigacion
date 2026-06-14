"""Modelo del Gemelo Digital Plan Institucional."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
BASELINE_PATH = ROOT / "data" / "pei_baseline_2025.json"
ANIOS_DISPONIBLES = [2023, 2024, 2025]


def load_baseline(anio: int = 2025) -> dict:
    with open(BASELINE_PATH, encoding="utf-8") as f:
        data = json.load(f)
    if anio != data.get("anio", 2025):
        serie = {r["anio"]: r["total"] for r in data.get("actividades_por_anio", [])}
        total = serie.get(anio, data["total_actividades"])
        factor = total / data["total_actividades"] if data["total_actividades"] else 1
        data = {**data, "anio": anio, "total_actividades": total}
        data["objetivos"] = [
            {**o, "actividades": max(1, round(o["actividades"] * factor)), "pct": round(o["pct"], 1)}
            for o in data["objetivos"]
        ]
    return data


def objetivos_df(data: dict | None = None) -> pd.DataFrame:
    return pd.DataFrame((data or load_baseline())["objetivos"])


def unidades_df(data: dict | None = None) -> pd.DataFrame:
    return pd.DataFrame((data or load_baseline())["unidades"])


def sedes_df(data: dict | None = None) -> pd.DataFrame:
    data = data or load_baseline()
    return (
        unidades_df(data)
        .groupby("sede", as_index=False)["actividades"]
        .sum()
        .sort_values("actividades", ascending=False)
    )


def funciones_df(data: dict | None = None) -> pd.DataFrame:
    return pd.DataFrame((data or load_baseline())["funciones_sustantivas"])


def actividades_por_anio_df() -> pd.DataFrame:
    data = load_baseline()
    return pd.DataFrame(data["actividades_por_anio"])


def funcion_metricas(funcion: str, data: dict | None = None) -> dict:
    data = data or load_baseline()
    row = next(f for f in data["funciones_sustantivas"] if f["funcion"] == funcion)
    sedes = data["sedes"]
    if funcion == "Docencia":
        alumnos = sum(row["alumnos"].values())
        docentes = sum(row["docentes"].values())
        return {
            "actividades_plan": row["actividades_plan"],
            "alumnos": alumnos,
            "docentes": docentes,
            "ratio_alumnos_docente": round(alumnos / docentes, 1) if docentes else 0,
            "por_sede": pd.DataFrame(
                {
                    "sede": sedes,
                    "alumnos": [row["alumnos"][s] for s in sedes],
                    "docentes": [row["docentes"][s] for s in sedes],
                }
            ),
        }
    if funcion == "Investigación":
        inv = sum(row["investigadores"].values())
        acts = sum(row["actividades"].values())
        return {
            "actividades_plan": row["actividades_plan"],
            "investigadores": inv,
            "actividades": acts,
            "actividades_por_investigador": round(acts / inv, 2) if inv else 0,
            "por_sede": pd.DataFrame(
                {
                    "sede": sedes,
                    "investigadores": [row["investigadores"][s] for s in sedes],
                    "actividades": [row["actividades"][s] for s in sedes],
                }
            ),
        }
    acts = sum(row["actividades"].values())
    return {
        "actividades_plan": row["actividades_plan"],
        "convenios": row["convenios_firmados"],
        "extension": row["actividades_extension"],
        "voluntariado": row["voluntariado_y_comunidad"],
        "actividades": acts,
        "por_sede": pd.DataFrame(
            {"sede": sedes, "actividades": [row["actividades"][s] for s in sedes]}
        ),
    }


def simular_distribucion(pesos: list[float], total: int = 805) -> pd.DataFrame:
    s = sum(pesos) or 1.0
    norm = [p / s for p in pesos]
    acts = [max(0, round(total * p)) for p in norm]
    diff = total - sum(acts)
    if diff:
        acts[0] += diff
    out = objetivos_df().copy()
    out["actividades_sim"] = acts
    out["pct_sim"] = (out["actividades_sim"] / total * 100).round(1)
    out["delta_pct"] = (out["pct_sim"] - out["pct"]).round(1)
    return out


def indice_equilibrio(pcts: list[float]) -> float:
    n = len(pcts) or 1
    ideal = 100 / n
    desv = sum(abs(p - ideal) for p in pcts) / (2 * (100 - ideal) or 1)
    return round(max(0.0, 1.0 - desv), 2)
