/**
 * Publicaciones — espejo del Observatorio para el sitio Secretaría de Investigación.
 *
 * Misma planilla que OIA (Publicaciones Observatorio · Hoja 1).
 * Proyecto Apps Script NUEVO (no reemplazar el del Observatorio).
 *
 * Diferencias con OIA:
 * - Clave de panel: SEC-Investigacion-2026 (OIA usa OIA-Privado-2026).
 * - Unidad por defecto al cargar: Secretaría de Investigación.
 * - La web Secretaría lista todo lo publicado en la planilla (todas las unidades);
 *   en cada fila se ve la unidad académica. OIA sigue filtrando solo filas OIA.
 *
 * Endpoints:
 * - GET  (sin action): JSON para la web pública.
 * - GET  ?action=admin: panel HTML de carga.
 * - GET  ?action=visit&site=secretaria|observatorio: contador de visitas a cada página web.
 * - POST ?action=add: agrega fila en la misma hoja.
 */

var SPREADSHEET_ID = "18xXPRok4kVF81hkEDDlfDf8Vx-KI2HeywZNFSXkozwU";
var HOJA_PUBLICACIONES = "Hoja 1";
/** false = misma planilla compartida, se listan todas las unidades (la UI muestra cuál es cada una). */
var SOLO_FILA_SECRETARIA = false;
var PATRON_UNIDAD_SEC =
  /Secretaría de Investigación|Secretaria de Investigacion|SEC.*Investigación/i;
var ESTADO_PUBLICABLE = "publicado";

var LOOKER_SHEET_ID = "10SKDfZJIZGSTOaOWgGmB46WPM0Bd0BvLe4aZ9jilA34";
var LOOKER_TAB = "indice_openalex";
var LOOKER_HEADERS = ["anio", "titulo", "autores", "doi", "url", "fuente", "fecha_sync"];

var ADMIN_ACCESS_KEY = "SEC-Investigacion-2026";

var AUTHORIZED_EMAILS = [
  "claudio.larrea@hotmail.com",
  "claudio17larrea@gmail.com",
  "investigacion@uccuyo.edu.ar",
  "observatorioia@uccuyo.edu.ar",
  "barias@uccuyo.edu.ar",
  "vincutec@uccuyo.edu.ar",
  "asistente.inv@uccuyo.edu.ar",
  "jose.lamalfa@uccuyosl.edu.ar",
  "laurapizarro92@gmail.com",
  "lpizarro@uccuyo.edu.ar"
];

/** Misma lista que Consejo / Producción Científica (Streamlit) + unidades transversales. */
var UNIDADES_ACADEMICAS = [
  "FDCSSL- Facultad de Derecho y Ciencias Sociales Sede San Luis",
  "FCMSL- Facultad de Ciencias Médicas Sede San Luis",
  "FCVSL- Facultad de Ciencias Veterinarias Sede San Luis",
  "FCEESL- Facultad de Ciencias Económicas y Empresariales Sede San Luis",
  "FBOSCO- Facultad Don Bosco",
  "FCEESJ- Facultad de Ciencias Económicas y Empresariales Sede San Juan",
  "FFyHSJ- Facultad de Filosofía y Humanidades",
  "ISDSM- Instituto Universitario Santa María",
  "ECRyPSJ- Escuela Cultura Religiosa y Pastoral",
  "FDCSSJ- Facultad de Derecho y Ciencias Sociales Sede San Juan",
  "FCMSJ- Facultad de Ciencias Médicas San Juan",
  "FEDSJ- Facultad de Educación",
  "ESEGSJ- Escuela de Seguridad",
  "FCQyTSJ- Facultad de Ciencias Químicas y Tecnológicas",
  "ISB- Instituto San Buenaventura",
  "Secretaría de Investigación",
  "Unidad de Vinculación Tecnológica",
  "OIA- Observatorio de Inteligencia Artificial",
  "Vicerrectora de Formación",
  "Departamento de Educación a Distancia"
];

