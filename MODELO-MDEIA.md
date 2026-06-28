MDeIA UCCuyo — Madurez digital e IA · UCCuyo
=============================================

Sistema de medición del **Índice de Madurez Digital (IMD)** e Inteligencia Artificial
para la Universidad Católica de Cuyo. Desarrollado por el Observatorio de IA.

Basado en **UDigital madurez** (MetaRed) con extensión **MDeIA** propia de la UCCuyo.

## Ejecutar en local

### Piloto Fase 1 (recomendado)

1. Abrí la app → sección **Piloto Fase 1**
2. Revisá la **Guía de sesión** (90 min, participantes, agenda)
3. Completá los **36 indicadores** en Encuesta piloto
4. Descargá el **informe HTML** y guardalo como PDF

```bash
cd ~/Documents/secretaria-investigacion
pip install -r modelo_mdeia/requirements.txt
streamlit run streamlit_app.py
```

Abrí en **Safari o Chrome**: http://localhost:8501

## Gemelo Digital del PEI (app aparte)

```bash
cd ~/Documents/secretaria-investigacion
.venv-gemelo/bin/pip install -r requirements.txt
.venv-gemelo/bin/streamlit run gemelo_streamlit_app.py
```

## Estructura

| Ruta | Uso |
|------|-----|
| `streamlit_app.py` | Entrada a **MDeIA UCCuyo** |
| `modelo_mdeia/app.py` | Aplicación principal |
| `modelo_mdeia/data/framework.json` | Marco: retos, objetivos, fases |
| `modelo_mdeia/data/indicadores_*.json` | Catálogo de indicadores |
| `modelo_mdeia/lib/mdeia_model.py` | Cálculo del IMD |

## Fórmula IMD

```
IMD = (P_satisfechas / P_totales) × 100
```

## Contacto

observatorioia@uccuyo.edu.ar
