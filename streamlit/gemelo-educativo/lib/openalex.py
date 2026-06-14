"""Consulta publicaciones UCCuyo en OpenAlex (misma institución que el sitio y Looker)."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import date

INSTITUTION_ID = "I4210121591"
MAILTO = "investigacion@uccuyo.edu.ar"
PER_PAGE = 100


def _fetch(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": f"mailto:{MAILTO} (gemelo-educativo-uccuyo)",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_works(year_from: int = 2020, max_pages: int = 5) -> list[dict]:
    filters = [
        f"authorships.institutions.lineage:{INSTITUTION_ID}",
        f"from_publication_date:{year_from}-01-01",
        f"to_publication_date:{date.today().year}-12-31",
    ]
    params = {
        "filter": ",".join(filters),
        "sort": "publication_date:desc",
        "per-page": str(PER_PAGE),
        "mailto": MAILTO,
    }
    rows: list[dict] = []
    for page in range(1, max_pages + 1):
        params["page"] = str(page)
        url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
        data = _fetch(url)
        for w in data.get("results", []):
            rows.append(
                {
                    "anio": w.get("publication_year"),
                    "titulo": (w.get("display_name") or "").strip(),
                    "autores": ", ".join(
                        a.get("author", {}).get("display_name", "")
                        for a in w.get("authorships", [])
                        if a.get("author", {}).get("display_name")
                    ),
                    "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
                    "tipo": (w.get("type") or "").replace("_", " "),
                    "oa": bool(w.get("open_access", {}).get("is_oa")),
                }
            )
        if not data.get("results") or len(data["results"]) < PER_PAGE:
            break
        time.sleep(0.35)
    return rows


def resumen_por_anio(rows: list[dict]) -> dict[int, int]:
    out: dict[int, int] = {}
    for r in rows:
        y = r.get("anio")
        if y:
            out[y] = out.get(y, 0) + 1
    return dict(sorted(out.items()))
