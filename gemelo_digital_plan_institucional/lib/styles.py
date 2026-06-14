"""Compatibilidad: delega en ui_theme del Observatorio."""

from ui_theme import apply_plotly_style, inject_theme, render_page

apply_styles = inject_theme
render_header = render_page
