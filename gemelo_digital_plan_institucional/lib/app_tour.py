# -*- coding: utf-8 -*-
"""Tour guiado del Gemelo Digital Plan Institucional."""

from __future__ import annotations

import streamlit as st

from constants import PEI_SHEET_URL
from ui_theme import GREEN, GREEN_LIGHT, TEXT_MUTED

TOUR_STEPS: list[dict[str, str]] = [
    {
        "titulo": "Bienvenida",
        "icono": "🎓",
        "cuerpo": (
            "El **Gemelo Digital Plan Institucional** integra las actividades del PEI "
            "(planilla Google Sheets), la matrícula y el plantel docente (memorias institucionales) "
            "y un módulo de **simulación** para conversar escenarios con autoridades.\n\n"
            "Está pensado para rectorado, decanatos y secretarías: no reemplaza Looker ni la memoria, "
            "sino que las **lee y cruza** en una sola vista."
        ),
    },
    {
        "titulo": "Dos pantallas",
        "icono": "📋",
        "cuerpo": (
            "En el **menú lateral izquierdo** (arriba del selector de año) elegís entre:\n\n"
            "1. **Análisis de actividades del plan** — qué pasó cada año: objetivos, sedes, "
            "funciones sustantivas y serie histórica.\n"
            "2. **Gemelo digital** — estado actual + simulación «qué pasaría si…» al mover "
            "los objetivos generales del PEI."
        ),
    },
    {
        "titulo": "Año y planilla en vivo",
        "icono": "📅",
        "cuerpo": (
            "En la barra lateral:\n\n"
            "- **Año** — filtra todo el análisis (2023, 2024 o 2025).\n"
            "- **Actualizar planilla** — vuelve a leer el Google Sheets del PEI "
            f"([abrir planilla]({PEI_SHEET_URL})).\n\n"
            "Cada fila del formulario = **una actividad** cargada por una unidad. "
            "El total de formularios coincide con Looker Studio («Cantidad total de actividades»)."
        ),
    },
    {
        "titulo": "Análisis · indicadores",
        "icono": "📊",
        "cuerpo": (
            "En la primera pantalla, arriba:\n\n"
            "- **Métricas** — formularios del año, objetivos OG1–OG6, sedes.\n"
            "- **Serie histórica** — compara alumnos, docentes, investigación y extensión "
            "entre años (alumnos/docentes desde memorias; actividades desde la planilla).\n\n"
            "Los colores verde/rojo en **Δ último año** marcan subas o bajas respecto del año anterior."
        ),
    },
    {
        "titulo": "Análisis · planillas PEI",
        "icono": "🗂️",
        "cuerpo": (
            "Más abajo, las pestañas del año elegido:\n\n"
            "- **Objetivos generales** — volumen y % por OG.\n"
            "- **Funciones sustantivas** — Docencia (alumnos, docentes), Investigación, Extensión.\n"
            "- **Sedes** — San Juan, San Luis, Mendoza.\n"
            "- **Evolución anual** — serie 2023–2025 de actividades del plan.\n"
            "- **Detalle por unidad** — cada facultad o secretaría.\n\n"
            "La escala de color ayuda a ver concentraciones (rojo → verde)."
        ),
    },
    {
        "titulo": "Gemelo · estado actual",
        "icono": "🔍",
        "cuerpo": (
            "En **Gemelo digital**, la primera sección muestra el **estado base** del año elegido: "
            "distribución por sede, actividades por función sustantiva y la guía "
            "«Qué objetivo impulsa qué indicador».\n\n"
            "Útil para responder: *¿qué objetivo del PEI empuja alumnos, convenios o identidad católica?*"
        ),
    },
    {
        "titulo": "Gemelo · simulación",
        "icono": "⚙️",
        "cuerpo": (
            "Los **controles OG1–OG6** (100 % = memoria del año base) permiten simular "
            "más actividades en un objetivo sin **recortar** las demás funciones.\n\n"
            "- Subir **OG2** → más extensión y convenios.\n"
            "- Subir **OG3** → más docencia (alumnos y docentes proyectados).\n"
            "- Subir **OG6** → más identidad católica e institucional.\n\n"
            "Abajo verás tablas con **Δ** en actividades e indicadores operativos (simulación ilustrativa)."
        ),
    },
    {
        "titulo": "Fuentes y buenas prácticas",
        "icono": "✅",
        "cuerpo": (
            "**Fuentes:** planilla PEI (actividades), Memoria Académica 2025 (matrícula por sede), "
            "Memorias Económicas 2023–2024 (docentes totales; alumnos estimados por serie PEI).\n\n"
            "**Sugerencia:** empezá en **2025**, revisá la serie histórica y luego probá en el Gemelo "
            "subir OG2 u OG3 para ver el impacto en extensión o docencia.\n\n"
            "Podés reabrir este tour cuando quieras desde la barra lateral."
        ),
    },
]


