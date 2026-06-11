(function () {
  var PUB = window.SEC_PUBLICACIONES || window.OBS_PUBLICACIONES || {};
  var root = document.getElementById("visitantes-widget");
  if (!root) return;

  var base = PUB.APPS_SCRIPT_URL && String(PUB.APPS_SCRIPT_URL).trim();
  if (!base) return;

  function fmt(n) {
    var x = Number(n);
    if (!isFinite(x)) return "—";
    try {
      return x.toLocaleString("es-AR");
    } catch (e) {
      return String(x);
    }
  }

  function pintar(data) {
    if (!data || !data.ok) return;
    root.hidden = false;
    root.innerHTML =
      "Visitas (" +
      (data.periodo || "últimos 90 días") +
      "): Secretaría <strong>" +
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
      var name = "_visStats_" + Math.floor(Math.random() * 1e9);
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
    base + (base.indexOf("?") >= 0 ? "&" : "?") + "action=stats&_=" + Date.now();

  fetchJson(url).then(pintar, function () {
    fetchJsonp(url).then(pintar, function () {});
  });
})();
