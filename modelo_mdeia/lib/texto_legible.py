# -*- coding: utf-8 -*-
"""Lenguaje claro para enunciados UDigital / MDeIA (siglas, abreviaturas)."""

from __future__ import annotations

import re

_TI = "tecnologías de la información (TI)"
_LAS_TI = "las tecnologías de la información (TI)"

# Orden: frases más largas primero; luego \bTI\b suelto.
_REGLAS_TI: list[tuple[str, str]] = [
    (r"\bde\s+las\s+TI\b", f"de {_LAS_TI}"),
    (r"\blas\s+TI\b", _LAS_TI),
    (r"\bgobierno\s+de\s+las\s+TI\b", f"gobierno de {_LAS_TI}"),
    (r"\bplanificación\s+estratégica\s+de\s+(?:las\s+)?TI\b", f"planificación estratégica de {_LAS_TI}"),
    (r"\bfinanciación\s+plurianual\s+de\s+TI\b", f"financiación plurianual de {_TI}"),
    (r"\bmodelo\s+de\s+gobierno\s+de\s+TI\b", f"modelo de gobierno de {_TI}"),
    (r"\bcomité\s+de\s+estrategia\s+y\s+gobierno\s+de\s+TI\b", f"comité de estrategia y gobierno de {_TI}"),
    (r"\bgobierno\s+TI\b", f"gobierno de {_TI}"),
    (r"\bÁrea\s+TI\b", f"área de {_TI}"),
    (r"\bárea\s+TI\b", f"área de {_TI}"),
    (r"\bservicios\s+TI\b", f"servicios de {_TI}"),
    (r"\bServicios\s+TI\b", f"Servicios de {_TI}"),
    (r"\bsoporte\s+TI\b", f"soporte de {_TI}"),
    (r"\bSoporte\s+TI\b", f"Soporte de {_TI}"),
    (r"\bayuda\s+TI\b", f"ayuda de {_TI}"),
    (r"\bproyectos\s+TI\b", f"proyectos de {_TI}"),
    (r"\binfraestructuras\s+TI\b", f"infraestructuras de {_TI}"),
    (r"\bequipamiento\s+TI\b", f"equipamiento de {_TI}"),
    (r"\btendencias\s+TI\b", f"tendencias en {_TI}"),
    (r"\bestándares\s+TI\b", f"estándares de {_TI}"),
    (r"\bpersonal\s+TI\b", f"personal de {_TI}"),
    (r"\bpresupuesto\s+para\s+TI\b", f"presupuesto para {_TI}"),
    (r"\bpresupuesto\s+TI\b", f"presupuesto de {_TI}"),
    (r"\bgestión\s+de\s+sus\s+TI\b", f"gestión de sus {_TI}"),
    (r"\bgestión\s+de\s+las\s+TI\b", f"gestión de {_LAS_TI}"),
    (r"\bGestión\s+de\s+las\s+TI\b", f"Gestión de {_LAS_TI}"),
    (r"\bentrevistas\s+con\s+TI\b", f"entrevistas con el área de {_TI}"),
    (r"\bTI\s*/\s*Sistemas\b", f"{_TI} / Sistemas"),
    (r"\bTI\s+y\b", f"{_TI} y"),
]


def legibilizar_siglas_udigital(texto: str) -> str:
    """Expande TI y otras siglas frecuentes en textos visibles para el usuario."""
    if not texto:
        return texto
    t = texto
    for patron, reemplazo in _REGLAS_TI:
        t = re.sub(patron, reemplazo, t, flags=re.IGNORECASE)
    # TI suelta que no quedó dentro de «(TI)»
    t = re.sub(r"(?<!\()\bTI\b(?!\))", _TI, t, flags=re.IGNORECASE)
    t = t.replace("equipo de gobierno (EG)", "equipo de gestión")
    t = re.sub(r"\bEG\b", "equipo de gestión", t)
    return t


def leyenda_siglas_markdown() -> str:
    return (
        "**Siglas usadas en el diagnóstico:** "
        "**TI** = tecnologías de la información (sistemas, software, redes, soporte y servicios digitales institucionales)."
    )
