/**
 * Sincroniza publicaciones UCCuyo (OpenAlex) hacia una hoja para Looker Studio.
 * Campos: anio, titulo, autores, doi, url, fuente, fecha_sync
 *
 * Si hay error 429: esperá 15 min y ejecutá syncLookerSolo2024 (o syncLookerSolo2023).
 */

var LOOKER_SHEET_ID = "10SKDfZJIZGSTOaOWgGmB46WPM0Bd0BvLe4aZ9jilA34";
var LOOKER_SHEET_NAME = "Hoja 1";
var OPENALEX_INSTITUTION_ID_LOOKER = "I4210121591";
var OPENALEX_MAILTO_LOOKER = "investigacion@uccuyo.edu.ar";
var LOOKER_MIN_YEAR = 1990;
var LOOKER_PER_PAGE = 50;
var LOOKER_MAX_PAGES = 30;
var LOOKER_SLEEP_MS = 1500;
var OPENALEX_MAX_RETRIES = 6;
var OPENALEX_WAIT_BEFORE_START_MS = 5000;

function syncLookerPruebaUnaPagina() {
  syncLookerPublicacionesOpenAlex_(1, null);
}

function syncLookerSolo2024() {
  syncLookerSoloAnio(2024);
}

function syncLookerSolo2023() {
  syncLookerSoloAnio(2023);
}

function syncLookerSoloAnio(anio) {
  syncLookerPublicacionesOpenAlex_(8, anio);
}

function syncLookerAniosRecientes() {
  var y = Number(Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy"));
  for (var year = y; year >= 2020; year--) {
    Logger.log("Sincronizando año " + year);
    syncLookerPublicacionesOpenAlex_(8, year);
    Utilities.sleep(25000);
  }
}

function syncLookerPublicacionesOpenAlex() {
  syncLookerPublicacionesOpenAlex_(LOOKER_MAX_PAGES, null);
}

function syncLookerPublicacionesOpenAlex_(maxPages, soloAnio) {
  Utilities.sleep(OPENALEX_WAIT_BEFORE_START_MS);
  var sheet = getLookerSheet_();
  ensureLookerHeaders_(sheet);

  var existing = getExistingKeys_(sheet);
  var rowsToAppend = [];
  var now = new Date();
  var fetched = 0;
  var added = 0;

  for (var page = 1; page <= maxPages; page++) {
    var data = fetchOpenAlexPage_(page, soloAnio);
    var works = (data && data.results) || [];
    if (!works.length) break;

    for (var i = 0; i < works.length; i++) {
      var w = works[i] || {};
      var row = mapWorkToLookerRow_(w, now);
      if (!row) continue;
      fetched++;

      var key = buildLookerKey_(row[3], row[1], row[0]);
      if (existing[key]) continue;
      existing[key] = true;
      rowsToAppend.push(row);
      added++;
    }

    if (works.length < LOOKER_PER_PAGE) break;
    Utilities.sleep(LOOKER_SLEEP_MS);
  }

  if (rowsToAppend.length) {
    var startRow = sheet.getLastRow() + 1;
    sheet.getRange(startRow, 1, rowsToAppend.length, rowsToAppend[0].length).setValues(rowsToAppend);
  }

  Logger.log(JSON.stringify({ ok: true, fetched: fetched, added: added, sheet: LOOKER_SHEET_NAME }));
}

function createDailyLookerSyncTrigger() {
  ScriptApp.newTrigger("syncLookerSolo2024").timeBased().everyDays(1).atHour(7).create();
}

function deleteLookerSyncTriggers() {
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    var fn = triggers[i].getHandlerFunction();
    if (fn.indexOf("syncLooker") === 0) ScriptApp.deleteTrigger(triggers[i]);
  }
}

function getLookerSheet_() {
  var ss = SpreadsheetApp.openById(LOOKER_SHEET_ID);
  var sh = ss.getSheetByName(LOOKER_SHEET_NAME);
  if (!sh) sh = ss.insertSheet(LOOKER_SHEET_NAME);
  return sh;
}

