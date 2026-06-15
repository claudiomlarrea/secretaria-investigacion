# -*- coding: utf-8 -*-
"""Carga y agregación de la planilla PEI en Google Sheets."""

from __future__ import annotations

import json
import time
from io import StringIO
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
METADATA_PATH = ROOT / "data" / "pei_baseline_2025.json"

PEI_SHEET_ID = "1c-ZPobdyqA5pW9mhyJsC1uJwFFAcEv4HliOjcSwhOsg"
PEI_SHEET_GID = "511573903"
PEI_SHEET_URL = (
    f"https://docs.google.com/spreadsheets/d/{PEI_SHEET_ID}/export"
    f"?format=csv&gid={PEI_SHEET_GID}"
)

OG_NOMBRES = {
    1: "Sistema integral de aseguramiento de la calidad",
    2: "Integralidad, vinculación y comunicación",
    3: "Educación a distancia",
    4: "Jerarquización de recursos humanos",
    5: "Participación estudiantil y de egresados",
    6: "Identidad institucional y compromiso social",
}

SEDES = ["Sede San Juan", "Sede San Luis", "Sede Mendoza"]

_CACHE: dict[str, object] = {"df": None, "fetched_at": 0.0}
_CACHE_TTL_SEC = 600


def _columna_unidad(df: pd.DataFrame) -> str:
    for col in df.columns:
        if "unidad" in col.lower() and "acad" in col.lower():
            return col
    raise KeyError("No se encontró la columna de unidad académica en la planilla.")


def _columnas_actividades(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.strip().startswith("Actividades Objetivo")]


def _celda_con_actividad(val) -> bool:  # noqa: ANN001
    if pd.isna(val):
        return False
    return bool(str(val).strip())


def unidad_a_sede(unidad: str) -> str:
    u = (unidad or "").strip().lower()
    if not u:
        return "Sede San Juan"
    if "mendoza" in u or "observatorio" in u or "vinculación tecnológica" in u:
        return "Sede Mendoza"
    if u == "facultad don bosco":
        return "Sede Mendoza"
    if "san luis" in u or "veterinarias" in u:
        return "Sede San Luis"
    if "don bosco" in u:
        return "Sede San Luis"
    return "Sede San Juan"


