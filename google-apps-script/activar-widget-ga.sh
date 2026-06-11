#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
pbcopy < "$DIR/PublicacionesWeb.gs"
open "https://script.google.com/home/projects/19z0bOktBiOQ0b8tA8EByQEm-oP9jNHFzvlyniDZmN-pSpdyXo1bc52ps/edit"
echo "✓ Código copiado. Pegá en SyncLookerOpenAlex.gs → Servicios: Analytics Data API → Nueva versión."
echo "  Ver ACTIVAR-WIDGET-GA.txt"
