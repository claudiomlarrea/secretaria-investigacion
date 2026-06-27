# Secretaría de Investigación · UCCuyo

Este repositorio incluye **MDeIA UCCuyo** (madurez digital e IA) y el sitio web estático de la Secretaría.

## MDeIA UCCuyo — Madurez digital e IA

Sistema de medición del **Índice de Madurez Digital (IMD)** para la UCCuyo.
Detalle en [`MODELO-MDEIA.md`](MODELO-MDEIA.md).

```bash
cd ~/Documents/secretaria-investigacion
streamlit run streamlit_app.py
```

Abrí: http://localhost:8501

> El **Gemelo Digital del PEI** es otro sistema: `streamlit run gemelo_streamlit_app.py`

---

## Sitio web estático

## Ver en local

```bash
cd ~/Documents/secretaria-investigacion
python3 -m http.server 8080
```

Abrí: http://localhost:8080

## Repositorio y sitio publicado

| | Enlace |
|---|--------|
| **Repositorio** | https://github.com/claudiomlarrea/secretaria-investigacion |
| **Sitio en vivo** | https://claudiomlarrea.github.io/secretaria-investigacion/ |

Cada `git push` a `main` vuelve a publicar el sitio (GitHub Actions).

### Actualizar cambios

```bash
cd ~/Documents/secretaria-investigacion
git add -A
git commit -m "Descripción del cambio"
git push
```

### Redirect desde Google Sites

Usá la URL del sitio en vivo en el [Google Sites actual](https://sites.google.com/uccuyo.edu.ar/tablero-de-investigacion/inicio) (bloque HTML con `window.location.replace` o enlace visible).

## Estructura del proyecto

| Ruta | Uso |
|------|-----|
| `streamlit_app.py` | **MDeIA UCCuyo** — madurez digital e IA |
| `modelo_mdeia/` | Catálogo, lógica IMD y app Streamlit |
| `gemelo_streamlit_app.py` | Gemelo Digital del PEI (app aparte) |
| `index.html` | Página única con todas las secciones |
| `css/` | Estilos institucionales |
| `js/main.js` | Menú móvil |
| `assets/logo-uccuyo.png` | Escudo UCCuyo |

## Menú de cabecera

Cada sección con `id` en el `<main>` debe tener su enlace en el `<nav>`:

`#inicio` · `#la-secretaria` · `#consejo-investigacion` · `#ordenanza-general` · `#equipo` · `#contacto`

## Contacto

investigacion@uccuyo.edu.ar
