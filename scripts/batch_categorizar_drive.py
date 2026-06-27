#!/usr/bin/env python3
"""
Lote: Google Drive (PDFs) → Categorizador UCCuyo (Playwright) → Excel consolidado.

Variables de entorno:
  GOOGLE_APPLICATION_CREDENTIALS  JSON de cuenta de servicio con acceso de lectura a Drive
  DRIVE_FOLDER_ID                 Carpeta en Drive (default: carpeta CVar UCCuyo)
  CATEGORIZADOR_URL               URL de la app Streamlit
  OUTPUT_XLSX                     Ruta del Excel de salida

La carpeta de Drive debe estar compartida con el client_email de la cuenta de servicio.

Uso:
  export GOOGLE_APPLICATION_CREDENTIALS=/ruta/a/credenciales.json
  python3 scripts/batch_categorizar_drive.py
"""

from __future__ import annotations

import io
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

DRIVE_FOLDER_ID = os.environ.get(
    "DRIVE_FOLDER_ID", "1T1GID13Wa5TXmTfibQ0HAMBtNmOvC-DH"
).strip()
CATEGORIZADOR_URL = os.environ.get(
    "CATEGORIZADOR_URL",
    "https://categorizador-investigadores-uccuyo-3lnyqyni7hsc4b4benzahm.streamlit.app/",
).strip()
OUTPUT_XLSX = os.environ.get(
    "OUTPUT_XLSX",
    str(
        Path(__file__).resolve().parent.parent
        / "output"
        / f"categorizacion_drive_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    ),
).strip()
PROCESS_TIMEOUT_MS = int(os.environ.get("PROCESS_TIMEOUT_MS", "300000"))
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def drive_service():
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if not creds_path or not Path(creds_path).is_file():
        raise SystemExit(
            "Falta GOOGLE_APPLICATION_CREDENTIALS apuntando a un JSON de cuenta de servicio."
        )
    creds = Credentials.from_service_account_file(creds_path, scopes=DRIVE_SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def list_pdfs_in_folder(service, folder_id: str) -> list[dict]:
    query = (
        f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
    )
    files: list[dict] = []
    page_token = None
    while True:
        response = (
            service.files()
            .list(
                q=query,
                fields="nextPageToken, files(id, name)",
                pageToken=page_token,
                orderBy="name",
            )
            .execute()
        )
        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return files


def download_pdf(service, file_id: str, dest_path: Path) -> None:
    request = service.files().get_media(fileId=file_id)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with io.FileIO(dest_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()


def wait_for_app(page) -> None:
    page.wait_for_function(
        "() => document.title.includes('Categorizador de Investigadores')",
        timeout=120_000,
    )
    frame = page.frame_locator('iframe[title="streamlitApp"]')
    frame.get_by_text("Cargar CVar (PDF, DOC o TXT normalizado)").wait_for(
        state="visible", timeout=120_000
    )


def upload_cvar(page, pdf_path: Path) -> None:
    frame = page.frame_locator('iframe[title="streamlitApp"]')
    region = frame.get_by_role(
        "region", name=re.compile(r"Cargar CVar \(PDF, DOC o TXT normalizado\)")
    )
    file_input = region.locator('input[type="file"]')
    if file_input.count() > 0:
        file_input.first.set_input_files(str(pdf_path))
        return
    with page.expect_file_chooser(timeout=30_000) as fc_info:
        region.get_by_test_id("stBaseButton-secondary").click()
    fc_info.value.set_files(str(pdf_path))


def extract_categorization(page) -> dict[str, str | None]:
    frame = page.frame_locator('iframe[title="streamlitApp"]')
    frame.get_by_text("Resultado de categorización").wait_for(
        state="visible", timeout=PROCESS_TIMEOUT_MS
    )
    frame.locator("body").wait_for_function(
        """() => {
            const ps = [...document.querySelectorAll('p')];
            const idx = ps.findIndex((p) => p.textContent?.trim() === 'Puntaje total');
            return idx >= 0 && Boolean(ps[idx + 1]?.textContent?.trim());
        }""",
        timeout=PROCESS_TIMEOUT_MS,
    )
    return frame.locator("body").evaluate(
        """() => {
            const read = (label) => {
                const ps = [...document.querySelectorAll('p')];
                const idx = ps.findIndex((p) => p.textContent?.trim() === label);
                return idx >= 0 ? ps[idx + 1]?.textContent?.trim() ?? null : null;
            };
            return {
                puntaje_total: read('Puntaje total'),
                categoria: read('Categoría'),
                puntaje_maximo_teorico: read('Puntaje máximo teórico'),
            };
        }"""
    )


def process_pdf_with_playwright(page, pdf_path: Path) -> dict[str, str | None]:
    page.goto(CATEGORIZADOR_URL, wait_until="domcontentloaded")
    wait_for_app(page)
    upload_cvar(page, pdf_path)
    return extract_categorization(page)


def main() -> int:
    service = drive_service()
    pdfs = list_pdfs_in_folder(service, DRIVE_FOLDER_ID)
    if not pdfs:
        print(f"No se encontraron PDFs en la carpeta {DRIVE_FOLDER_ID}.", file=sys.stderr)
        return 1

    print(f"PDFs encontrados: {len(pdfs)}", file=sys.stderr)
    rows: list[dict] = []

    with tempfile.TemporaryDirectory(prefix="cvar_batch_") as tmp_dir:
        tmp = Path(tmp_dir)
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=False)
            context = browser.new_context()
            page = context.new_page()

            for index, item in enumerate(pdfs, start=1):
                name = item["name"]
                file_id = item["id"]
                local_path = tmp / name
                print(f"[{index}/{len(pdfs)}] Descargando: {name}", file=sys.stderr)

                row = {
                    "Nombre PDF": name,
                    "Puntaje": None,
                    "Categoría": None,
                    "Puntaje máximo": None,
                    "Estado": "pendiente",
                    "Error": None,
                }

                try:
                    download_pdf(service, file_id, local_path)
                    print(f"[{index}/{len(pdfs)}] Procesando en Categorizador…", file=sys.stderr)
                    result = process_pdf_with_playwright(page, local_path)
                    row["Puntaje"] = result.get("puntaje_total")
                    row["Categoría"] = result.get("categoria")
                    row["Puntaje máximo"] = result.get("puntaje_maximo_teorico")
                    row["Estado"] = (
                        "ok"
                        if row["Puntaje"] and row["Categoría"] and row["Puntaje máximo"]
                        else "incompleto"
                    )
                    print(
                        f"  → {row['Puntaje']} | {row['Categoría']} | máx {row['Puntaje máximo']}",
                        file=sys.stderr,
                    )
                except PlaywrightTimeoutError as exc:
                    row["Estado"] = "timeout"
                    row["Error"] = str(exc)
                    print(f"  → timeout: {exc}", file=sys.stderr)
                except Exception as exc:  # noqa: BLE001
                    row["Estado"] = "error"
                    row["Error"] = str(exc)
                    print(f"  → error: {exc}", file=sys.stderr)

                rows.append(row)

            browser.close()

    df = pd.DataFrame(rows)
    out = Path(OUTPUT_XLSX)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(out, index=False, sheet_name="Categorización")

    ok = (df["Estado"] == "ok").sum()
    print(f"\nFinalizado: {ok}/{len(df)} OK. Excel: {out}", file=sys.stderr)
    print(df.to_json(orient="records", force_ascii=False, indent=2))
    return 0 if ok == len(df) else 2


if __name__ == "__main__":
    sys.exit(main())
