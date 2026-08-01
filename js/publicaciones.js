(function () {
  var CFG = window.SEC_PUBLICACIONES || {};

  function el(id) {
    return document.getElementById(id);
  }

  function adminUrl() {
    if (CFG.ADMIN_URL && String(CFG.ADMIN_URL).trim()) return String(CFG.ADMIN_URL).trim();
    if (!CFG.APPS_SCRIPT_URL || !String(CFG.APPS_SCRIPT_URL).trim()) return "";
    var base = String(CFG.APPS_SCRIPT_URL).trim();
    return base + (base.indexOf("?") >= 0 ? "&" : "?") + "action=admin";
  }

  function dibujarIngresoEquipo() {
    var root = el("pub-team-entry");
    if (!root) return;
    var url = adminUrl();
    if (!url) {
      root.innerHTML = "";
      return;
    }
    root.innerHTML =
      "<p class=\"pub-intro\" style=\"margin-top:0\">" +
      "<a class=\"btn btn-ghost\" href=\"" +
      esc(url) +
      "\" target=\"_blank\" rel=\"noopener noreferrer\">" +
      (window.I18N && window.I18N.t
        ? window.I18N.t("dyn.pub.teamEntry")
        : "Ingreso equipo · Cargar publicaciones") +
      "</a> " +
      "<small>" +
      (window.I18N && window.I18N.t
        ? window.I18N.t("dyn.pub.teamHint")
        : "(iniciá sesión en Google con un correo autorizado)") +
      "</small></p>";
  }

  function esc(s) {
    var d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  var filtrosDef = [
    { id: "todas", label: "Ver todas", icono: "✨" },
    { id: "revistas", label: "Revistas", icono: "📑" },
    { id: "libros", label: "Libros y capítulos", icono: "📚" },
    { id: "repositorios", label: "Informes", icono: "🗂️" },
    { id: "eventos", label: "Reuniones / eventos", icono: "🎓" },
    { id: "diarios", label: "Medios / diarios", icono: "📰" }
  ];

  var items = [];
  var filtroActivo = "todas";
  var PAGE_SIZE = 10;
  var visibleLimit = PAGE_SIZE;

  function fetchJson(url) {
    return fetch(url, { method: "GET" }).then(function (r) {
      if (!r.ok) throw new Error("network");
      return r.json();
    });
  }

  function fetchJsonp(url) {
    return new Promise(function (resolve, reject) {
      var name = "_secPubCb_" + Math.floor(Math.random() * 1e9);
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

  function cargar() {
    var status = el("pub-status");
    var url = CFG.APPS_SCRIPT_URL && CFG.APPS_SCRIPT_URL.trim();
    dibujarIngresoEquipo();

    if (!url) {
      status.innerHTML =
        "<div class=\"pub-msg pub-msg--hint\">Las publicaciones se mostrarán aquí cuando conectés la aplicación web (Google Apps Script). " +
        "Pasos en el archivo <strong>INSTRUCCIONES-PUBLICACIONES.txt</strong>.</div>";
      return;
    }

    status.innerHTML = "<div class=\"pub-msg pub-msg--loading\">Cargando publicaciones…</div>";

    var urlLive = url + (url.indexOf("?") >= 0 ? "&" : "?") + "_=" + Date.now();
    fetchJson(urlLive).then(
      function (data) {
        if (!data || !data.ok || !Array.isArray(data.items)) throw new Error("format");
        items = data.items;
        var cw = el("pub-count-wrap");
        if (cw) cw.hidden = false;
        renderTodo();
      },
      function () {
        return fetchJsonp(urlLive).then(
          function (data) {
            if (!data || !data.ok || !Array.isArray(data.items)) throw new Error("format");
            items = data.items;
            var cw2 = el("pub-count-wrap");
            if (cw2) cw2.hidden = false;
            renderTodo();
          },
          function () {
            status.innerHTML =
              "<div class=\"pub-msg pub-msg--error\">No se pudo conectar al servicio de publicaciones. Revisá la URL en " +
              "<code>publicaciones-config.js</code> y volvé a cargar esta página (<kbd>⌘⇧R</kbd>).</div>";
          }
        );
      }
    );
  }

  function renderTodo() {
    el("pub-status").innerHTML = "";
    dibujarFiltros();
    dibujarGrilla();
  }

  function dibujarFiltros() {
    var root = el("pub-filters");
    if (!root) return;
    root.innerHTML = filtrosDef
      .map(function (f) {
        var sel = filtroActivo === f.id ? " pub-filter--active" : "";
        return (
          "<button type=\"button\" class=\"pub-filter" +
          sel +
          "\" data-filtro=\"" +
          esc(f.id) +
          "\" aria-pressed=\"" +
          (filtroActivo === f.id) +
          "\">" +
          "<span class=\"pub-filter-icon\" aria-hidden=\"true\">" +
          esc(f.icono) +
          "</span> " +
          esc(f.label) +
          "</button>"
        );
      })
      .join("");

    root.querySelectorAll(".pub-filter").forEach(function (btn) {
      btn.addEventListener("click", function () {
        filtroActivo = btn.getAttribute("data-filtro");
        visibleLimit = PAGE_SIZE;
        dibujarFiltros();
        dibujarGrilla();
      });
    });
  }

  function aplicarFiltro(list) {
    if (filtroActivo === "todas") return list;
    return list.filter(function (it) {
      return categoriaItem(it) === filtroActivo;
    });
  }

  function categoriaItem(it) {
    var c = String((it && it.categoria) || "").toLowerCase().trim();
    if (c) return c;

    var t = String((it && it.tipo_origen) || "").toLowerCase().trim();
    var tp = String((it && it.tipo_publicacion) || "").toLowerCase().trim();

    if (t === "revista") return "revistas";
    if (t === "repositorio") return "repositorios";
    if (t === "evento") return "eventos";
    if (t === "diario") return "diarios";
    if (t === "libro" || t.indexOf("capitulo") >= 0 || t.indexOf("capítulo") >= 0) return "libros";
    if (tp.indexOf("libro") >= 0 || tp.indexOf("capitulo") >= 0 || tp.indexOf("capítulo") >= 0) return "libros";
    if (it && it.repositorio) return "repositorios";
    if (it && it.evento) return "eventos";
    if (it && it.revista_o_medio && !(it && it.doi)) return "diarios";
    return "otros";
  }

  function safeCatClass(c) {
    return String(c || "otros").replace(/[^a-z0-9_-]/gi, "");
  }

  function textoChip(categoria) {
    var m = {
      revistas: "Revista",
      libros: "Libro / capítulo",
      repositorios: "Repositorio",
      eventos: "Evento científico",
      diarios: "Medios",
      otros: "Publicación"
    };
    return m[categoria] || m.otros;
  }

  function doiToUrl(d) {
    var x = String(d).trim();
    if (!x) return "";
    if (/^https?:\/\//i.test(x)) return x;
    return "https://doi.org/" + x.replace(/^doi:\s*/i, "");
  }

  function safeHref(url) {
    var u = String(url || "").trim();
    if (!u) return "#";
    if (/^https?:\/\//i.test(u)) return u;
    if (/^doi:/i.test(u)) return doiToUrl(u);
    if (/^10\.\d+/i.test(u)) return doiToUrl(u);
    return "#";
  }

  function metaLinea(it, categoria) {
    var partes = [];
    if (it.autores) partes.push(it.autores);
    if (it.revista_o_medio) partes.push(it.revista_o_medio);
    if (it.evento && categoria === "eventos") partes.push(it.evento);
    if (it.lugar) partes.push(it.lugar);
    if (it.editorial) partes.push(it.editorial);
    return partes.join(" · ");
  }

  function enlaceItem(it) {
    var href = "";
    if (it.link) href = safeHref(it.link);
    else if (it.doi) href = doiToUrl(it.doi);
    var label = /doi\.org/i.test(href) ? "Ver DOI" : "Abrir enlace";
    return { href: href, label: label };
  }

  function etiquetaUnidad(it) {
    return String((it && it.unidad) || "").trim();
  }

  function celdaUnidadAnioHTML(it) {
    var unidad = etiquetaUnidad(it);
    var tiempo = (it && (it.fecha || it.anio)) || "";
    var html = '<div class="pub-row-when" aria-label="Unidad académica y año o fecha">';
    if (unidad) {
      html +=
        '<span class="pub-row-unidad" title="' +
        esc(unidad) +
        '">' +
        esc(unidad) +
        "</span>";
    }
    html += '<span class="pub-row-year">' + esc(tiempo || "—") + "</span></div>";
    return html;
  }

  function filaCompactaHTML(it) {
    var categoria = categoriaItem(it);
    var chip =
      '<span class="pub-chip pub-chip--' +
      safeCatClass(categoria) +
      '">' +
      esc(textoChip(categoria)) +
      "</span>";
    var meta = metaLinea(it, categoria);
    var link = enlaceItem(it);
    var linkHtml =
      link.href && link.href !== "#"
        ? '<a class="pub-btn-link" href="' +
          esc(link.href) +
          '" target="_blank" rel="noopener noreferrer">' +
          esc(link.label) +
          "</a>"
        : '<span class="pub-row-nolink">Sin enlace</span>';

    return (
      '<article class="pub-row pub-row--' +
      safeCatClass(categoria) +
      '">' +
      '<div class="pub-row-type">' +
      chip +
      "</div>" +
      '<div class="pub-row-main">' +
      '<h3 class="pub-row-title">' +
      esc(it.titulo || "Sin título") +
      "</h3>" +
      (meta ? '<p class="pub-row-meta">' + esc(meta) + "</p>" : "") +
      "</div>" +
      celdaUnidadAnioHTML(it) +
      '<div class="pub-row-link">' +
      linkHtml +
      "</div>" +
      "</article>"
    );
  }

  function dibujarGrilla() {
    var grid = el("pub-grid");
    if (!grid) return;
    var list = aplicarFiltro(items);
    el("pub-count").textContent = String(list.length);

    if (!list.length) {
      var filtro = filtrosDef.filter(function (f) {
        return f.id === filtroActivo;
      })[0];
      var tituloFiltro = filtro ? filtro.label : "esta sección";
      var cuerpo;
      if (!items.length) {
        cuerpo =
          "<p><strong>Próximamente</strong></p>" +
          "<p>Estamos incorporando las publicaciones de la Secretaría de Investigación.</p>";
      } else if (filtroActivo === "todas") {
        cuerpo =
          "<p>No hay publicaciones para mostrar en este momento.</p>" +
          "<p>Volvé a consultar pronto.</p>";
      } else {
        cuerpo =
          "<p>Todavía no hay publicaciones en <strong>" +
          esc(tituloFiltro) +
          "</strong>.</p>" +
          "<p>Podés ver lo disponible en <strong>Ver todas</strong>.</p>";
      }
      grid.innerHTML = "<div class=\"pub-msg pub-msg--hint\">" + cuerpo + "</div>";
      return;
    }

    var shown = list.slice(0, visibleLimit);
    var restantes = list.length - shown.length;

    var html =
      '<div class="pub-list" role="list">' +
      '<div class="pub-list-head" aria-hidden="true">' +
      "<span>Tipo</span><span>Título</span><span>Unidad · Año</span><span>Enlace</span>" +
      "</div>" +
      shown.map(filaCompactaHTML).join("") +
      "</div>";

    if (restantes > 0) {
      html +=
        '<div class="pub-more-wrap">' +
        '<button type="button" class="pub-more-btn" data-pub-more="1">Ver más (' +
        restantes +
        ")</button>" +
        "</div>";
    }

    grid.innerHTML = html;

    var moreBtn = grid.querySelector("[data-pub-more]");
    if (moreBtn) {
      moreBtn.addEventListener("click", function () {
        visibleLimit += PAGE_SIZE;
        dibujarGrilla();
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", cargar);
  } else {
    cargar();
  }
})();