function getUnidadesAcademicas_() {
  return UNIDADES_ACADEMICAS.slice();
}

function doGet(e) {
  var action = param_(e, "action", "public");
  if (action === "admin") {
    return renderAdmin_(e);
  }
  if (action === "visit") {
    return jsonOrJsonp_(registrarVisita_(param_(e, "site", "")), e);
  }
  if (action === "noticias") {
    return jsonOrJsonp_(obtenerNoticiasMedios_(), e);
  }

  var datos = obtenerItemsPublicos_();
  return jsonOrJsonp_({ ok: true, generatedAt: new Date().toISOString(), items: datos }, e);
}

function doPost(e) {
  var payload = mergePostParams_(e);
  var action = val_(payload.action) || param_(e, "action", "add");

  if (action !== "add") return json_({ ok: false, error: "invalid_action" });

  var fromPanel = val_(payload._panel) === "1";

  if (!isAuthorized_(e)) {
    if (fromPanel) return panelSaveResponse_(false, "No autorizado", payload);
    return json_({ ok: false, error: "unauthorized" });
  }

  var row = payloadToRow_(payload);

  if (!row[0] || !row[1] || !row[6]) {
    if (fromPanel) return panelSaveResponse_(false, "Completá tipo, título y unidad", payload);
    return json_({ ok: false, error: "required_fields", message: "tipo, titulo y unidad son obligatorios" });
  }

  try {
    getSheet_().appendRow(row);
    SpreadsheetApp.flush();
    mirrorPublicationToLooker_(payload);
  } catch (err) {
    if (fromPanel) return panelSaveResponse_(false, String(err), payload);
    return json_({ ok: false, error: "save_failed", message: String(err) });
  }

  if (fromPanel) return panelSaveResponse_(true, "Guardado correctamente", payload);
  return json_({ ok: true });
}

function panelAdminReturnUrl_(ok, message, payload) {
  var url = ScriptApp.getService().getUrl() + "?action=admin";
  var key = val_(payload && payload.key);
  if (key) url += "&key=" + encodeURIComponent(key);
  if (ok) return url + "&saved=1";
  return url + "&saved=0&err=" + encodeURIComponent(String(message || "error"));
}

function panelSaveResponse_(ok, message, payload) {
  return HtmlService.createHtmlOutput(panelRedirectHtml_(panelAdminReturnUrl_(ok, message, payload))).setXFrameOptionsMode(
    HtmlService.XFrameOptionsMode.ALLOWALL
  );
}

function savePublicationAdmin_(payload) {
  try {
    payload = payload || {};
    if (!isAuthorizedForPayload_(payload)) {
      return {
        ok: false,
        message:
          "No autorizado. Abrí el panel desde «Ingreso equipo · Cargar publicaciones» en el sitio."
      };
    }
    var row = payloadToRow_(payload);
    if (!row[0] || !row[1] || !row[6]) {
      return { ok: false, message: "Completá tipo, título y unidad." };
    }
    getSheet_().appendRow(row);
    SpreadsheetApp.flush();
    mirrorPublicationToLooker_(payload);
    return { ok: true, message: "Guardado" };
  } catch (err) {
    return { ok: false, message: String(err) };
  }
}

function mirrorPublicationToLooker_(p) {
  if (!LOOKER_SHEET_ID) return;
  try {
    var est = normalizar_(val_(p.estado) || ESTADO_PUBLICABLE);
    if (est === "borrador") return;

    var sh = SpreadsheetApp.openById(LOOKER_SHEET_ID).getSheetByName(LOOKER_TAB);
    if (!sh) sh = SpreadsheetApp.openById(LOOKER_SHEET_ID).insertSheet(LOOKER_TAB);

    if (sh.getLastRow() === 0) {
      sh.getRange(1, 1, 1, LOOKER_HEADERS.length).setValues([LOOKER_HEADERS]);
    }

    var doi = normalizeDoiForLooker_(val_(p.doi));
    if (doi && lookerHasDoi_(sh, doi)) return;

    var anio = val_(p.anio);
    if (/^\d{4}\/\d/.test(anio)) {
      try {
        anio = String(new Date(anio).getFullYear());
      } catch (_e) {}
    }
    var link = val_(p.link);
    if (!link && doi) link = "https://doi.org/" + doi;
    var now = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd HH:mm:ss");

    sh.appendRow([anio, val_(p.titulo), val_(p.autores), doi, link, "Registro manual", now]);
  } catch (err) {
    Logger.log("mirrorPublicationToLooker_: " + err);
  }
}

