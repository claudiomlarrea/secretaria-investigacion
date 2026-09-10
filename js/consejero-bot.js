/**
 * Mesa de ayuda para consejeros: respuestas fijas del instructivo
 * (carga de temas y CVar). Sin API: funciona en GitHub Pages.
 */
(function () {
  var SISTEMA =
    "https://extractor-actas-investigacion-erpqi2qct7z5sapp3ucdyej.streamlit.app/";
  var ACTAS_DRIVE =
    "https://drive.google.com/drive/folders/14_QJAYZPCPkB_zCj0bBF1m1PssGNwE-S";
  var MAIL = "investigacion@uccuyo.edu.ar";

  function t(key, fallback) {
    if (window.I18N && typeof window.I18N.t === "function") return window.I18N.t(key);
    return fallback || key;
  }

  function lang() {
    return window.I18N && window.I18N.getLang ? window.I18N.getLang() : "es";
  }

  function normalize(text) {
    return String(text || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/\p{M}/gu, "")
      .replace(/[¿?¡!.,;:()]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  var ANSWERS = {
    "cargar-tema": {
      keywords: [
        "cargar un tema",
        "cargar tema",
        "cargar temas",
        "como cargo un tema",
        "como se carga un tema",
        "orden del dia",
        "orden del día",
        "formulario de temas",
        "enviar al consejo"
      ],
      extra: ["tema", "temas", "od"]
    },
    "cargar-cvar": {
      keywords: [
        "cargar un cvar",
        "cargar cvar",
        "cargar cvars",
        "como cargo un cvar",
        "como se carga un cvar",
        "subir cvar",
        "cvar 2026",
        "curriculum",
        "cv ar"
      ],
      extra: ["cvar", "cvars", "adjunto", "adjuntos", "archivo", "archivos", "drive"]
    },
    acta: {
      keywords: ["elegir el acta", "elegir acta", "acta en curso", "acta cerrada", "proxima"],
      extra: ["acta", "actas"]
    },
    descargar: {
      keywords: ["descargar orden", "descargar od", "generar orden", "word"],
      extra: ["descargar"]
    },
    login: {
      keywords: ["usuario", "contraseña", "contrasena", "password", "login", "pide clave"],
      extra: []
    },
    normativa: {
      keywords: ["ordenanza", "instructivo", "anexo", "normativa"],
      extra: []
    }
  };

  function htmlTema() {
    var en = lang() === "en";
    if (en) {
      return (
        "<p><strong>Load a topic (5 steps)</strong></p>" +
        "<ol>" +
        "<li>Portal → Research Council → <a href=\"" +
        SISTEMA +
        "\" target=\"_blank\" rel=\"noopener noreferrer\">Topic management system</a>.</li>" +
        "<li><strong>Minutes (Actas)</strong>: choose the current meeting. If it says “Cerrada”, do not use it.</li>" +
        "<li><strong>Cargar Temas</strong>: type, title, description (max. 50 words), participants, academic unit (max. 5), person responsible for the load.</li>" +
        "<li>Check <em>Temas ya cargados</em> → <em>Revisión</em> → send.</li>" +
        "<li>CVars and attachments are <strong>not</strong> in this form. Use <strong>Carga de Archivos</strong> (see “How to upload a CVar”).</li>" +
        "</ol>"
      );
    }
    return (
      "<p><strong>Cargar un tema (5 pasos)</strong></p>" +
      "<ol>" +
      "<li>Portal → Consejo → <a href=\"" +
      SISTEMA +
      "\" target=\"_blank\" rel=\"noopener noreferrer\">Sistema de gestión de temas</a>.</li>" +
      "<li><strong>Actas</strong>: elegí el acta en curso (si está “Cerrada”, no uses esa).</li>" +
      "<li><strong>Cargar Temas</strong>: tipo, denominación, descripción (máx. 50 palabras), participantes, UA (máx. 5), responsable de carga.</li>" +
      "<li>Mirá <em>Temas ya cargados</em> → <em>Revisión</em> → enviar.</li>" +
      "<li>CVars y adjuntos <strong>no van en el formulario</strong>. Van en <strong>Carga de Archivos</strong> (ver “Cómo cargar un CVar”).</li>" +
      "</ol>"
    );
  }

  function htmlCvar() {
    var en = lang() === "en";
    if (en) {
      return (
        "<p><strong>Upload a CVar / file</strong></p>" +
        "<ol>" +
        "<li>Open the system → <strong>Carga de Archivos</strong> (there is no uploader inside Streamlit).</li>" +
        "<li>Open the matching Drive folder: <strong>CVar 2026</strong> or the agenda / minutes of that meeting.</li>" +
        "<li>In Drive: your academic unit folder → <strong>New</strong> → <strong>File upload</strong>.</li>" +
        "<li>Check that the file is inside that folder.</li>" +
        "</ol>" +
        "<p>The topic form has no CV/attachment field. Signed minutes are in the <a href=\"" +
        ACTAS_DRIVE +
        "\" target=\"_blank\" rel=\"noopener noreferrer\">minutes Drive</a>, not in this form.</p>"
      );
    }
    return (
      "<p><strong>Cómo cargar un CVar (y otros archivos)</strong></p>" +
      "<ol>" +
      "<li>Entrá al sistema → <strong>Carga de Archivos</strong> (no hay uploader dentro de Streamlit).</li>" +
      "<li>Abrí la carpeta de Drive que corresponda: <strong>CVar 2026</strong> o el Orden del Día / Acta de la reunión.</li>" +
      "<li>En Drive: carpeta de tu Unidad Académica → <strong>Nuevo</strong> → <strong>Subir archivo</strong>.</li>" +
      "<li>Verificá que el archivo quedó dentro de esa carpeta.</li>" +
      "</ol>" +
      "<p>En el formulario de temas no hay campo “CV/adjunto”. Las actas firmadas están en el <a href=\"" +
      ACTAS_DRIVE +
      "\" target=\"_blank\" rel=\"noopener noreferrer\">Drive de actas</a>, no en este formulario.</p>"
    );
  }

  function htmlActa() {
    if (lang() === "en") {
      return (
        "<p>On <strong>Actas</strong>, tap a card (or <em>Elegir</em>). Closed meetings say “Cerrada”; the current one “En curso”; later ones “Próxima”. There is also a <strong>CVar 2026</strong> card.</p>" +
        "<p>Until a meeting is selected, <em>Ver temas</em>, <em>Cargar tema</em>, <em>Descargar OD</em> and <em>Cargar archivo</em> stay disabled. If unsure, ask for the minutes number before sending.</p>"
      );
    }
    return (
      "<p>En <strong>Actas</strong>: tocá una tarjeta (o <em>Elegir</em>). Las cerradas dicen “Cerrada”; la en curso “En curso”; las siguientes “Próxima”. También está la tarjeta <strong>CVar 2026</strong>.</p>" +
      "<p>Hasta elegir un acta, quedan deshabilitadas: Ver temas, Cargar tema, Descargar OD, Cargar archivo. Si no estás seguro de cuál usar, pedí el número de acta antes de enviar.</p>"
    );
  }

  function htmlDescargar() {
    if (lang() === "en") {
      return (
        "<p>On <strong>Descargar Orden del Dia</strong>: choose the agenda (e.g. “194 - Septiembre”), check how many topics it has, then <em>Generar Orden del Día</em> and <em>Descargar Orden del Día</em> (Word).</p>" +
        "<p>Reordering with ↑/↓ does not change the Google Sheet; it only affects the generated Word file.</p>"
      );
    }
    return (
      "<p>En <strong>Descargar Orden del Dia</strong>: seleccioná el OD (ej. “194 - Septiembre”), revisá cuántos temas tiene, <em>Generar Orden del Día</em> y después <em>Descargar Orden del Día</em> (Word).</p>" +
      "<p>Reordenar con ↑/↓ no cambia la planilla de Google Sheets: solo afecta el Word generado.</p>"
    );
  }

  function htmlLogin() {
    if (lang() === "en") {
      return "<p>The topic system does not ask for a username or password. If a Google sign-in appears, it is Drive, not the form.</p>";
    }
    return "<p>El sistema de temas no pide usuario ni contraseña. Si aparece un inicio de sesión de Google, es Drive, no el formulario.</p>";
  }

  function htmlNormativa() {
    if (lang() === "en") {
      return (
        "<p>Project, progress and final-report instructions are on the portal under <a href=\"#ordenanza-general\">Ordinance</a>.</p>"
      );
    }
    return (
      "<p>Instructivos de proyectos, avances y finales: portal → <a href=\"#ordenanza-general\">Ordenanza</a> (anexos e instructivos).</p>"
    );
  }

  function htmlFallback() {
    if (lang() === "en") {
      return (
        "<p>I can walk you through loading a topic or a CVar. If it is not in the portal or the system, write to <a href=\"mailto:" +
        MAIL +
        "\">" +
        MAIL +
        "</a>. This help desk does not change data, send email, or approve topics.</p>"
      );
    }
    return (
      "<p>Puedo guiarte para <strong>cargar un tema</strong> o <strong>cargar un CVar</strong>. Si no está en el portal o el sistema, escribí a <a href=\"mailto:" +
      MAIL +
      "\">" +
      MAIL +
      "</a>. Esta mesa no cambia datos, no envía mails ni aprueba temas.</p>"
    );
  }

  function htmlGreeting() {
    if (lang() === "en") {
      return "<p>I help Research Council members. The two most frequent questions are <strong>how to load a topic</strong> and <strong>how to upload a CVar</strong>.</p>";
    }
    return (
      "<p>Soy la mesa de ayuda para consejeros. Las dos consultas más frecuentes: <strong>cómo cargar un tema</strong> y <strong>cómo cargar un CVar</strong>.</p>"
    );
  }

  function renderFor(id) {
    if (id === "cargar-tema") return htmlTema();
    if (id === "cargar-cvar") return htmlCvar();
    if (id === "acta") return htmlActa();
    if (id === "descargar") return htmlDescargar();
    if (id === "login") return htmlLogin();
    if (id === "normativa") return htmlNormativa();
    return htmlFallback();
  }

  function matchId(query) {
    var q = normalize(query);
    if (!q) return null;
    var best = null;
    var bestScore = 0;
    Object.keys(ANSWERS).forEach(function (id) {
      var entry = ANSWERS[id];
      var score = 0;
      entry.keywords.forEach(function (kw) {
        if (q.indexOf(normalize(kw)) !== -1) score += 4;
      });
      (entry.extra || []).forEach(function (kw) {
        if (q.indexOf(normalize(kw)) !== -1) score += 1;
      });
      if (score > bestScore) {
        bestScore = score;
        best = id;
      }
    });
    if (best === "cargar-cvar" && bestScore >= 1) return "cargar-cvar";
    if (best === "cargar-tema" && bestScore >= 1) return "cargar-tema";
    if (!best || bestScore < 2) return null;
    return best;
  }

  function appendMessage(log, role, htmlOrText, asHtml) {
    var div = document.createElement("div");
    div.className = "consejero-bot-msg consejero-bot-msg--" + role;
    if (asHtml) div.innerHTML = htmlOrText;
    else div.textContent = htmlOrText;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
  }

  function init() {
    var panel = document.getElementById("consejero-bot-panel");
    var toggle = document.getElementById("consejero-bot-toggle");
    var closeBtn = document.getElementById("consejero-bot-close");
    var log = document.getElementById("consejero-bot-log");
    var form = document.getElementById("consejero-bot-form");
    var input = document.getElementById("consejero-bot-input");
    var quick = document.getElementById("consejero-bot-quick");
    if (!panel || !toggle || !log || !form || !input) return;

    var greeted = false;

    function greet() {
      if (greeted) return;
      greeted = true;
      appendMessage(log, "bot", htmlGreeting(), true);
    }

    function setOpen(open) {
      if (open) {
        panel.removeAttribute("hidden");
        toggle.setAttribute("aria-expanded", "true");
        document.body.classList.add("consejero-bot-open");
        greet();
        window.setTimeout(function () {
          input.focus();
        }, 50);
      } else {
        panel.setAttribute("hidden", "");
        toggle.setAttribute("aria-expanded", "false");
        document.body.classList.remove("consejero-bot-open");
      }
    }

    function paintQuick() {
      quick.innerHTML =
        '<button type="button" data-consejero-q="cargar-tema">' +
        t("bot.q.tema", "Cómo cargar un tema") +
        "</button>" +
        '<button type="button" data-consejero-q="cargar-cvar">' +
        t("bot.q.cvar", "Cómo cargar un CVar") +
        "</button>";
    }

    function ask(text, idHint) {
      var q = String(text || "").trim();
      var id = idHint || matchId(q);
      if (!q && !id) return;
      var label = q;
      if (!label) {
        label = id === "cargar-cvar" ? t("bot.q.cvar", "Cómo cargar un CVar") : t("bot.q.tema", "Cómo cargar un tema");
      }
      setOpen(true);
      appendMessage(log, "user", label, false);
      var html = renderFor(id);
      window.setTimeout(function () {
        appendMessage(log, "bot", html, true);
      }, 180);
    }

    paintQuick();
    greet();

    toggle.addEventListener("click", function () {
      setOpen(panel.hasAttribute("hidden"));
    });
    if (closeBtn) {
      closeBtn.addEventListener("click", function () {
        setOpen(false);
      });
    }

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var q = input.value;
      input.value = "";
      ask(q);
    });

    document.addEventListener("click", function (ev) {
      var btn = ev.target.closest("[data-consejero-q]");
      if (!btn) return;
      ev.preventDefault();
      ask("", btn.getAttribute("data-consejero-q"));
    });

    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && !panel.hasAttribute("hidden")) setOpen(false);
    });

    window.addEventListener("oia:langchange", function () {
      paintQuick();
      if (window.I18N && window.I18N.apply) {
        /* labels already on DOM via data-i18n */
      }
    });

    if (location.hash === "#bot-consejeros") {
      setOpen(true);
    }

    window.ConsejeroBot = {
      ask: ask,
      open: function () {
        setOpen(true);
      }
    };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
