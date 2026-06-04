#!/usr/bin/env python3
"""
Sincroniza publicaciones UCCuyo desde OpenAlex → CSV para Google Sheets / Looker.

Uso:
  python3 scripts/sync_looker_openalex.py --year 2024
  python3 scripts/sync_looker_openalex.py --years 2020-2026
  python3 scripts/sync_looker_openalex.py --all   # desde 1990 (más lento)

Importar en Sheets: Archivo → Importar → Subir → looker_openalex.csv
  → "Insertar filas" o reemplazar según prefieras.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date

INSTITUTION_ID = "I4210121591"
MAILTO = "investigacion@uccuyo.edu.ar"
MIN_YEAR = 1990
PER_PAGE = 100
SLEEP_SEC = 0.35
OUT_DEFAULT = "looker_openalex.csv"
HEADERS = ["anio", "titulo", "autores", "doi", "url", "fuente", "fecha_sync"]


def fetch_page(filters: str, page: int) -> dict:
    params = {
        "filter": filters,
        "sort": "publication_date:desc",
        "per-page": str(PER_PAGE),
        "page": str(page),
        "mailto": MAILTO,
    }
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": f"mailto:{MAILTO} (sync-looker-local)",
        },
    )
    for attempt in range(1, 8):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 7:
                wait = 2 ** attempt
                print(f"  429 — esperando {wait}s (intento {attempt})…", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("Sin respuesta tras reintentos")


def normalize_doi(raw: str) -> str:
    s = (raw or "").strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if s.lower().startswith(prefix):
            s = s[len(prefix) :].strip()
    return s


def work_to_row(w: dict, synced_at: str) -> list | None:
    year = w.get("publication_year")
    if not year or year < MIN_YEAR or year > date.today().year:
        return None
    title = (w.get("display_name") or "").strip()
    if not title:
        return None
    authors = ", ".join(
        a.get("author", {}).get("display_name", "")
        for a in w.get("authorships") or []
        if a.get("author", {}).get("display_name")
    )
    doi = normalize_doi(w.get("doi") or "")
    loc = w.get("primary_location") or {}
    link = f"https://doi.org/{doi}" if doi else (loc.get("landing_page_url") or loc.get("pdf_url") or w.get("id") or "")
    return [year, title, authors, doi, link, "OpenAlex", synced_at]


def dedupe_key(row: list) -> str:
    doi = (row[3] or "").lower()
    if doi:
        return f"doi:{doi}"
    return f"t:{row[1].lower()}|y:{row[0]}"


def fetch_year(year: int, synced_at: str) -> list[list]:
    filters = f"authorships.institutions.lineage:{INSTITUTION_ID},publication_year:{year}"
    rows: list[list] = []
    page = 1
    while True:
        print(f"  Año {year}, página {page}…", file=sys.stderr)
        data = fetch_page(filters, page)
        results = data.get("results") or []
        if not results:
            break
        for w in results:
            row = work_to_row(w, synced_at)
            if row:
                rows.append(row)
        if len(results) < PER_PAGE:
            break
        page += 1
        time.sleep(SLEEP_SEC)
    return rows


def fetch_all_years(year_from: int, year_to: int, synced_at: str) -> list[list]:
    seen: dict[str, list] = {}
    for year in range(year_to, year_from - 1, -1):
        print(f"Año {year}…", file=sys.stderr)
        for row in fetch_year(year, synced_at):
            seen.setdefault(dedupe_key(row), row)
        time.sleep(1.0)
    return list(seen.values())


def main() -> int:
    parser = argparse.ArgumentParser(description="Exportar publicaciones UCCuyo (OpenAlex) a CSV")
    parser.add_argument("--year", type=int, help="Un solo año, ej. 2024")
    parser.add_argument("--years", metavar="DESDE-HASTA", help="Rango, ej. 2020-2026")
    parser.add_argument("--all", action="store_true", help=f"Todos los años {MIN_YEAR}–hoy")
    parser.add_argument("-o", "--output", default=OUT_DEFAULT, help="Archivo CSV de salida")
    args = parser.parse_args()

    synced_at = date.today().isoformat() + " " + time.strftime("%H:%M:%S")
    y_max = date.today().year

    if args.year:
        rows = fetch_year(args.year, synced_at)
    elif args.years:
        a, b = args.years.split("-", 1)
        rows = fetch_all_years(int(a), int(b), synced_at)
    elif args.all:
        rows = fetch_all_years(MIN_YEAR, y_max, synced_at)
    else:
        parser.print_help()
        print("\nEjemplo rápido: python3 scripts/sync_looker_openalex.py --year 2024", file=sys.stderr)
        return 1

    seen: dict[str, list] = {}
    for row in rows:
        seen.setdefault(dedupe_key(row), row)
    final = sorted(seen.values(), key=lambda r: (-int(r[0] or 0), r[1]))

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(HEADERS)
        w.writerows(final)

    print(f"Listo: {len(final)} filas → {args.output}")
    print("En Google Sheets: Archivo → Importar → Subir → elegir CSV → Insertar filas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
