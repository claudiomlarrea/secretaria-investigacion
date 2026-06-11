(function () {
  var CFG = window.SEC_VISITANTES || {};
  var root = document.getElementById("visitantes-widget");
  if (!root) return;

  var base = CFG.VISITAS_SCRIPT_URL && String(CFG.VISITAS_SCRIPT_URL).trim();
  var site = CFG.SITE && String(CFG.SITE).trim();
  var paginas = CFG.PAGINAS || {};
  if (!base || !site) return;

  function esc(s) {
    var d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
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

  function esRespuestaVisitas(data) {
    return data && data.ok && data.secretaria != null && data.observatorio != null && !Array.isArray(data.items);
  }

  function pintar(data) {
    if (!esRespuestaVisitas(data)) return;
    var urlSec = paginas.secretaria || "#";
    var urlObs = paginas.observatorio || "#";
    root.hidden = false;
    root.innerHTML =
      "Visitas a las páginas web: " +
      '<a href="' +
      esc(urlSec) +
      '" rel="noopener noreferrer">Secretaría de Investigación</a> <strong>' +
      fmt(data.secretaria) +
      "</strong> · " +
      '<a href="' +
      esc(urlObs) +
      '" rel="noopener noreferrer">Observatorio de IA</a> <strong>' +
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
      var name = "_secVisCb_" + Math.floor(Math.random() * 1e9);
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
