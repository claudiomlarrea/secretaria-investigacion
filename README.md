# Secretaría de Investigación — sitio web

Sitio estático de la **Secretaría de Investigación** de la Universidad Católica de Cuyo (UCCuyo). Misma paleta y navegación por secciones que el sitio del Observatorio de IA.

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
| `index.html` | Página única con todas las secciones |
| `css/` | Estilos institucionales |
| `js/main.js` | Menú móvil |
| `assets/logo-uccuyo.png` | Escudo UCCuyo |

## Menú de cabecera

Cada sección con `id` en el `<main>` debe tener su enlace en el `<nav>`:

`#inicio` · `#la-secretaria` · `#consejo-investigacion` · `#ordenanza-general` · `#equipo` · `#contacto`

## Contacto

investigacion@uccuyo.edu.ar
