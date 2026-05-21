/**
 * CONFIGURACIÓN — Secretaría de Investigación (espejo del Observatorio)
 *
 * Misma planilla Google · proyecto Apps Script NUEVO en google-apps-script/
 * Clave panel Secretaría: SEC-Investigacion-2026
 * Clave Observatorio (solo su sitio): OIA-Privado-2026
 */

/** Pegá acá la URL /exec después de desplegar PublicacionesWeb.gs (proyecto nuevo). */
var SEC_APPS_SCRIPT_PRODUCCION = {
  APPS_SCRIPT_URL: "",
  ADMIN_URL: ""
};

/** Prueba local: usa el script del OIA hasta tener la URL de Secretaría. */
var SEC_APPS_SCRIPT_LOCAL_OIA = {
  APPS_SCRIPT_URL:
    "https://script.google.com/macros/s/AKfycbwwHlP8QpZsm_uK2Kwcauk1BvgmsWl5f_VrFFNQJzq6r4NcLUgHosaFO8uVRmy6mfiRig/exec",
  ADMIN_URL:
    "https://script.google.com/macros/s/AKfycbwwHlP8QpZsm_uK2Kwcauk1BvgmsWl5f_VrFFNQJzq6r4NcLUgHosaFO8uVRmy6mfiRig/exec?action=admin&key=OIA-Privado-2026"
};

window.SEC_PUBLICACIONES =
  SEC_APPS_SCRIPT_PRODUCCION.APPS_SCRIPT_URL &&
  String(SEC_APPS_SCRIPT_PRODUCCION.APPS_SCRIPT_URL).trim()
    ? SEC_APPS_SCRIPT_PRODUCCION
    : SEC_APPS_SCRIPT_LOCAL_OIA;
