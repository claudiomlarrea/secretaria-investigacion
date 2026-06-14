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


def simular_distribucion(
    pesos: list[float], total: int = 805, data: dict | None = None
) -> pd.DataFrame:
    data = data or load_baseline()
    s = sum(pesos) or 1.0
    norm = [p / s for p in pesos]
    acts = [max(0, round(total * p)) for p in norm]
    diff = total - sum(acts)
    if diff:
        acts[0] += diff
    out = objetivos_df(data).copy()
    out["actividades_sim"] = acts
    out["pct_sim"] = (out["actividades_sim"] / total * 100).round(1)
    out["delta_actividades"] = out["actividades_sim"] - out["actividades"]
    out["delta_pct"] = (out["pct_sim"] - out["pct"]).round(1)
    return out


def _matriz_objetivo_funcion(data: dict) -> dict[str, dict[str, float]]:
    return data.get("matriz_objetivo_funcion", {})


def contribucion_objetivo_funcion(sim: pd.DataFrame, data: dict | None = None) -> pd.DataFrame:
    """Cuánto aporta cada cambio de objetivo al delta de cada función sustantiva."""
    data = data or load_baseline()
    matriz = _matriz_objetivo_funcion(data)
    rows: list[dict] = []
    for _, row in sim.iterrows():
        og_id = str(int(row["id"]))
        delta = int(row["delta_actividades"])
        for funcion, peso in matriz.get(og_id, {}).items():
            rows.append(
                {
                    "objetivo": f"OG{og_id}",
                    "funcion": funcion,
                    "contribucion": round(delta * peso),
                }
            )
    return pd.DataFrame(rows)


def simular_impacto_funciones(sim: pd.DataFrame, data: dict | None = None) -> pd.DataFrame:
    """Proyecta actividades por función según cambios en la distribución por objetivo."""
    data = data or load_baseline()
    matriz = _matriz_objetivo_funcion(data)
    funciones_base = {
        f["funcion"]: f["actividades_plan"] for f in data["funciones_sustantivas"]
    }
    impacto = {fn: 0.0 for fn in funciones_base}
    for _, row in sim.iterrows():
        og_id = str(int(row["id"]))
        delta = int(row["delta_actividades"])
        for funcion, peso in matriz.get(og_id, {}).items():
            impacto[funcion] += delta * peso

    rows: list[dict] = []
    for funcion, base in funciones_base.items():
        delta_float = impacto[funcion]
        factor = max(0.0, (base + delta_float) / base) if base else 1.0
        sim_act = max(0, round(base * factor))
        rows.append(
            {
                "funcion": funcion,
                "actividades_base": base,
                "actividades_sim": sim_act,
                "delta": sim_act - base,
                "delta_pct": round((sim_act - base) / base * 100, 1) if base else 0.0,
                "factor": factor,
            }
        )
    return pd.DataFrame(rows)


def metricas_operativas_por_funcion(
    impacto_funciones: pd.DataFrame, data: dict | None = None
) -> dict[str, list[dict]]:
    """Indicadores base vs proyectados por función, listos para mostrar en la UI."""
    data = data or load_baseline()
    factor_map = {r["funcion"]: r["factor"] for _, r in impacto_funciones.iterrows()}
    out: dict[str, list[dict]] = {}

    for funcion in ("Docencia", "Investigación", "Extensión"):
        factor = factor_map.get(funcion, 1.0)
        base = funcion_metricas(funcion, data)
        filas: list[dict] = []

        if funcion == "Docencia":
            pares = [
                ("Alumnos", base["alumnos"], int(base["alumnos"] * factor)),
                ("Docentes", base["docentes"], max(1, round(base["docentes"] * factor))),
            ]
            ratio_base = round(base["alumnos"] / base["docentes"], 1) if base["docentes"] else 0
            ratio_proj = round(pares[0][2] / pares[1][2], 1) if pares[1][2] else 0
            pares.append(("Alumnos / docente", ratio_base, ratio_proj))
        elif funcion == "Investigación":
            inv_base = base["investigadores"]
            acts_base = base["actividades"]
            inv_proj = max(1, round(inv_base * factor))
            acts_proj = max(0, round(acts_base * factor))
            pares = [
                ("Investigadores", inv_base, inv_proj),
                ("Actividades científicas", acts_base, acts_proj),
                (
                    "Actividades / investigador",
                    round(acts_base / inv_base, 2) if inv_base else 0,
                    round(acts_proj / inv_proj, 2) if inv_proj else 0,
                ),
            ]
        else:
            pares = [
                ("Convenios firmados", base["convenios"], max(0, round(base["convenios"] * factor))),
                ("Actividades de extensión", base["extension"], max(0, round(base["extension"] * factor))),
                (
                    "Voluntariado y comunidad",
                    base["voluntariado"],
                    max(0, round(base["voluntariado"] * factor)),
                ),
                (
                    "Actividades en el plan",
                    base["actividades_plan"],
                    max(0, round(base["actividades_plan"] * factor)),
                ),
            ]

        for indicador, valor_base, valor_proj in pares:
            diff = valor_proj - valor_base
            if isinstance(valor_base, int):
                delta: int | float = int(valor_proj) - valor_base
            else:
                delta = round(diff, 2)
            filas.append(
                {
                    "indicador": indicador,
                    "base": valor_base,
                    "proyectado": valor_proj,
                    "delta": delta,
                }
            )
        out[funcion] = filas
    return out


def indice_equilibrio(pcts: list[float]) -> float:
    n = len(pcts) or 1
    ideal = 100 / n
    desv = sum(abs(p - ideal) for p in pcts) / (2 * (100 - ideal) or 1)
    return round(max(0.0, 1.0 - desv), 2)
