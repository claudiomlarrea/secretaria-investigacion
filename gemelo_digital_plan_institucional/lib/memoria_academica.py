# -*- coding: utf-8 -*-
"""Datos de matrícula y plantel docente desde la Memoria Académica."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEMORIA_POR_ANIO: dict[int, Path] = {
    2023: ROOT / "data" / "memoria_academica_2023.json",
    2024: ROOT / "data" / "memoria_academica_2024.json",
    2025: ROOT / "data" / "memoria_academica_2025.json",
}
MEMORIA_BASE_ANIO = 2025

SEDES = ["Sede San Juan", "Sede San Luis", "Sede Mendoza"]


def load_memoria(anio: int) -> dict | None:
    path = MEMORIA_POR_ANIO.get(anio)
    if path and path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def load_memoria_2025() -> dict:
    memoria = load_memoria(MEMORIA_BASE_ANIO)
    if not memoria:
        raise FileNotFoundError("memoria_academica_2025.json no encontrado")
    return memoria


def _factor_historico(anio: int) -> float:
    """Para años sin memoria publicada, escala con la serie histórica de actividades PEI."""
    if load_memoria(anio):
        return 1.0
    memoria = load_memoria_2025()
    base = int(memoria["anio"])
    if anio == base:
        return 1.0
    baseline_path = ROOT / "data" / "pei_baseline_2025.json"
    with open(baseline_path, encoding="utf-8") as f:
        meta = json.load(f)
    serie = {int(r["anio"]): int(r["total"]) for r in meta.get("actividades_por_anio", [])}
    total_base = serie.get(base) or 1
    total_anio = serie.get(anio)
    if not total_anio:
        return 1.0
    return total_anio / total_base


def docencia_desde_memoria(anio: int) -> dict:
    """Alumnos (nivel universitario) y docentes por sede según memorias académicas disponibles."""
    memoria = load_memoria(anio)
    if memoria:
        return {
            "alumnos": dict(memoria["alumnos"]["por_sede"]),
            "docentes": dict(memoria["docentes"]["por_sede"]),
            "fuente_memoria": memoria["fuente"],
            "factor_estimacion": memoria.get("factor_estimacion", 1.0),
            "notas": memoria.get("notas", []),
        }

    memoria_base = load_memoria_2025()
    factor = _factor_historico(anio)
    alumnos = {
        s: max(0, round(memoria_base["alumnos"]["por_sede"][s] * factor))
        for s in SEDES
    }
    docentes = {
        s: max(0, round(memoria_base["docentes"]["por_sede"][s] * factor))
        for s in SEDES
    }
    return {
        "alumnos": alumnos,
        "docentes": docentes,
        "fuente_memoria": (
            f"{memoria_base['fuente']} · estimación proporcional para {anio} "
            f"(factor PEI {factor:.4f})"
        ),
        "factor_estimacion": round(factor, 4) if factor != 1.0 else 1.0,
        "notas": [],
    }