function normalizeDoiForLooker_(raw) {
  var s = String(raw || "").trim();
  s = s.replace(/^https?:\/\/(?:dx\.)?doi\.org\//i, "");
  s = s.replace(/^doi:\s*/i, "");
  return s.trim();
}

function lookerHasDoi_(sh, doi) {
  var last = sh.getLastRow();
  if (last < 2) return false;
  var vals = sh.getRange(2, 4, last - 1, 1).getValues();
  var needle = doi.toLowerCase();
  for (var i = 0; i < vals.length; i++) {
    if (normalizeDoiForLooker_(vals[i][0]).toLowerCase() === needle) return true;
  }
  return false;
}

function authorizeSavePanel() {
  var r = savePublicationAdmin_({
    key: ADMIN_ACCESS_KEY,
    tipo: "Diario",
    titulo: "Prueba permisos panel",
    unidad: "Secretaría de Investigación",
    estado: "publicado"
  });
  Logger.log(JSON.stringify(r));
  return r;
}

function isAuthorizedForPayload_(p) {
  var email = getEmail_();
  if (email && AUTHORIZED_EMAILS.indexOf(email) >= 0) return true;
  return val_(p && p.key) === ADMIN_ACCESS_KEY;
}

function renderAdmin_(e) {
  if (!isAuthorized_(e)) {
    return HtmlService.createHtmlOutput(
      "<h3>Acceso denegado</h3>" +
        "<p>No se pudo validar el acceso. En las apps web de Google el correo con el que entraste " +
        "casi nunca se detecta automáticamente.</p>" +
        "<p><strong>Cómo entrar:</strong> usá el botón " +
        "<em>Ingreso equipo · Cargar publicaciones</em> en la sección Publicaciones del sitio " +
        "(ese enlace incluye la clave de acceso).</p>" +
        "<p>Si abriste esta página a mano, la URL debe terminar en " +
        "<code>?action=admin&amp;key=SEC-Investigacion-2026</code> " +
        "(clave del proyecto Secretaría, no la del Observatorio).</p>"
    ).setTitle("Secretaría - Acceso denegado");
  }
  var t = HtmlService.createTemplateFromFile("PublicacionesAdmin");
  t.apiUrl = ScriptApp.getService().getUrl();
  var keyFromUrl = adminKeyFromRequest_(e);
  t.adminKey = keyFromUrl === ADMIN_ACCESS_KEY ? keyFromUrl : ADMIN_ACCESS_KEY;
  t.unidades = getUnidadesAcademicas_();
  t.defaultUnidad = "Secretaría de Investigación";
  return t
    .evaluate()
    .setTitle("Carga de Publicaciones")
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function obtenerItemsPublicos_() {
  var values = getSheet_().getDataRange().getDisplayValues();
  if (!values.length) return [];

  var startIdx = tieneHeader_(values[0]) ? 1 : 0;
  var out = [];

  for (var i = startIdx; i < values.length; i++) {
    var o = rowAToObj_(values[i]);
    if (!o.titulo && !o.autores && !o.evento) continue;
    if (SOLO_FILA_SECRETARIA && !PATRON_UNIDAD_SEC.test(String(o.unidad || ""))) continue;
    if (!esVisibleEnWeb_(o)) continue;
    o.categoria = inferirCategoria_(o);
    out.push(o);
  }

  out.sort(comparadorFechaReciente_);
  return out;
}

function getSheet_() {
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var sh = ss.getSheetByName(HOJA_PUBLICACIONES);
  if (!sh) throw new Error("No existe la pestaña '" + HOJA_PUBLICACIONES + "'");
  return sh;
}

function esVisibleEnWeb_(o) {
  var est = normalizar_(o && o.estado);
  if (est === "borrador") return false;
  return true;
}

function payloadToRow_(p) {
  var estado = ESTADO_PUBLICABLE;
  return [
    val_(p.tipo),
    val_(p.titulo),
    val_(p.autores),
    val_(p.revista_o_medio),
    val_(p.doi),
    val_(p.anio),
    val_(p.unidad),
    val_(p.indexacion),
    val_(p.editorial),
    val_(p.isbn),
    val_(p.tipo_publicacion),
    val_(p.link),
    val_(p.evento),
    val_(p.lugar),
    val_(p.fecha),
    val_(p.resumen),
    val_(p.repositorio),
    estado
  ];
}

function rowAToObj_(row) {
  function g(i) {
    return row[i] != null ? String(row[i]).trim() : "";
  }
  var anio = g(5);
  if (/^\d{4}\/\d/.test(anio)) {
    try {
      anio = String(new Date(anio).getFullYear());
    } catch (_e) {}
  }
  return {
    tipo_origen: g(0),
    titulo: g(1),
    autores: g(2),
    revista_o_medio: g(3),
    doi: g(4),
    anio: anio,
    unidad: g(6),
    indexacion: g(7),
    editorial: g(8),
    isbn: g(9),
    tipo_publicacion: g(10),
    link: g(11),
    evento: g(12),
    lugar: g(13),
    fecha: g(14),
    resumen: g(15),
    repositorio: g(16),
    estado: g(17)
  };
}

function inferirCategoria_(o) {
  var t = normalizar_(o.tipo_origen);
  var tp = normalizar_(o.tipo_publicacion);
  if (t === "revista") return "revistas";
  if (t === "repositorio") return "repositorios";
  if (t === "evento") return "eventos";
  if (t === "diario") return "diarios";
  if (t === "libro" || t.indexOf("capitulo") >= 0) return "libros";
  if (tp.indexOf("libro") >= 0 || tp.indexOf("capitulo") >= 0) return "libros";
  if (o.doi && (o.revista_o_medio || t === "revista")) return "revistas";
  if (o.repositorio || t.indexOf("repo") === 0) return "repositorios";
  if (o.evento) return "eventos";
  if (o.resumen && o.revista_o_medio && !o.doi) return "diarios";
  return "otros";
}

function comparadorFechaReciente_(a, b) {
  var ya = parseNum_(a.anio);
  var yb = parseNum_(b.anio);
  if (yb !== ya) return yb - ya;
  return String(b.fecha || "").localeCompare(String(a.fecha || ""));
}

function parseNum_(s) {
  var n = parseInt(String(s || ""), 10);
  return isNaN(n) ? 0 : n;
}

function parseBody_(e) {
  var raw = e && e.postData && e.postData.contents ? e.postData.contents : "{}";
  try {
    return JSON.parse(raw);
  } catch (_err) {
    return parseUrlEncoded_(raw);
  }
}

function parseUrlEncoded_(raw) {
  var out = {};
  if (!raw || String(raw).indexOf("=") < 0) return out;
  String(raw)
    .split("&")
    .forEach(function (pair) {
      var i = pair.indexOf("=");
      if (i < 0) return;
      var k = decodeURIComponent(pair.slice(0, i).replace(/\+/g, " "));
      var v = decodeURIComponent(pair.slice(i + 1).replace(/\+/g, " "));
      out[k] = v;
    });
  return out;
}

function mergePostParams_(e) {
  var out = {};
  var params = e && e.parameter ? e.parameter : {};
  var k;
  for (k in params) {
    if (params.hasOwnProperty(k)) out[k] = params[k];
  }
  var body = parseBody_(e);
  for (k in body) {
    if (body.hasOwnProperty(k)) out[k] = body[k];
  }
  return out;
}

function panelRedirectHtml_(url) {
  var safe = String(url)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;");
  return (
    "<!DOCTYPE html><html lang=\"es\"><head><meta charset=\"utf-8\">" +
    '<meta http-equiv="refresh" content="0;url=' +
    safe +
    '">' +
    "<script>var u=" +
    JSON.stringify(String(url)) +
    ";try{window.top.location.replace(u);}catch(e){window.location.replace(u);}</script>" +
    "</head><body><p>Volviendo al panel…</p></body></html>"
  );
}

function param_(e, key, def) {
  var p = e && e.parameter ? e.parameter : {};
  return p[key] != null ? String(p[key]) : def;
}

function tieneHeader_(r0) {
  var c0 = normalizar_(r0 && r0[0]);
  return c0 === "tipo" || c0 === "categoria";
}

function val_(x) {
  return x == null ? "" : String(x).trim();
}

function normalizar_(x) {
  return String(x || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
}

function getEmail_() {
  try {
    return String(Session.getActiveUser().getEmail() || "").toLowerCase().trim();
  } catch (_e) {
    return "";
  }
}

function isAuthorized_(e) {
  var email = getEmail_();
  if (email && AUTHORIZED_EMAILS.indexOf(email) >= 0) return true;
  if (adminKeyFromRequest_(e) === ADMIN_ACCESS_KEY) return true;
  if (e) {
    var payload = mergePostParams_(e);
    if (val_(payload.key) === ADMIN_ACCESS_KEY) return true;
  }
  return false;
}

function adminKeyFromRequest_(e) {
  if (!e || !e.parameter) return "";
  return val_(e.parameter.key);
}

function registrarVisita_(site) {
  var props = PropertiesService.getScriptProperties();
  var sec = parseInt(props.getProperty("visitas_web_secretaria") || "0", 10) || 0;
  var obs = parseInt(props.getProperty("visitas_web_observatorio") || "0", 10) || 0;
  if (site === "secretaria") {
    sec++;
    props.setProperty("visitas_web_secretaria", String(sec));
  } else if (site === "observatorio") {
    obs++;
    props.setProperty("visitas_web_observatorio", String(obs));
  }
  return { ok: true, secretaria: sec, observatorio: obs };
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

function jsonOrJsonp_(obj, e) {
  var json = JSON.stringify(obj);
  var callback = param_(e, "callback", "");
  if (callback && /^[a-zA-Z_$][a-zA-Z0-9_$]*$/.test(callback)) {
    return ContentService.createTextOutput(callback + "(" + json + ");").setMimeType(
      ContentService.MimeType.JAVASCRIPT
    );
  }
  return ContentService.createTextOutput(json).setMimeType(ContentService.MimeType.JSON);
}

var NOTICIAS_UCCUYO_API = "https://noticias.uccuyo.edu.ar/wp-json/wp/v2/posts";
var NOTICIAS_BUSQUEDAS_UCCUYO = [
  "observatorio inteligencia artificial",
  "observatorio de ia",
  "oia uccuyo",
  "boletin observatorio ia"
];
var NOTICIAS_GOOGLE_QUERIES = [
  '"Observatorio de Inteligencia Artificial" UCCuyo',
  '"Observatorio de IA" UCCuyo',
  "site:noticias.uccuyo.edu.ar observatorio inteligencia artificial"
];
var PATRON_UNIDAD_OIA_NOTICIAS = /OIA|Observatorio de Inteligencia Artificial/i;

function obtenerNoticiasMedios_() {
  var items = [];
  items = items.concat(fetchUccuyoNoticiasWp_());
  items = items.concat(fetchGoogleNewsRss_());
  items = items.concat(fetchPublicacionesMedios_());
  items = dedupeNoticias_(items);
  items = items.filter(function (it) {
    return !esMedioExcluidoNoticia_(it);
  });
  items.sort(comparadorNoticiaReciente_);
  return {
    ok: true,
    generatedAt: new Date().toISOString(),
    count: items.length,
    items: items
  };
}

function fetchUccuyoNoticiasWp_() {
  var out = [];
  var seen = {};
  NOTICIAS_BUSQUEDAS_UCCUYO.forEach(function (q) {
    try {
      var url =
        NOTICIAS_UCCUYO_API +
        "?search=" +
        encodeURIComponent(q) +
        "&per_page=20&_fields=id,date,link,title,excerpt";
      var resp = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
      if (resp.getResponseCode() !== 200) return;
      var posts = JSON.parse(resp.getContentText());
      if (!posts || !posts.length) return;
      posts.forEach(function (post) {
        var id = "uccuyo-" + post.id;
        if (seen[id]) return;
        var titulo = stripHtmlNoticia_(post.title && post.title.rendered);
        var excerpt = stripHtmlNoticia_(post.excerpt && post.excerpt.rendered);
        var texto = titulo + " " + excerpt;
        if (!esRelevanteOIA_(texto)) return;
        seen[id] = true;
        out.push({
          id: id,
          fuente: "Noticias UCCuyo",
          medio: "noticias.uccuyo.edu.ar",
          titulo: titulo,
          link: post.link,
          fecha: post.date,
          excerpt: excerpt,
          origen: "uccuyo_noticias"
        });
      });
    } catch (err) {
      Logger.log("fetchUccuyoNoticiasWp_: " + err);
    }
  });
  return out;
}

function fetchGoogleNewsRss_() {
  var out = [];
  var seen = {};
  NOTICIAS_GOOGLE_QUERIES.forEach(function (q) {
    try {
      var url =
        "https://news.google.com/rss/search?q=" +
        encodeURIComponent(q) +
        "&hl=es-419&gl=AR&ceid=AR:es-419";
      var resp = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
      if (resp.getResponseCode() !== 200) return;
      var doc = XmlService.parse(resp.getContentText());
      var channel = doc.getRootElement().getChild("channel");
      if (!channel) return;
      var rssItems = channel.getChildren("item");
      rssItems.forEach(function (item) {
        var rawTitle = item.getChildText("title") || "";
        var link = item.getChildText("link") || "";
        if (!link) return;
        var key = normalizarUrlNoticia_(link);
        if (seen[key]) return;
        var titulo = limpiarTituloGoogleNews_(rawTitle);
        var desc = stripHtmlNoticia_(item.getChildText("description") || "");
        var texto = titulo + " " + desc;
        if (!esRelevanteOIA_(texto)) return;
        seen[key] = true;
        var medio = extraerMedioGoogleNews_(rawTitle);
        out.push({
          id: "gnews-" + key.slice(0, 48),
          fuente: "Diario online",
          medio: medio,
          titulo: titulo,
          link: link,
          fecha: item.getChildText("pubDate") || "",
          excerpt: desc,
          origen: "google_news"
        });
      });
    } catch (err) {
      Logger.log("fetchGoogleNewsRss_: " + err);
    }
  });
  return out;
}

function fetchPublicacionesMedios_() {
  var values = getSheet_().getDataRange().getDisplayValues();
  if (!values.length) return [];
  var startIdx = tieneHeader_(values[0]) ? 1 : 0;
  var out = [];
  for (var i = startIdx; i < values.length; i++) {
    var o = rowAToObj_(values[i]);
    if (!esVisibleEnWeb_(o)) continue;
    if (!esPublicacionMedioOIA_(o)) continue;
    var cat = inferirCategoria_(o);
    var tipoNorm = normalizar_(o.tipo_origen);
    var esBoletin = tipoNorm.indexOf("boletin") >= 0 || normalizar_(o.tipo_publicacion).indexOf("boletin") >= 0;
    var link = val_(o.link);
    if (!link && o.doi) link = "https://doi.org/" + o.doi;
    if (!link) continue;
    out.push({
      id: "pub-" + i,
      fuente: esBoletin ? "Boletín" : "Medio registrado",
      medio: val_(o.revista_o_medio) || val_(o.unidad),
      titulo: val_(o.titulo),
      link: link,
      fecha: val_(o.fecha) || val_(o.anio),
      excerpt: val_(o.resumen),
      origen: esBoletin ? "boletin" : cat === "diarios" ? "diario_registrado" : "medio_registrado"
    });
  }
  return out;
}

function esPublicacionMedioOIA_(o) {
  var cat = inferirCategoria_(o);
  var tipoNorm = normalizar_(o.tipo_origen);
  var esBoletin = tipoNorm.indexOf("boletin") >= 0 || normalizar_(o.tipo_publicacion).indexOf("boletin") >= 0;
  if (cat !== "diarios" && !esBoletin) return false;
  var texto =
    val_(o.titulo) +
    " " +
    val_(o.resumen) +
    " " +
    val_(o.revista_o_medio) +
    " " +
    val_(o.unidad);
  if (PATRON_UNIDAD_OIA_NOTICIAS.test(val_(o.unidad))) return true;
  return esRelevanteOIA_(texto);
}

function esRelevanteOIA_(texto) {
  var t = normalizar_(texto);
  if (!t) return false;
  if (t.indexOf("observatorio de inteligencia artificial") >= 0) return true;
  if (t.indexOf("observatorio de ia") >= 0) return true;
  if (t.indexOf("observatorio de i.a") >= 0) return true;
  if (t.indexOf("oia de la uccuyo") >= 0) return true;
  if (t.indexOf("oia uccuyo") >= 0) return true;
  if (t.indexOf("observatorio") >= 0 && t.indexOf("inteligencia artificial") >= 0) return true;
  if (t.indexOf("observatorio") >= 0 && t.indexOf("uccuyo") >= 0 && /\bia\b/.test(t)) return true;
  return false;
}

function esMedioExcluidoNoticia_(item) {
  var blob = normalizar_(
    val_(item && item.medio) +
      " " +
      val_(item && item.link) +
      " " +
      val_(item && item.fuente) +
      " " +
      val_(item && item.titulo)
  );
  return blob.indexOf("diario de cuyo") >= 0 || blob.indexOf("diariodecuyo") >= 0;
}

function dedupeNoticias_(items) {
  var seen = {};
  var out = [];
  items.forEach(function (it) {
    var key = normalizarUrlNoticia_(it.link || it.id || "");
    if (!key || seen[key]) return;
    seen[key] = true;
    out.push(it);
  });
  return out;
}

function comparadorNoticiaReciente_(a, b) {
  return parseFechaNoticia_(b.fecha) - parseFechaNoticia_(a.fecha);
}

function parseFechaNoticia_(raw) {
  if (!raw) return 0;
  var s = String(raw).trim();
  if (/^\d{4}$/.test(s)) return parseInt(s, 10) * 10000;
  var t = Date.parse(s);
  return isNaN(t) ? 0 : t;
}

function normalizarUrlNoticia_(url) {
  return String(url || "")
    .toLowerCase()
    .replace(/^https?:\/\//, "")
    .replace(/\/$/, "")
    .replace(/\?.*$/, "")
    .trim();
}

function stripHtmlNoticia_(html) {
  return String(html || "")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&#039;/g, "'")
    .replace(/\s+/g, " ")
    .trim();
}

function limpiarTituloGoogleNews_(title) {
  var t = String(title || "").trim();
  var idx = t.lastIndexOf(" - ");
  if (idx > 0) return t.slice(0, idx).trim();
  return t;
}

function extraerMedioGoogleNews_(title) {
  var t = String(title || "").trim();
  var idx = t.lastIndexOf(" - ");
  if (idx > 0) return t.slice(idx + 3).trim();
  return "Google Noticias";
}
