#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
pbcopy < "$DIR/PublicacionesWeb.gs"
open "https://script.google.com/home/projects/19z0bOktBiOQ0b8tA8EByQEm-oP9jNHFzvlyniDZmN-pSpdyXo1bc52ps/edit"
echo ""
echo "✓ Código copiado al portapapeles."
echo ""
echo "En el navegador:"
echo "  1. Panel izquierdo → PublicacionesWeb.gs (NO SyncLookerOpenAlex.gs)"
echo "  2. Cmd+A → Cmd+V → Cmd+S"
echo "  3. Implementar → Administrar implementaciones → lápiz → Nueva versión → Implementar"
echo ""
