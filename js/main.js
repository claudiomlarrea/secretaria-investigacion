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

  function cerrarSubmenus(except) {
    if (!nav) return;
    nav.querySelectorAll(".has-submenu.is-open").forEach(function (item) {
      if (except && item === except) return;
      item.classList.remove("is-open");
      var btn = item.querySelector(".nav-submenu-toggle");
      if (btn) btn.setAttribute("aria-expanded", "false");
    });
  }

  function cerrarMenu() {
    if (!nav || !toggle) return;
    nav.classList.remove("is-open");
    toggle.setAttribute("aria-expanded", "false");
    cerrarSubmenus();
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
    if (!open) cerrarSubmenus();
  });

  nav.querySelectorAll(".nav-submenu-toggle").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      var item = btn.closest(".has-submenu");
      if (!item) return;
      var willOpen = !item.classList.contains("is-open");
      cerrarSubmenus(willOpen ? item : null);
      item.classList.toggle("is-open", willOpen);
      btn.setAttribute("aria-expanded", willOpen ? "true" : "false");
    });
  });

  (function () {
    var desktopHover = window.matchMedia("(hover: hover) and (pointer: fine)");
    var closeTimer = null;
    var activeItem = null;

    function setOpen(item, open) {
      if (!item) return;
      item.classList.toggle("is-open", open);
      var btn = item.querySelector(".nav-submenu-toggle");
      if (btn) btn.setAttribute("aria-expanded", open ? "true" : "false");
    }

    function openItem(item) {
      if (closeTimer) {
        clearTimeout(closeTimer);
        closeTimer = null;
      }
      if (activeItem && activeItem !== item) setOpen(activeItem, false);
      activeItem = item;
      setOpen(item, true);
    }

    function scheduleClose(item) {
      if (closeTimer) clearTimeout(closeTimer);
      closeTimer = setTimeout(function () {
        if (activeItem === item) {
          setOpen(item, false);
          activeItem = null;
        }
        closeTimer = null;
      }, 320);
    }

    nav.querySelectorAll(".has-submenu").forEach(function (item) {
      item.addEventListener("mouseenter", function () {
        if (!desktopHover.matches) return;
        openItem(item);
      });
      item.addEventListener("mouseleave", function () {
        if (!desktopHover.matches) return;
        scheduleClose(item);
      });
    });
  })();

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") cerrarMenu();
  });

  document.addEventListener("click", function (e) {
    if (!nav.contains(e.target) && !(toggle && toggle.contains(e.target))) {
      cerrarSubmenus();
    }
  });
})();
