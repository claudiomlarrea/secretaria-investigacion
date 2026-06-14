"""Modelo del gemelo PEI: baseline 2025, simulación y alertas."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
BASELINE_PATH = ROOT / "data" / "pei_baseline_2025.json"


def load_baseline() -> dict:
    with open(BASELINE_PATH, encoding="utf-8") as f:
        return json.load(f)


def objetivos_df(data: dict | None = None) -> pd.DataFrame:
    data = data or load_baseline()
    return pd.DataFrame(data["objetivos"])


def unidades_df(data: dict | None = None) -> pd.DataFrame:
    data = data or load_baseline()
    return pd.DataFrame(data["unidades"])


def simular_distribucion(pesos: list[float], total: int = 805) -> pd.DataFrame:
    s = sum(pesos) or 1.0
    norm = [p / s for p in pesos]
    acts = [max(0, round(total * p)) for p in norm]
    diff = total - sum(acts)
    if diff:
        acts[0] += diff
    base = objetivos_df()
    out = base.copy()
    out["actividades_sim"] = acts
    out["pct_sim"] = (out["actividades_sim"] / total * 100).round(1)
    out["delta_pct"] = (out["pct_sim"] - out["pct"]).round(1)
    return out


def indice_equilibrio(pcts: list[float]) -> float:
    """1 = perfectamente equilibrado; 0 = máxima concentración."""
    n = len(pcts) or 1
    ideal = 100 / n
    desv = sum(abs(p - ideal) for p in pcts) / (2 * (100 - ideal) or 1)
    return round(max(0.0, 1.0 - desv), 2)


def etiqueta_transversalidad(valor: float) -> str:
    if valor < 1.2:
        return "baja"
    if valor < 1.5:
        return "moderada"
    return "alta"
