(function () {
  var CFG = window.SEC_VISITANTES || {};
  var PUB = window.SEC_PUBLICACIONES || window.OBS_PUBLICACIONES || {};
  var mapRoot = document.getElementById("visitas-mapa");
  var listRoot = document.getElementById("visitas-lista");
  var statusEl = document.getElementById("visitas-status");
  if (!mapRoot) return;

  var base = PUB.APPS_SCRIPT_URL && String(PUB.APPS_SCRIPT_URL).trim();
  var site = (CFG.SITE && String(CFG.SITE).trim()) || "observatorio";
  if (!base) {
    setStatus("No se pudo cargar el mapa de visitas.");
    return;
  }

  var GEO_SESSION_KEY = "visitgeo_" + site;
  var COUNTRY_CENTROIDS = {
    AF: [-65.2, 33.9],
    AL: [20.2, 41.2],
    DZ: [1.7, 28.0],
    AD: [1.6, 42.5],
    AO: [17.9, -11.2],
    AR: [-64.0, -34.6],
    AM: [45.0, 40.1],
    AU: [133.8, -25.3],
    AT: [14.6, 47.5],
    AZ: [47.6, 40.1],
    BS: [-77.4, 25.0],
    BH: [50.6, 26.0],
    BD: [90.4, 23.7],
    BY: [27.9, 53.7],
    BE: [4.5, 50.5],
    BZ: [-88.5, 17.2],
    BJ: [2.3, 9.3],
    BT: [90.4, 27.5],
    BO: [-63.6, -16.3],
    BA: [17.7, 43.9],
    BW: [24.7, -22.3],
    BR: [-51.9, -14.2],
    BN: [114.7, 4.5],
    BG: [25.5, 42.7],
    BF: [-1.6, 12.2],
    BI: [29.9, -3.4],
    KH: [104.9, 12.6],
    CM: [12.4, 7.4],
    CA: [-106.3, 56.1],
    CV: [-23.6, 16.0],
    CF: [20.9, 6.6],
    TD: [18.7, 15.5],
    CL: [-71.5, -35.7],
    CN: [104.2, 35.9],
    CO: [-74.3, 4.6],
    CR: [-83.8, 9.7],
    HR: [15.2, 45.1],
    CU: [-77.8, 21.5],
    CY: [33.4, 35.1],
    CZ: [15.5, 49.8],
    CD: [21.8, -4.0],
    DK: [9.5, 56.3],
    DJ: [42.6, 11.8],
    DO: [-70.2, 18.7],
    EC: [-78.2, -1.8],
    EG: [30.8, 26.8],
    SV: [-88.9, 13.8],
    GQ: [10.3, 1.6],
    ER: [39.8, 15.2],
    EE: [25.0, 58.6],
    SZ: [31.5, -26.5],
    ET: [40.5, 9.1],
    FJ: [178.1, -17.7],
    FI: [26.0, 61.9],
    FR: [2.2, 46.2],
    GA: [11.6, -0.8],
    GM: [-15.3, 13.4],
    GE: [43.4, 42.3],
    DE: [10.5, 51.2],
    GH: [-1.0, 7.9],
    GR: [21.8, 39.1],
    GT: [-90.2, 15.8],
    GN: [-9.7, 9.9],
    GY: [-58.9, 4.9],
    HT: [-72.3, 18.97],
    HN: [-86.2, 15.2],
    HK: [114.2, 22.3],
    HU: [19.5, 47.2],
    IS: [-19.0, 64.96],
    IN: [78.96, 20.6],
    ID: [113.9, -0.8],
    IR: [53.7, 32.4],
    IQ: [43.7, 33.2],
    IE: [-8.2, 53.1],
    IL: [34.9, 31.0],
    IT: [12.6, 41.9],
    CI: [-5.5, 7.5],
    JM: [-77.3, 18.1],
    JP: [138.3, 36.2],
    JO: [36.2, 30.6],
    KZ: [66.9, 48.0],
    KE: [37.9, -0.0],
    KW: [47.5, 29.3],
    KG: [74.8, 41.2],
    LA: [102.5, 19.9],
    LV: [24.6, 56.9],
    LB: [35.9, 33.9],
    LS: [28.2, -29.6],
    LR: [-9.4, 6.4],
    LY: [17.2, 26.3],
    LT: [23.9, 55.2],
    LU: [6.1, 49.8],
    MG: [46.9, -18.8],
    MW: [34.3, -13.3],
    MY: [101.98, 4.2],
    ML: [-3.996, 17.6],
    MT: [14.4, 35.9],
    MR: [-10.9, 21.0],
    MU: [57.6, -20.3],
    MX: [-102.6, 23.6],
    MD: [28.4, 47.4],
    MC: [7.4, 43.7],
    MN: [103.8, 46.9],
    ME: [19.4, 42.7],
    MA: [-7.1, 31.8],
    MZ: [35.5, -18.7],
    MM: [96.0, 21.9],
    NA: [18.5, -22.96],
    NP: [84.1, 28.4],
    NL: [5.3, 52.1],
    NZ: [174.9, -40.9],
    NI: [-85.2, 12.9],
    NE: [8.1, 17.6],
    NG: [8.7, 9.1],
    KP: [127.5, 40.3],
    MK: [21.7, 41.6],
    NO: [8.5, 60.5],
    OM: [55.9, 21.5],
    PK: [69.3, 30.4],
    PA: [-80.8, 8.5],
    PG: [143.96, -6.3],
    PY: [-58.4, -23.4],
    PE: [-75.0, -9.2],
    PH: [121.8, 12.9],
    PL: [19.1, 51.9],
    PT: [-8.2, 39.4],
    PR: [-66.6, 18.2],
    QA: [51.2, 25.4],
    CG: [15.8, -0.2],
    RO: [24.97, 45.9],
    RU: [105.3, 61.5],
    RW: [29.9, -1.9],
    SA: [45.1, 23.9],
    SN: [-14.5, 14.5],
    RS: [21.0, 44.0],
    SG: [103.8, 1.4],
    SK: [19.7, 48.7],
    SI: [14.8, 46.2],
    SO: [46.2, 5.2],
    ZA: [22.9, -30.6],
    KR: [127.8, 35.9],
    SS: [31.3, 6.9],
    ES: [-3.7, 40.5],
    LK: [80.8, 7.9],
    SD: [30.2, 12.9],
    SR: [-56.0, 3.9],
    SE: [18.6, 60.1],
    CH: [8.2, 46.8],
    SY: [38.996, 34.8],
    TW: [120.96, 23.7],
    TJ: [71.3, 38.9],
    TZ: [34.9, -6.4],
    TH: [100.99, 15.9],
    TL: [125.7, -8.9],
    TG: [0.8, 8.6],
    TT: [-61.2, 10.7],
    TN: [9.5, 33.9],
    TR: [35.2, 38.96],
    TM: [59.6, 38.97],
    UG: [32.3, 1.4],
    UA: [31.2, 48.4],
    AE: [53.8, 23.4],
    GB: [-3.4, 55.4],
    US: [-95.7, 37.1],
    UY: [-55.8, -32.5],
    UZ: [64.6, 41.4],
    VE: [-66.6, 6.4],
    VN: [108.3, 14.1],
    YE: [48.5, 15.6],
    ZM: [27.8, -13.1],
    ZW: [29.2, -19.0]
  };

  var AR_PROVINCE_CENTROIDS = {
    "ciudad autonoma de buenos aires": [-58.4, -34.6],
    "ciudad de buenos aires": [-58.4, -34.6],
    caba: [-58.4, -34.6],
    "buenos aires": [-60.0, -36.7],
    catamarca: [-66.0, -28.5],
    chaco: [-60.0, -26.4],
    chubut: [-68.0, -43.8],
    cordoba: [-64.0, -32.0],
    corrientes: [-58.8, -28.6],
    "entre rios": [-59.2, -32.0],
    formosa: [-59.0, -24.6],
    jujuy: [-65.5, -23.3],
    "la pampa": [-65.0, -37.0],
    "la rioja": [-66.9, -29.4],
    mendoza: [-68.6, -34.6],
    misiones: [-54.6, -26.9],
    neuquen: [-69.0, -38.95],
    "rio negro": [-67.3, -40.7],
    salta: [-65.0, -24.8],
    "san juan": [-68.5, -30.9],
    "san luis": [-66.0, -33.3],
    "santa cruz": [-69.96, -48.8],
    "santa fe": [-61.0, -30.7],
    "santiago del estero": [-63.3, -27.8],
    "tierra del fuego": [-67.0, -54.4],
    tucuman: [-65.3, -26.9]
  };

  function setStatus(msg) {
    if (!statusEl) return;
    statusEl.hidden = !msg;
    statusEl.textContent = msg || "";
  }

  function fmt(n) {
    var x = Number(n);
    if (!isFinite(x)) return "—";
    try {
      return x.toLocaleString("es-AR");
    } catch (e) {
      return String(x);
    }
  }

  function normKey(s) {
    return String(s || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim();
  }

  function appsUrl(action, extra) {
    var url =
      base +
      (base.indexOf("?") >= 0 ? "&" : "?") +
      "action=" +
      encodeURIComponent(action) +
      "&site=" +
      encodeURIComponent(site) +
      "&_=" +
      Date.now();
    if (extra) url += "&" + extra;
    return url;
  }

  function fetchJson(url) {
    return fetch(url, { method: "GET" }).then(function (r) {
      if (!r.ok) throw new Error("network");
      return r.json();
    });
  }

  function fetchJsonp(url) {
    return new Promise(function (resolve, reject) {
      var name = "_visMapCb_" + Math.floor(Math.random() * 1e9);
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

  function fetchApps(action, extra) {
    var url = appsUrl(action, extra);
    return fetchJson(url).then(null, function () {
      return fetchJsonp(url);
    });
  }

  function loadLeaflet() {
    return new Promise(function (resolve, reject) {
      if (window.L) {
        resolve(window.L);
        return;
      }
      if (!document.getElementById("leaflet-css")) {
        var link = document.createElement("link");
        link.id = "leaflet-css";
        link.rel = "stylesheet";
        link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
        link.integrity = "sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=";
        link.crossOrigin = "";
        document.head.appendChild(link);
      }
      var script = document.createElement("script");
      script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
      script.integrity = "sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=";
      script.crossOrigin = "";
      script.onload = function () {
        if (window.L) resolve(window.L);
        else reject(new Error("leaflet"));
      };
      script.onerror = function () {
        reject(new Error("leaflet"));
      };
      document.head.appendChild(script);
    });
  }

  function colorForCount(count, max) {
    if (!max || count <= 0) return "#d9e8e1";
    var t = Math.min(1, count / max);
    if (t < 0.25) return "#a8cfc0";
    if (t < 0.5) return "#5fa88c";
    if (t < 0.75) return "#0d6e4f";
    return "#7a1532";
  }

  function radiusForCount(count, max) {
    var t = max > 0 ? count / max : 0;
    return 8 + Math.round(t * 22);
  }

  function provinceCentroid(region) {
    return AR_PROVINCE_CENTROIDS[normKey(region)] || null;
  }

  function renderList(data) {
    if (!listRoot) return;
    var countries = data.countries || [];
    var regions = data.regions || [];
    if (!countries.length) {
      listRoot.innerHTML =
        "<p class=\"visitas-empty\">Todavía no hay orígenes registrados. El mapa se irá completando con las nuevas visitas.</p>";
      return;
    }

    var html = "<div class=\"visitas-tables\">";
    html += "<div><h3>Países</h3><ol class=\"visitas-rank\">";
    countries.slice(0, 12).forEach(function (c) {
      html +=
        "<li><span>" +
        escapeHtml(c.name || c.code) +
        "</span><strong>" +
        fmt(c.count) +
        "</strong></li>";
    });
    html += "</ol></div>";

    if (regions.length) {
      html += "<div><h3>Provincias / regiones</h3><ol class=\"visitas-rank\">";
      regions.slice(0, 12).forEach(function (r) {
        var label = r.region;
        if (r.countryName) label += " (" + r.countryName + ")";
        html +=
          "<li><span>" +
          escapeHtml(label) +
          "</span><strong>" +
          fmt(r.count) +
          "</strong></li>";
      });
      html += "</ol></div>";
    }
    html += "</div>";
    listRoot.innerHTML = html;
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderMap(L, data) {
    mapRoot.innerHTML = "";
    var map = L.map(mapRoot, {
      scrollWheelZoom: false,
      worldCopyJump: true
    }).setView([-15, -40], 2);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 8,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    var countries = data.countries || [];
    var regions = data.regions || [];
    var max = 0;
    countries.forEach(function (c) {
      if (c.count > max) max = c.count;
    });

    var bounds = [];
    var arRegions = regions.filter(function (r) {
      return String(r.country || "").toUpperCase() === "AR" && provinceCentroid(r.region);
    });

    countries.forEach(function (c) {
      var code = String(c.code || "").toUpperCase();
      if (code === "AR" && arRegions.length) return;
      var centroid = COUNTRY_CENTROIDS[code];
      if (!centroid) return;
      var marker = L.circleMarker([centroid[1], centroid[0]], {
        radius: radiusForCount(c.count, max),
        color: "#042f23",
        weight: 1,
        fillColor: colorForCount(c.count, max),
        fillOpacity: 0.78
      }).addTo(map);
      marker.bindPopup(
        "<strong>" +
          escapeHtml(c.name || code) +
          "</strong><br>" +
          fmt(c.count) +
          " visita" +
          (c.count === 1 ? "" : "s")
      );
      bounds.push([centroid[1], centroid[0]]);
    });

    arRegions.forEach(function (r) {
      var c = provinceCentroid(r.region);
      var marker = L.circleMarker([c[1], c[0]], {
        radius: radiusForCount(r.count, max),
        color: "#4a0c1f",
        weight: 1,
        fillColor: colorForCount(r.count, max),
        fillOpacity: 0.78
      }).addTo(map);
      marker.bindPopup(
        "<strong>" +
          escapeHtml(r.region) +
          "</strong><br>" +
          fmt(r.count) +
          " visita" +
          (r.count === 1 ? "" : "s")
      );
      bounds.push([c[1], c[0]]);
    });

    if (bounds.length === 1) {
      map.setView(bounds[0], arRegions.length ? 5 : 3);
    } else if (bounds.length > 1) {
      map.fitBounds(bounds, { padding: [36, 36], maxZoom: arRegions.length ? 5 : 4 });
    }

    window.setTimeout(function () {
      map.invalidateSize();
    }, 200);
  }

  function paint(data) {
    if (!data || !data.ok) {
      setStatus("No se pudo obtener el origen de las visitas.");
      return;
    }
    var totalNote = document.getElementById("visitas-total");
    if (totalNote) {
      totalNote.hidden = false;
      totalNote.innerHTML =
        "Visitas con origen registrado: <strong>" +
        fmt(data.total || 0) +
        "</strong>";
    }
    setStatus("");
    renderList(data);
    loadLeaflet()
      .then(function (L) {
        renderMap(L, data);
      })
      .catch(function () {
        mapRoot.innerHTML =
          "<p class=\"visitas-empty\">No se pudo cargar el mapa interactivo. La lista de orígenes sigue disponible.</p>";
      });
  }

  function registerGeoOnce() {
    try {
      if (sessionStorage.getItem(GEO_SESSION_KEY)) return Promise.resolve();
    } catch (e) {}

    return fetch("https://ipapi.co/json/", { method: "GET" })
      .then(function (r) {
        if (!r.ok) throw new Error("geo");
        return r.json();
      })
      .then(function (geo) {
        if (!geo || geo.error) throw new Error("geo");
        var country = String(geo.country_code || "").trim();
        var countryName = String(geo.country_name || "").trim();
        var region = String(geo.region || "").trim();
        if (!country) throw new Error("geo");
        var extra =
          "country=" +
          encodeURIComponent(country) +
          "&countryName=" +
          encodeURIComponent(countryName) +
          "&region=" +
          encodeURIComponent(region);
        return fetchApps("visitgeo", extra).then(function (res) {
          if (res && res.ok) {
            try {
              sessionStorage.setItem(GEO_SESSION_KEY, "1");
            } catch (e2) {}
          } else if (res && res.error === "invalid_site") {
            window.__visitasGeoBackendPendiente = true;
          }
          return res;
        });
      })
      .catch(function () {
        return null;
      });
  }

  setStatus("Cargando origen de visitas…");

  registerGeoOnce()
    .then(function () {
      return fetchApps("visitmap");
    })
    .then(function (data) {
      paint(data);
      if (
        window.__visitasGeoBackendPendiente &&
        data &&
        data.ok &&
        !(data.total > 0)
      ) {
        setStatus(
          "El mapa está listo, pero Apps Script aún no acepta este sitio. En Publicaciones Página Web hay que pegar PublicacionesWeb.gs actualizado y publicar Nueva versión (ver PARCHE-VISITGEO-SECRETARIA.txt)."
        );
      }
    }, function () {
      setStatus("No se pudo cargar el origen de las visitas.");
    });
})();
