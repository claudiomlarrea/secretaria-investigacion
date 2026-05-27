(function () {
  var CFG = window.SEC_PUBLICACIONES || {};
  var INSTITUTION_ID = String(CFG.OPENALEX_INSTITUTION_ID || "I4210121591").trim();
  var MAILTO = String(CFG.OPENALEX_MAILTO || "investigacion@uccuyo.edu.ar").trim();
  var PAGE_SIZE = Number(CFG.OPENALEX_PAGE_SIZE) || 15;
  var SEARCH_DEBOUNCE_MS = 450;

  var items = [];
  var metaTotal = 0;
  var currentPage = 1;
  var totalPages = 1;
  var loaded = false;
  var loading = false;
  var searchQuery = "";
  var searchMode = "auto";
  var searchDebounce = null;

  var ETIQUETA_MODO = {
    auto: "coincidencias",
    title: "título",
    author: "autor/a",
    doi: "DOI"
  };

  function el(id) {
    return document.getElementById(id);
  }

  function esc(s) {
    var d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  function openAlexHeaders() {
    return {
      Accept: "application/json",
      "User-Agent": "mailto:" + MAILTO + " (Secretaría de Investigación UCCuyo)"
    };
  }

  function autoresDeWork(work) {
    var list = (work && work.authorships) || [];
    return list
      .map(function (a) {
        return a && a.author && a.author.display_name;
      })
      .filter(Boolean)
      .join(", ");
  }

  function doiDeWork(work) {
    var raw = work && work.doi;
    if (!raw) return "";
    return String(raw).replace(/^https?:\/\/doi\.org\//i, "").trim();
  }

  function enlaceDeWork(work) {
    var doi = doiDeWork(work);
    if (doi) return "https://doi.org/" + doi;
    var loc = work && work.primary_location;
    if (loc && loc.landing_page_url) return loc.landing_page_url;
    if (loc && loc.pdf_url) return loc.pdf_url;
    if (work && work.id) return work.id;
    return "";
  }

  function tipoDeWork(work) {
    var t = work && work.type;
    if (!t) return "Trabajo académico";
    var map = {
      article: "Artículo",
      "book-chapter": "Capítulo",
      book: "Libro",
      dissertation: "Tesis",
      dataset: "Dataset",
      review: "Revisión",
      preprint: "Preprint",
      report: "Informe",
      proceedings: "Actas"
    };
    return map[t] || t.replace(/-/g, " ");
  }

  function fetchOpenAlex(url) {
    return fetch(url, { method: "GET", headers: openAlexHeaders() }).then(function (r) {
      if (!r.ok) throw new Error("network");
      return r.json();
    });
  }

  function normalizarDoi(q) {
    var s = String(q || "").trim();
    s = s.replace(/^https?:\/\/(?:dx\.)?doi\.org\//i, "");
    s = s.replace(/^doi:\s*/i, "");
    return s.trim();
  }

  function pareceDoi(q) {
    var d = normalizarDoi(q);
    return /^10\.\d{3,}/i.test(d);
  }

  function palabrasDe(q) {
    return String(q || "")
      .trim()
      .split(/\s+/)
      .filter(Boolean);
  }

  function pareceAutor(q) {
    var s = String(q || "").trim();
    if (!s) return false;
    if (s.indexOf(",") >= 0) return true;

    var partes = palabrasDe(s);
    if (partes.length === 1) {
      return partes[0].length >= 3 && /^[\p{L}]/u.test(partes[0]);
    }
    if (partes.length < 2 || partes.length > 6) return false;

    var mayusculas = partes.filter(function (w) {
      return /^[\p{Lu}]/u.test(w);
    }).length;
    if (mayusculas >= 2) return true;
    if (partes.length === 2 && mayusculas >= 1) return true;
    return false;
  }

  function modoBusquedaEfectivo(q) {
    var modo = searchMode;
    if (modo === "auto") {
      if (pareceDoi(q)) return "doi";
      if (pareceAutor(q)) return "author";
      return "title";
    }
    return modo;
  }

  function textoAutorBusqueda(q) {
    return String(q || "")
      .trim()
      .replace(/\s*,\s*/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function filtroOpenAlex() {
    var parts = ["authorships.institutions.lineage:" + INSTITUTION_ID];
    var q = searchQuery.trim();
    if (!q) return parts.join(",");

    var modo = modoBusquedaEfectivo(q);
    if (modo === "doi") {
      var doi = normalizarDoi(q);
      if (/^10\.\d{4,}.+\/.+/i.test(doi)) {
        parts.push("doi:" + doi);
      } else {
        parts.push("doi_starts_with:" + doi);
      }
    } else if (modo === "author") {
      parts.push("raw_author_name.search:" + textoAutorBusqueda(q));
    } else {
      parts.push("display_name.search:" + q);
    }
    return parts.join(",");
  }

  function etiquetaModoActual() {
    var q = searchQuery.trim();
    if (!q) return "";
    return ETIQUETA_MODO[modoBusquedaEfectivo(q)] || "coincidencias";
  }

  function urlWorks(page) {
    var params = new URLSearchParams();
    params.set("filter", filtroOpenAlex());
    params.set("sort", "publication_date:desc");
    params.set("per-page", String(PAGE_SIZE));
    params.set("page", String(page));
    return "https://api.openalex.org/works?" + params.toString();
  }

  function actualizarContador() {
    var wrap = el("pub-index-count-wrap");
    var totalEl = el("pub-index-total");
    if (!wrap || !totalEl) return;
    wrap.hidden = false;
    totalEl.textContent = String(metaTotal);
  }

  function mensajeCarga() {
    if (searchQuery.trim()) {
      return (
        '<div class="pub-msg pub-msg--loading">Buscando por ' +
        esc(etiquetaModoActual()) +
        ": «" +
        esc(searchQuery.trim()) +
        "»…</div>"
      );
    }
    return '<div class="pub-msg pub-msg--loading">Cargando publicaciones indexadas…</div>';
  }

  function cargarPagina(page, query) {
    if (typeof query === "string") searchQuery = query;
    if (loading) return;

    loading = true;
    currentPage = page;
    var status = el("pub-index-status");
    if (status) status.innerHTML = mensajeCarga();

    fetchOpenAlex(urlWorks(page))
      .then(function (data) {
        loading = false;
        if (!data || !Array.isArray(data.results)) throw new Error("format");

        metaTotal = Number(data.meta && data.meta.count) || 0;
        currentPage = Number(data.meta && data.meta.page) || page;
        totalPages = Math.max(1, Math.ceil(metaTotal / PAGE_SIZE));

        items = data.results.map(function (w) {
          return {
            titulo: w.display_name || "Sin título",
            autores: autoresDeWork(w),
            doi: doiDeWork(w),
            link: enlaceDeWork(w),
            anio: w.publication_year || "",
            tipo: tipoDeWork(w)
          };
        });

        loaded = true;
        actualizarContador();
        actualizarBotonLimpiar();

        if (status) status.innerHTML = "";
        dibujarGrilla();
      })
      .catch(function () {
        loading = false;
        if (status) {
          status.innerHTML =
            '<div class="pub-msg pub-msg--error">No se pudo cargar el índice de OpenAlex. ' +
            "Comprobá tu conexión o probá de nuevo en unos minutos.</div>";
        }
      });
  }

  function actualizarBotonLimpiar() {
    var clearBtn = el("pub-index-q-clear");
    var input = el("pub-index-q");
    if (!clearBtn) return;
    var tieneTexto = (input && input.value.trim()) || searchQuery.trim();
    clearBtn.hidden = !tieneTexto;
  }

  function filaHTML(it) {
    var link = it.link || (it.doi ? "https://doi.org/" + it.doi : "");
    var linkLabel = it.doi ? "Ver DOI" : "Abrir enlace";
    var linkHtml = link
      ? '<a class="pub-btn-link" href="' +
        esc(link) +
        '" target="_blank" rel="noopener noreferrer">' +
        esc(linkLabel) +
        "</a>"
      : '<span class="pub-row-nolink">Sin enlace</span>';

    var meta = it.autores || "";
    if (it.doi) meta += (meta ? " · " : "") + "DOI: " + it.doi;

    return (
      '<article class="pub-row pub-row--revistas">' +
      '<div class="pub-row-type">' +
      '<span class="pub-chip pub-chip--revistas">' +
      esc(it.tipo) +
      "</span>" +
      "</div>" +
      '<div class="pub-row-main">' +
      '<h3 class="pub-row-title">' +
      esc(it.titulo) +
      "</h3>" +
      (meta ? '<p class="pub-row-meta">' + esc(meta) + "</p>" : "") +
      "</div>" +
      '<div class="pub-row-when" aria-label="Año de publicación">' +
      '<span class="pub-row-year">' +
      esc(it.anio || "—") +
      "</span>" +
      "</div>" +
      '<div class="pub-row-link">' +
      linkHtml +
      "</div>" +
      "</article>"
    );
  }

  function mensajeVacio() {
    if (searchQuery.trim()) {
      return (
        "<p>No hay publicaciones indexadas que coincidan por <strong>" +
        esc(etiquetaModoActual()) +
        "</strong> con «" +
        esc(searchQuery.trim()) +
        "».</p>" +
        "<p>Probá otro criterio (título, DOI o autor/a) o usá <strong>Limpiar</strong>.</p>"
      );
    }
    return "<p>No hay registros para mostrar en esta página.</p>";
  }

  function dibujarGrilla() {
    var grid = el("pub-index-grid");
    if (!grid) return;

    if (!items.length) {
      grid.innerHTML = '<div class="pub-msg pub-msg--hint">' + mensajeVacio() + "</div>";
      return;
    }

    var html =
      '<div class="pub-list" role="list">' +
      '<div class="pub-list-head pub-list-head--index" aria-hidden="true">' +
      "<span>Tipo</span><span>Título</span><span>Año</span><span>Enlace</span>" +
      "</div>" +
      items.map(filaHTML).join("") +
      "</div>";

    if (totalPages > 1) {
      html += '<div class="pub-index-pager">';

      if (currentPage > 1) {
        html +=
          '<button type="button" class="pub-more-btn pub-index-nav" data-pub-index-page="' +
          (currentPage - 1) +
          '">← Anterior</button>';
      }

      var info = "Página " + currentPage + " de " + totalPages;
      if (searchQuery.trim()) {
        info += " · " + metaTotal + " resultado" + (metaTotal === 1 ? "" : "s");
      }
      html += '<span class="pub-index-page-info">' + info + "</span>";

      if (currentPage < totalPages) {
        html +=
          '<button type="button" class="pub-more-btn pub-index-nav" data-pub-index-page="' +
          (currentPage + 1) +
          '">Siguiente →</button>';
      }

      html += "</div>";
    }

    grid.innerHTML = html;

    grid.querySelectorAll("[data-pub-index-page]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var p = parseInt(btn.getAttribute("data-pub-index-page"), 10);
        if (!p || p < 1) return;
        cargarPagina(p);
        var panel = el("pub-panel-uccuyo");
        if (panel) panel.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
  }

  function programarBusqueda(valor) {
    if (searchDebounce) window.clearTimeout(searchDebounce);
    searchDebounce = window.setTimeout(function () {
      searchDebounce = null;
      cargarPagina(1, valor);
    }, SEARCH_DEBOUNCE_MS);
  }

  function limpiarBusqueda() {
    var input = el("pub-index-q");
    if (input) input.value = "";
    searchQuery = "";
    actualizarBotonLimpiar();
    cargarPagina(1, "");
  }

  function seleccionarModo(modo) {
    searchMode = modo || "auto";
    document.querySelectorAll("[data-pub-index-mode]").forEach(function (btn) {
      var on = btn.getAttribute("data-pub-index-mode") === searchMode;
      btn.classList.toggle("pub-index-mode--active", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  function initBuscador() {
    var input = el("pub-index-q");
    var clearBtn = el("pub-index-q-clear");
    if (!input) return;

    document.querySelectorAll("[data-pub-index-mode]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        seleccionarModo(btn.getAttribute("data-pub-index-mode"));
        if (input.value.trim()) {
          if (searchDebounce) window.clearTimeout(searchDebounce);
          cargarPagina(1, input.value);
        }
      });
    });

    input.addEventListener("input", function () {
      actualizarBotonLimpiar();
      programarBusqueda(input.value);
    });

    input.addEventListener("keydown", function (e) {
      if (e.key !== "Enter") return;
      e.preventDefault();
      if (searchDebounce) window.clearTimeout(searchDebounce);
      cargarPagina(1, input.value);
    });

    if (clearBtn) {
      clearBtn.addEventListener("click", limpiarBusqueda);
    }
  }

  function activarTab(tabId) {
    var tabs = document.querySelectorAll("[data-pub-tab]");
    var panels = {
      registradas: el("pub-panel-registradas"),
      uccuyo: el("pub-panel-uccuyo")
    };

    tabs.forEach(function (btn) {
      var on = btn.getAttribute("data-pub-tab") === tabId;
      btn.classList.toggle("pub-tab--active", on);
      btn.setAttribute("aria-selected", on ? "true" : "false");
      btn.tabIndex = on ? 0 : -1;
    });

    Object.keys(panels).forEach(function (key) {
      var panel = panels[key];
      if (!panel) return;
      if (key === tabId) {
        panel.hidden = false;
        panel.removeAttribute("hidden");
      } else {
        panel.hidden = true;
      }
    });

    if (tabId === "uccuyo" && !loaded && !loading) {
      cargarPagina(1);
    }
  }

  function initTabs() {
    var tablist = document.querySelector(".pub-tabs");
    if (!tablist) return;

    initBuscador();

    tablist.querySelectorAll("[data-pub-tab]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        activarTab(btn.getAttribute("data-pub-tab"));
      });
      btn.addEventListener("keydown", function (e) {
        if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
        var tabs = Array.prototype.slice.call(tablist.querySelectorAll("[data-pub-tab]"));
        var i = tabs.indexOf(btn);
        if (i < 0) return;
        e.preventDefault();
        var next = e.key === "ArrowRight" ? tabs[i + 1] : tabs[i - 1];
        if (next) {
          next.focus();
          activarTab(next.getAttribute("data-pub-tab"));
        }
      });
    });

    if (window.location.hash === "#publicaciones-uccuyo") {
      activarTab("uccuyo");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTabs);
  } else {
    initTabs();
  }
})();
