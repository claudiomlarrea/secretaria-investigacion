(function () {
  var CFG = window.SEC_PUBLICACIONES || {};

  function el(id) {
    return document.getElementById(id);
  }

  function esc(s) {
    var d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  function proyectosUrl() {
    var base = CFG.APPS_SCRIPT_URL && String(CFG.APPS_SCRIPT_URL).trim();
    if (!base) return "";
    var sep = base.indexOf("?") >= 0 ? "&" : "?";
    return base + sep + "action=proyectos";
  }

  function fetchJson(url) {
    return fetch(url, { method: "GET" }).then(function (r) {
      if (!r.ok) throw new Error("network");
      return r.json();
    });
  }

  function fetchJsonp(url) {
    return new Promise(function (resolve, reject) {
      var name = "_secProyCb_" + Math.floor(Math.random() * 1e9);
      var done = false;
      var qs = url.indexOf("?") >= 0 ? "&" : "?";
      var script = document.createElement("script");
      window[name] = function (data) {
        if (done) return;
        done = true;
        delete window[name];
        if (script.parentNode) script.parentNode.removeChild(script);
        resolve(data);
      };
      script.async = true;
      script.src = url + qs + "callback=" + encodeURIComponent(name);
      script.onerror = function () {
        if (done) return;
        done = true;
        delete window[name];
        if (script.parentNode) script.parentNode.removeChild(script);
        reject(new Error("jsonp"));
      };
      document.body.appendChild(script);
      window.setTimeout(function () {
        if (done) return;
        script.onerror();
      }, 20000);
    });
  }

  var items = [];
  var filtroUnidad = "all";
  var filtroAnio = "all";

  function unidadesUnicas(list) {
    var set = {};
    list.forEach(function (it) {
      var u = String((it && it.unidad) || "").trim();
      if (u) set[u] = true;
    });
    return Object.keys(set).sort(function (a, b) {
      return a.localeCompare(b, "es");
    });
  }

  function aniosUnicos(list) {
    var set = {};
    list.forEach(function (it) {
      var y = String((it && it.anio) || "").trim();
      if (y) set[y] = true;
    });
    return Object.keys(set).sort(function (a, b) {
      var na = parseInt(a, 10);
      var nb = parseInt(b, 10);
      if (!isNaN(na) && !isNaN(nb)) return nb - na;
      return b.localeCompare(a, "es");
    });
  }

  function aplicarFiltros(list) {
    return list.filter(function (it) {
      if (filtroUnidad !== "all" && String(it.unidad || "") !== filtroUnidad) return false;
      if (filtroAnio !== "all" && String(it.anio || "") !== filtroAnio) return false;
      return true;
    });
  }

  function dibujarFiltros() {
    var root = el("proy-filters");
    if (!root) return;

    var unidades = unidadesUnicas(items);
    var anios = aniosUnicos(items);

    var html =
      '<label class="proy-filter-label" for="proy-filter-unidad">Unidad</label>' +
      '<select id="proy-filter-unidad" class="proy-filter-select" aria-label="Filtrar por unidad académica">' +
      '<option value="all">Todas las unidades</option>';
    unidades.forEach(function (u) {
      html +=
        '<option value="' +
        esc(u) +
        '"' +
        (filtroUnidad === u ? " selected" : "") +
        ">" +
        esc(u) +
        "</option>";
    });
    html += "</select>";

    html +=
      '<label class="proy-filter-label" for="proy-filter-anio">Año</label>' +
      '<select id="proy-filter-anio" class="proy-filter-select" aria-label="Filtrar por año">' +
      '<option value="all">Todos los años</option>';
    anios.forEach(function (y) {
      html +=
        '<option value="' +
        esc(y) +
        '"' +
        (filtroAnio === y ? " selected" : "") +
        ">" +
        esc(y) +
        "</option>";
    });
    html += "</select>";

    root.innerHTML = html;

    var selU = el("proy-filter-unidad");
    var selA = el("proy-filter-anio");
    if (selU) {
      selU.addEventListener("change", function () {
        filtroUnidad = selU.value;
        dibujarGrilla();
      });
    }
    if (selA) {
      selA.addEventListener("change", function () {
        filtroAnio = selA.value;
        dibujarGrilla();
      });
    }
  }

  function metaLinea(it) {
    var partes = [];
    if (it.director) partes.push("Director/a: " + it.director);
    if (it.instituto) partes.push(it.instituto);
    if (it.catedra) partes.push(it.catedra);
    return partes.join(" · ");
  }

  function tarjetaHTML(it) {
    var meta = metaLinea(it);
    var html =
      '<article class="proyecto-card">' +
      '<p class="proyecto-card-meta">' +
      '<span class="proyecto-card-year">' +
      esc(it.anio || "—") +
      "</span>";
    if (it.tipo) {
      html += '<span class="proyecto-card-tipo">' + esc(it.tipo) + "</span>";
    }
    html += "</p>";
    if (it.unidad) {
      html +=
        '<p class="proyecto-card-unidad" title="' +
        esc(it.unidad) +
        '">' +
        esc(it.unidad) +
        "</p>";
    }
    html += "<h3>" + esc(it.titulo) + "</h3>";
    if (it.descripcion) {
      html += '<p class="proyecto-card-desc">' + esc(it.descripcion) + "</p>";
    }
    if (meta) {
      html += '<p class="proyecto-card-director">' + esc(meta) + "</p>";
    }
    if (it.equipo) {
      html +=
        '<p class="proyecto-card-equipo"><span>Equipo:</span> ' + esc(it.equipo) + "</p>";
    }
    html += "</article>";
    return html;
  }

  function dibujarGrilla() {
    var grid = el("proy-grid");
    var count = el("proy-count");
    if (!grid) return;

    var visibles = aplicarFiltros(items);
    if (count) {
      count.textContent =
        visibles.length === 1
          ? "1 investigación destacada"
          : visibles.length + " investigaciones destacadas";
    }

    if (!visibles.length) {
      grid.innerHTML =
        '<p class="proy-empty">No hay proyectos que coincidan con los filtros seleccionados.</p>';
      return;
    }

    grid.innerHTML = '<div class="proyectos-grid">' + visibles.map(tarjetaHTML).join("") + "</div>";
  }

  function renderTodo() {
    el("proy-status").innerHTML = "";
    var wrap = el("proy-content");
    if (wrap) wrap.hidden = false;
    dibujarFiltros();
    dibujarGrilla();
  }

  function cargar() {
    var status = el("proy-status");
    var url = proyectosUrl();

    if (!url) {
      status.innerHTML =
        '<div class="pub-msg pub-msg--hint">Las investigaciones destacadas se mostrarán cuando conectés la aplicación web. ' +
        "Pasos en <strong>INSTRUCCIONES-PROYECTOS.txt</strong>.</div>";
      return;
    }

    status.innerHTML = '<div class="pub-msg pub-msg--loading">Cargando investigaciones…</div>';

    var urlLive = url + (url.indexOf("?") >= 0 ? "&" : "?") + "_=" + Date.now();

    function onData(data) {
      if (!data || !data.ok || !Array.isArray(data.items)) throw new Error("format");
      items = data.items;
      if (!items.length) {
        status.innerHTML =
          '<div class="pub-msg pub-msg--hint">Aún no hay investigaciones marcadas para el sitio. ' +
          "En la planilla <em>Datos Consejo Investigación</em> · Hoja 2, completá la columna " +
          "<strong>destacar_web</strong> con <em>sí</em> en los proyectos que quieras mostrar.</div>";
        return;
      }
      renderTodo();
    }

    fetchJson(urlLive).then(onData, function () {
      return fetchJsonp(urlLive).then(onData, function () {
        status.innerHTML =
          '<div class="pub-msg pub-msg--error">No se pudo cargar las investigaciones destacadas. ' +
          "Si acabás de actualizar Apps Script, publicá una nueva versión y recargá (<kbd>⌘⇧R</kbd>).</div>";
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", cargar);
  } else {
    cargar();
  }
})();
