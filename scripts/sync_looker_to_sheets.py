#!/usr/bin/env python3
"""
Sincronización automática OpenAlex → Google Sheets (pestaña indice_openalex).

Variables de entorno:
  LOOKER_SHEET_ID          ID de la planilla (obligatorio para subir)
  LOOKER_SHEET_TAB         Nombre de pestaña (default: indice_openalex)
  LOOKER_YEAR_FROM         Año inicial (default: 2020)
  LOOKER_YEAR_TO           Año final (default: año actual)
  GOOGLE_APPLICATION_CREDENTIALS  Ruta al JSON de cuenta de servicio

Uso local:
  export GOOGLE_APPLICATION_CREDENTIALS=~/credenciales-looker.json
  export LOOKER_SHEET_ID=10SKDfZJIZGSTOaOWgGmB46WPM0Bd0BvLe4aZ9jilA34
  python3 scripts/sync_looker_to_sheets.py
"""

from __future__ import annotations

import os
import sys
import time
from datetime import date
from pathlib import Path

# Reutiliza lógica OpenAlex del script CSV
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_looker_openalex import (  # noqa: E402
    HEADERS,
    fetch_all_years,
)

SHEET_ID = os.environ.get("LOOKER_SHEET_ID", "10SKDfZJIZGSTOaOWgGmB46WPM0Bd0BvLe4aZ9jilA34").strip()
SHEET_TAB = os.environ.get("LOOKER_SHEET_TAB", "indice_openalex").strip()
YEAR_FROM = int(os.environ.get("LOOKER_YEAR_FROM", "2020"))
YEAR_TO = int(os.environ.get("LOOKER_YEAR_TO", str(date.today().year)))


def existing_dois_from_sheet(ws) -> set[str]:
    try:
        col = ws.col_values(4)
    except Exception:
        return set()
    out = set()
    for raw in col[1:]:
        d = (raw or "").strip().lower()
        if d.startswith("10."):
            out.add(d)
    return out


def push_to_sheets(rows: list[list], incremental: bool = True) -> None:
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if not creds_path or not Path(creds_path).is_file():
        raise SystemExit(
            "Falta GOOGLE_APPLICATION_CREDENTIALS (ruta al JSON de cuenta de servicio de Google)."
        )
    if not SHEET_ID:
        raise SystemExit("Falta LOOKER_SHEET_ID.")

    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError as e:
        raise SystemExit("Instalá dependencias: pip install gspread google-auth") from e

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
    ]
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    try:
        ws = sh.worksheet(SHEET_TAB)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=SHEET_TAB, rows=max(len(rows) + 1, 100), cols=len(HEADERS))

    new_rows = [[str(c) if c is not None else "" for c in row] for row in rows]

    if incremental:
        if (ws.acell("A1").value or "").strip() != HEADERS[0]:
            ws.update([HEADERS], "A1", value_input_option="USER_ENTERED")
        existing = existing_dois_from_sheet(ws)
        to_add = []
        for row in new_rows:
            doi = (row[3] or "").strip().lower()
            if doi and doi in existing:
                continue
            to_add.append(row)
        if to_add:
            ws.append_rows(to_add, value_input_option="USER_ENTERED")
        print(f"Planilla: +{len(to_add)} filas nuevas (OpenAlex), total consultado: {len(new_rows)}.")
        return

    data = [HEADERS] + new_rows
    ws.clear()
    ws.update(data, value_input_option="USER_ENTERED")
    print(f"Planilla reemplazada: {len(rows)} filas en «{SHEET_TAB}».")


def main() -> int:
    synced_at = date.today().isoformat() + " " + time.strftime("%H:%M:%S")
    print(f"Descargando OpenAlex UCCuyo ({YEAR_FROM}–{YEAR_TO})…", file=sys.stderr)
    rows = fetch_all_years(YEAR_FROM, YEAR_TO, synced_at)
    rows.sort(key=lambda r: (-int(r[0] or 0), str(r[1])))
    print(f"Total único: {len(rows)} publicaciones.", file=sys.stderr)
    push_to_sheets(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
