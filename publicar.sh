#!/bin/bash
# Publica cambios en GitHub Pages (rama main).
set -e
cd "$(dirname "$0")"

MSG="${1:-Actualización del sitio Secretaría de Investigación}"

if [[ -z $(git status --porcelain) ]]; then
  echo "No hay cambios para publicar."
  exit 0
fi

git add -A
git commit -m "$MSG"
git push

echo ""
echo "Listo. En 1–2 minutos verás los cambios en:"
echo "https://claudiomlarrea.github.io/secretaria-investigacion/"
