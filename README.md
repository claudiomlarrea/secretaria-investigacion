# Secretaría de Investigación — sitio web

Sitio estático de la **Secretaría de Investigación** de la Universidad Católica de Cuyo (UCCuyo). Misma paleta y navegación por secciones que el sitio del Observatorio de IA.

## Ver en local

```bash
cd ~/Documents/secretaria-investigacion
python3 -m http.server 8080
```

Abrí: http://localhost:8080

## Publicar en GitHub Pages

### 1. Crear el repositorio en GitHub

En [github.com/new](https://github.com/new):

- **Nombre:** `secretaria-investigacion` (o el que prefieras)
- **Público**
- Sin README ni `.gitignore` (ya están en este proyecto)

### 2. Subir el código (primera vez)

```bash
cd ~/Documents/secretaria-investigacion
git remote add origin https://github.com/TU_USUARIO/secretaria-investigacion.git
git push -u origin main
```

(Reemplazá `TU_USUARIO` por tu cuenta de GitHub.)

### 3. Activar GitHub Pages

En el repo: **Settings → Pages → Build and deployment → Source:** **GitHub Actions**.

El workflow `.github/workflows/deploy-pages.yml` publica automáticamente en cada `push` a `main`.

### 4. URL del sitio

Tras el primer deploy (unos minutos):

`https://TU_USUARIO.github.io/secretaria-investigacion/`

Esa URL es la que conviene usar en el **redirect** del [Google Sites actual](https://sites.google.com/uccuyo.edu.ar/tablero-de-investigacion/inicio).

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