def fetch_planilla_pei(*, force: bool = False) -> pd.DataFrame:
    """Descarga la planilla pública de respuestas del PEI."""
    now = time.time()
    if (
        not force
        and _CACHE["df"] is not None
        and now - float(_CACHE["fetched_at"]) < _CACHE_TTL_SEC
    ):
        return _CACHE["df"].copy()  # type: ignore[union-attr]

    try:
        with urlopen(PEI_SHEET_URL, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except URLError as exc:
        raise ConnectionError(f"No se pudo leer la planilla Google Sheets: {exc}") from exc

    df = pd.read_csv(StringIO(raw), low_memory=False)
    if "AÑO" not in df.columns:
        raise ValueError("La planilla no contiene la columna AÑO.")

    df["AÑO"] = pd.to_numeric(df["AÑO"], errors="coerce")
    df = df[df["AÑO"].notna()].copy()
    df["AÑO"] = df["AÑO"].astype(int)
    ucol = _columna_unidad(df)
    df["_sede"] = df[ucol].astype(str).map(unidad_a_sede)

    _CACHE["df"] = df
    _CACHE["fetched_at"] = now
    return df.copy()


def _metadata_estatico() -> dict:
    with open(METADATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _texto_actividad(val) -> str:  # noqa: ANN001
    """Texto de actividad normalizado (espacios); respeta mayúsculas como Looker Studio."""
    return " ".join(str(val).strip().split())


def _conteo_por_og(df_anio: pd.DataFrame, cols_act: list[str]) -> list[int]:
    """Actividades únicas por OG (COUNT DISTINCT del nombre), alineado a Looker Studio."""
    conteos: list[int] = []
    for col in cols_act:
        mask = df_anio[col].map(_celda_con_actividad)
        textos = df_anio.loc[mask, col].map(_texto_actividad)
        conteos.append(int(textos.nunique()))
    return conteos


def _conteo_por_unidad(df_anio: pd.DataFrame, ucol: str) -> dict[str, int]:
    """Formularios cargados por unidad (1 fila = 1 registro), alineado a Looker Studio."""
    conteo: dict[str, int] = {}
    for unidad, n in df_anio[ucol].astype(str).str.strip().value_counts().items():
        if unidad:
            conteo[unidad] = int(n)
    return conteo


def _actividades_por_funcion(objetivos: list[dict], matriz: dict) -> dict[str, int]:
    totales = {f: 0.0 for f in ("Docencia", "Investigación", "Extensión")}
    for og in objetivos:
        pesos = matriz.get(str(og["id"]), {})
        for funcion, peso in pesos.items():
            totales[funcion] += og["actividades"] * peso
    return {k: max(0, round(v)) for k, v in totales.items()}


def _distribuir_por_sede(
    df_anio: pd.DataFrame,
    cols_act: list[str],
    matriz: dict,
    funcion: str,
) -> dict[str, int]:
    acum = {s: 0.0 for s in SEDES}
    for _, row in df_anio.iterrows():
        sede = row["_sede"]
        for og_idx, col in enumerate(cols_act, start=1):
            if not _celda_con_actividad(row[col]):
                continue
            peso = matriz.get(str(og_idx), {}).get(funcion, 0.0)
            if peso:
                acum[sede] += peso
    return {s: max(0, round(acum[s])) for s in SEDES}


def _convenios_desde_planilla(df_anio: pd.DataFrame, cols_act: list[str]) -> int:
    col = cols_act[1]  # OG2
    mask = df_anio[col].map(_celda_con_actividad) & df_anio[col].astype(str).str.contains(
        "convenio", case=False, na=False
    )
    return int(df_anio.loc[mask, col].map(_texto_actividad).nunique())


def _extension_y_voluntariado(
    df_anio: pd.DataFrame, cols_act: list[str], actividades_ext: int
) -> tuple[int, int]:
    col2, col6 = cols_act[1], cols_act[5]
    conv_mask = df_anio[col2].map(_celda_con_actividad) & df_anio[col2].astype(str).str.contains(
        "convenio", case=False, na=False
    )
    vol_mask = df_anio[col6].map(_celda_con_actividad) & df_anio[col6].astype(str).str.contains(
        r"voluntariado|comunidad|pastoral", case=False, na=False
    )
    convenios = int(df_anio.loc[conv_mask, col2].map(_texto_actividad).nunique())
    voluntariado = int(df_anio.loc[vol_mask, col6].map(_texto_actividad).nunique())
    extension = max(0, actividades_ext - convenios - voluntariado)
    return extension, voluntariado


def build_baseline_from_sheets(anio: int) -> dict:
    """Arma el baseline del gemelo a partir de la planilla Google Sheets."""
    df = fetch_planilla_pei()
    meta = _metadata_estatico()
    matriz = meta["matriz_objetivo_funcion"]
    cols_act = _columnas_actividades(df)
    if len(cols_act) != 6:
        raise ValueError(f"Se esperaban 6 columnas de actividades, hay {len(cols_act)}.")

    anios = sorted(int(a) for a in df["AÑO"].unique())
    if anio not in anios:
        raise ValueError(f"Año {anio} no disponible en la planilla ({anios}).")

    ucol = _columna_unidad(df)
    df_anio = df[df["AÑO"] == anio].copy()
    conteos = _conteo_por_og(df_anio, cols_act)
    total_formularios = len(df_anio)
    suma_unicas_og = sum(conteos)
    total_pct = suma_unicas_og or 1

    objetivos = [
        {
            "id": og_id,
            "nombre": OG_NOMBRES[og_id],
            "actividades": conteos[og_id - 1],
            "pct": round(conteos[og_id - 1] / total_pct * 100, 1),
        }
        for og_id in range(1, 7)
    ]

    actividades_por_anio = []
    for a in anios:
        if a > 2026:
            continue
        sub = df[df["AÑO"] == a]
        actividades_por_anio.append({"anio": a, "total": len(sub)})

    unidad_act = _conteo_por_unidad(df_anio, ucol)

    unidades = [
        {"unidad": nombre, "sede": unidad_a_sede(nombre), "actividades": cant}
        for nombre, cant in sorted(unidad_act.items(), key=lambda x: (-x[1], x[0]))
    ]

    act_func = _actividades_por_funcion(objetivos, matriz)
    meta_func = {f["funcion"]: f for f in meta["funciones_sustantivas"]}
    factor_anio = act_func["Docencia"] / meta_func["Docencia"]["actividades_plan"] if act_func["Docencia"] else 1

    funciones_sustantivas: list[dict] = []
    for nombre in ("Docencia", "Investigación", "Extensión"):
        base_fn = meta_func[nombre]
        plan = act_func[nombre]
        item: dict = {
            "funcion": nombre,
            "descripcion": base_fn["descripcion"],
            "actividades_plan": plan,
        }
        if nombre == "Docencia":
            item["alumnos"] = {s: max(0, round(base_fn["alumnos"][s] * factor_anio)) for s in SEDES}
            item["docentes"] = {s: max(0, round(base_fn["docentes"][s] * factor_anio)) for s in SEDES}
        elif nombre == "Investigación":
            dist = _distribuir_por_sede(df_anio, cols_act, matriz, "Investigación")
            if sum(dist.values()):
                escala = plan / sum(dist.values())
                dist = {s: max(0, round(v * escala)) for s, v in dist.items()}
            else:
                dist = {s: max(0, round(base_fn["actividades"][s] * factor_anio)) for s in SEDES}
            item["investigadores"] = {
                s: max(0, round(base_fn["investigadores"][s] * factor_anio)) for s in SEDES
            }
            item["actividades"] = dist
        else:
            dist = _distribuir_por_sede(df_anio, cols_act, matriz, "Extensión")
            if sum(dist.values()):
                escala = plan / sum(dist.values())
                dist = {s: max(0, round(v * escala)) for s, v in dist.items()}
            extension, voluntariado = _extension_y_voluntariado(df_anio, cols_act, plan)
            item["convenios_firmados"] = _convenios_desde_planilla(df_anio, cols_act)
            item["actividades_extension"] = extension
            item["voluntariado_y_comunidad"] = voluntariado
            item["actividades"] = dist if sum(dist.values()) else {
                s: max(0, round(base_fn["actividades"][s] * factor_anio)) for s in SEDES
            }
        funciones_sustantivas.append(item)

    return {
        "anio": anio,
        "fuente": (
            "Planilla Google Sheets PEI · total de formularios como Looker Studio; "
            "columnas OG con actividades únicas por objetivo"
        ),
        "fuente_url": f"https://docs.google.com/spreadsheets/d/{PEI_SHEET_ID}/edit#gid={PEI_SHEET_GID}",
        "total_actividades": total_formularios,
        "suma_actividades_unicas_og": suma_unicas_og,
        "sedes": SEDES,
        "objetivos": objetivos,
        "funciones_sustantivas": funciones_sustantivas,
        "matriz_objetivo_funcion": matriz,
        "actividades_por_anio": actividades_por_anio,
        "unidades": unidades,
        "alertas": meta.get("alertas", []),
    }


def anios_disponibles_planilla() -> list[int]:
    df = fetch_planilla_pei()
    return sorted(int(a) for a in df["AÑO"].unique() if int(a) <= 2026)