function ensureLookerHeaders_(sheet) {
  var headers = ["anio", "titulo", "autores", "doi", "url", "fuente", "fecha_sync"];
  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    return;
  }
  var current = sheet.getRange(1, 1, 1, headers.length).getValues()[0];
  var needsUpdate = false;
  for (var i = 0; i < headers.length; i++) {
    if (String(current[i] || "").trim() !== headers[i]) {
      needsUpdate = true;
      break;
    }
  }
  if (needsUpdate) sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
}

function getExistingKeys_(sheet) {
  var out = {};
  var lastRow = sheet.getLastRow();
  if (lastRow < 2) return out;

  var values = sheet.getRange(2, 1, lastRow - 1, 4).getValues();
  for (var i = 0; i < values.length; i++) {
    out[buildLookerKey_(values[i][3], values[i][1], values[i][0])] = true;
  }
  return out;
}

function buildLookerKey_(doi, titulo, anio) {
  var d = normalizeDoi_(doi).toLowerCase();
  if (d) return "doi:" + d;
  return "t:" + normalizeText_(titulo) + "|y:" + String(anio || "");
}

function fetchOpenAlexPage_(page, soloAnio) {
  var filters = ["authorships.institutions.lineage:" + OPENALEX_INSTITUTION_ID_LOOKER];
  if (soloAnio) {
    filters.push("publication_year:" + soloAnio);
  } else {
    filters.push("from_publication_date:" + LOOKER_MIN_YEAR + "-01-01");
    filters.push("to_publication_date:" + isoDate_(new Date()));
  }

  var params = [
    "filter=" + encodeURIComponent(filters.join(",")),
    "sort=publication_date:desc",
    "per-page=" + LOOKER_PER_PAGE,
    "page=" + page,
    "mailto=" + encodeURIComponent(OPENALEX_MAILTO_LOOKER)
  ];
  var url = "https://api.openalex.org/works?" + params.join("&");
  var attempt = 0;

  while (attempt < OPENALEX_MAX_RETRIES) {
    attempt++;
    var res = UrlFetchApp.fetch(url, {
      method: "get",
      muteHttpExceptions: true,
      headers: {
        Accept: "application/json",
        "User-Agent": "mailto:" + OPENALEX_MAILTO_LOOKER + " (Sync Looker UCCuyo)"
      }
    });
    var code = res.getResponseCode();

    if (code >= 200 && code < 300) return JSON.parse(res.getContentText());

    if (code === 429 && attempt < OPENALEX_MAX_RETRIES) {
      var waitMs = [5000, 10000, 20000, 30000, 45000, 60000][attempt - 1] || 60000;
      Logger.log("OpenAlex 429 pág " + page + ": espera " + waitMs + " ms (" + attempt + ")");
      Utilities.sleep(waitMs);
      continue;
    }

    throw new Error("OpenAlex HTTP " + code + " en página " + page);
  }

  throw new Error("OpenAlex: sin respuesta tras reintentos en página " + page);
}

function mapWorkToLookerRow_(w, now) {
  var anio = Number(w.publication_year || 0);
  var maxY = Number(Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy"));
  if (!anio || anio < LOOKER_MIN_YEAR || anio > maxY) return null;

  var titulo = String(w.display_name || "").trim();
  if (!titulo) return null;

  var autores = ((w.authorships || [])
    .map(function (a) {
      return a && a.author && a.author.display_name;
    })
    .filter(Boolean)
    .join(", "));

  var doi = normalizeDoi_(w.doi || "");
  var loc = w.primary_location || {};
  var url = doi ? "https://doi.org/" + doi : String(loc.landing_page_url || loc.pdf_url || w.id || "").trim();

  return [
    anio,
    titulo,
    autores,
    doi,
    url,
    "OpenAlex",
    Utilities.formatDate(now, Session.getScriptTimeZone(), "yyyy-MM-dd HH:mm:ss")
  ];
}

function normalizeDoi_(raw) {
  var s = String(raw || "").trim();
  s = s.replace(/^https?:\/\/(?:dx\.)?doi\.org\//i, "");
  s = s.replace(/^doi:\s*/i, "");
  return s.trim();
}

function normalizeText_(s) {
  return String(s || "")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

function isoDate_(d) {
  return Utilities.formatDate(d, "UTC", "yyyy-MM-dd");
}
