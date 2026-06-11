(function () {
  var CFG = window.SEC_VISITANTES || {};
  var PUB = window.SEC_PUBLICACIONES || window.OBS_PUBLICACIONES || {};
  var root = document.getElementById("visitantes-widget");
  if (!root) return;

  var base = PUB.APPS_SCRIPT_URL && String(PUB.APPS_SCRIPT_URL).trim();
  var site = CFG.SITE && String(CFG.SITE).trim();
  if (!base || !site) return;

  function fmt(n) {
    var x = Number(n);
    if (!isFinite(x)) return "—";
    try {
      return x.toLocaleString("es-AR");
    } catch (e) {
      return String(x);
    }
  }

  function esContador(data) {
    return data && data.ok && data.secretaria != null && data.observatorio != null && !Array.isArray(data.items);
  }

  function pintar(data) {
    if (!esContador(data)) return;
    root.hidden = false;
    root.innerHTML =
      "Visitas a las páginas web: Secretaría <strong>" +
      fmt(data.secretaria) +
      "</strong> · Observatorio <strong>" +
      fmt(data.observatorio) +
      "</strong>";
  }

  function fetchJson(url) {
    return fetch(url, { method: "GET" }).then(function (r) {
      if (!r.ok) throw new Error("network");
      return r.json();
    });
  }

  function fetchJsonp(url) {
    return new Promise(function (resolve, reject) {
      var name = "_visCb_" + Math.floor(Math.random() * 1e9);
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

  var url =
    base +
    (base.indexOf("?") >= 0 ? "&" : "?") +
    "action=visit&site=" +
    encodeURIComponent(site) +
    "&_=" +
    Date.now();

  fetchJson(url).then(pintar, function () {
    fetchJsonp(url).then(pintar, function () {});
  });
})();
