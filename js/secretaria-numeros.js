/**
 * Renderiza “La Secretaría en números” y permite actualizar visitas/publicaciones.
 */
(function () {
  var CFG = window.SEC_NUMEROS || { items: [] };
  var root = document.getElementById("numeros-grid");
  if (!root) return;

  function tt(key, fallback) {
    if (window.I18N && typeof window.I18N.t === "function") {
      var v = window.I18N.t(key);
      if (v && v !== key) return v;
    }
    return fallback;
  }

  function lang() {
    if (window.I18N && typeof window.I18N.getLang === "function") {
      return window.I18N.getLang();
    }
    return document.documentElement.lang || "es";
  }

  function labelFor(item) {
    var en = String(lang()).toLowerCase().indexOf("en") === 0;
    return en ? item.labelEn || item.labelEs : item.labelEs;
  }

  function fmt(n) {
    if (n == null || n === "" || isNaN(Number(n))) return "—";
    try {
      return Number(n).toLocaleString(lang().indexOf("en") === 0 ? "en-US" : "es-AR");
    } catch (e) {
      return String(n);
    }
  }

  function countSelector(sel, fallback) {
    var n = document.querySelectorAll(sel).length;
    return n > 0 ? n : fallback;
  }

  var state = {};
  (CFG.items || []).forEach(function (it) {
    if (it.fromEquipo) state[it.id] = countSelector("[data-page='equipo'] .team-card", it.value);
    else if (it.fromHerramientas) state[it.id] = countSelector("#herramientas .tool-card", it.value);
    else state[it.id] = it.value;
  });

  function draw() {
    var html = "";
    (CFG.items || []).forEach(function (it) {
      var val = state[it.id];
      var shown = fmt(val);
      var big = shown.replace(/\D/g, "").length >= 7;
      var inner =
        '<span class="numeros-value' +
        (big ? " numeros-value--lg" : "") +
        '">' +
        shown +
        '</span><span class="numeros-label">' +
        labelFor(it) +
        "</span>";
      if (it.href) {
        html +=
          '<a class="numeros-card" href="' +
          it.href +
          '">' +
          inner +
          "</a>";
      } else {
        html += '<div class="numeros-card">' + inner + "</div>";
      }
    });
    root.innerHTML = html;
  }

  window.OBS_NUMEROS_API = {
    set: function (id, value) {
      if (!id) return;
      state[id] = value;
      draw();
    },
    refresh: draw
  };

  draw();

  var editorial = document.getElementById("numeros-editorial");
  if (editorial) {
    editorial.textContent = tt(
      "sec.numeros.editorial",
      lang().indexOf("en") === 0 ? CFG.editorialEn : CFG.editorialEs
    );
  }

  document.addEventListener("oia:langchange", function () {
    draw();
    if (editorial) {
      editorial.textContent = tt(
        "sec.numeros.editorial",
        lang().indexOf("en") === 0 ? CFG.editorialEn : CFG.editorialEs
      );
    }
  });
})();
