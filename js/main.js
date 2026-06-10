(function () {
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector("#site-nav");
  var siteTop = document.querySelector(".site-top");

  function headerOffset() {
    return siteTop ? siteTop.offsetHeight + 10 : 110;
  }

  function scrollToTarget(el, updateHash) {
    if (!el) return;
    var top =
      el.getBoundingClientRect().top + window.pageYOffset - headerOffset();
    window.scrollTo({ top: Math.max(0, top), left: 0, behavior: "smooth" });
    if (updateHash && el.id) {
      history.pushState(null, "", "#" + el.id);
    }
  }

  function cerrarMenu() {
    if (!nav || !toggle) return;
    nav.classList.remove("is-open");
    toggle.setAttribute("aria-expanded", "false");
  }

  function irInicio() {
    window.scrollTo({ top: 0, left: 0, behavior: "smooth" });
    if (window.location.hash !== "#inicio") {
      history.pushState(null, "", "#inicio");
    }
  }

  document.querySelectorAll('a[href="#inicio"]').forEach(function (link) {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      irInicio();
      cerrarMenu();
    });
  });

  document.querySelectorAll('a[href^="#"]').forEach(function (link) {
    var hash = link.getAttribute("href");
    if (!hash || hash === "#" || hash === "#inicio") return;

    link.addEventListener("click", function (e) {
      var el = document.querySelector(hash);
      if (!el) return;
      e.preventDefault();
      scrollToTarget(el, true);
      cerrarMenu();
    });
  });

  function alinearHashInicial() {
    var hash = window.location.hash;
    if (hash === "#investigaciones") {
      history.replaceState(null, "", "#inicio");
      hash = "#inicio";
    }
    if (!hash || hash === "#inicio") return;
    var el = document.querySelector(hash);
    if (!el) return;
    requestAnimationFrame(function () {
      scrollToTarget(el, false);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", alinearHashInicial);
  } else {
    alinearHashInicial();
  }

  if (!toggle || !nav) return;

  toggle.addEventListener("click", function () {
    var open = nav.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
  });
})();