def _tour_step() -> int:
    return int(st.session_state.get("tour_step", 0))


def _set_tour_step(step: int) -> None:
    st.session_state["tour_step"] = max(0, min(step, len(TOUR_STEPS) - 1))


@st.dialog("Tour guiado · Gemelo Digital", width="large")
def _tour_dialog() -> None:
    step = _tour_step()
    total = len(TOUR_STEPS)
    actual = TOUR_STEPS[step]

    st.markdown(
        f"""
        <div style="
            background:{GREEN_LIGHT};
            border-left:4px solid {GREEN};
            padding:0.75rem 1rem;
            border-radius:0 8px 8px 0;
            margin-bottom:1rem;
        ">
            <span style="font-size:1.5rem;">{actual["icono"]}</span>
            <strong style="color:{GREEN}; margin-left:0.35rem;">Paso {step + 1} de {total}</strong>
            <span style="color:{TEXT_MUTED};"> — {actual["titulo"]}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    progreso = (step + 1) / total
    st.progress(progreso, text=f"{actual['titulo']}")

    st.markdown(actual["cuerpo"])

    if step == 0:
        omitir = st.checkbox("No mostrar automáticamente al entrar", value=False, key="tour_skip_auto")
        if omitir:
            st.session_state["tour_auto"] = False

    c_prev, c_next, c_close = st.columns([1, 1, 2])
    with c_prev:
        if step > 0 and st.button("← Anterior", use_container_width=True):
            _set_tour_step(step - 1)
            st.rerun()
    with c_next:
        if step < total - 1 and st.button("Siguiente →", type="primary", use_container_width=True):
            _set_tour_step(step + 1)
            st.rerun()
        elif step == total - 1 and st.button("Finalizar", type="primary", use_container_width=True):
            st.session_state["tour_completed"] = True
            st.session_state["tour_open"] = False
            st.rerun()
    with c_close:
        if st.button("Cerrar tour", use_container_width=True):
            st.session_state["tour_open"] = False
            st.rerun()


def render_tour_sidebar() -> None:
    """Controles del tour en la barra lateral (todas las pantallas)."""
    if "tour_auto" not in st.session_state:
        st.session_state["tour_auto"] = True
    if "tour_completed" not in st.session_state:
        st.session_state["tour_completed"] = False
    if "tour_open" not in st.session_state:
        st.session_state["tour_open"] = False

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f'<p style="color:{GREEN}; font-weight:600; margin-bottom:0.25rem;">'
        f"¿Primera vez acá?</p>",
        unsafe_allow_html=True,
    )
    if st.sidebar.button("Iniciar tour guiado", use_container_width=True, type="primary"):
        st.session_state["tour_open"] = True
        _set_tour_step(0)

    if st.session_state.get("tour_auto") and not st.session_state.get("tour_completed"):
        st.sidebar.caption(
            "Al abrir la app se ofrece un recorrido breve. "
            "Podés desactivarlo dentro del tour."
        )

    if st.session_state.get("tour_open"):
        _tour_dialog()


def maybe_auto_start_tour() -> None:
    """Muestra el tour una vez por sesión si el usuario no lo desactivó."""
    if (
        st.session_state.get("tour_auto", True)
        and not st.session_state.get("tour_completed")
        and not st.session_state.get("tour_auto_started")
    ):
        st.session_state["tour_auto_started"] = True
        st.session_state["tour_open"] = True
        _set_tour_step(0)
