/* Botons a la capçalera per mostrar o amagar els panells laterals:
   - Menú de l'esquerra: visible per defecte (classe .amaga-menu per amagar-lo).
   - Índex de la dreta ("En aquesta pàgina"): amagat per defecte (classe .mostra-index per mostrar-lo).
   La tria es recorda en aquest navegador. overrides/main.html aplica les classes abans de pintar. */
(function () {
  var PANELLS = [
    {
      selector: ".md-sidebar--primary",
      classe: "amaga-menu",
      clau: "recursos-menu-amagat",
      visibleSiActiva: false,
      textMostra: "Mostra el menú",
      textAmaga: "Amaga el menú",
      // Icona dock-left (Material Design Icons)
      icona: "M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2m0 14H9V6h11v12Z",
    },
    {
      selector: ".md-sidebar--secondary",
      classe: "mostra-index",
      clau: "recursos-index-visible",
      visibleSiActiva: true,
      textMostra: "Mostra l'índex de la pàgina",
      textAmaga: "Amaga l'índex de la pàgina",
      // Icona dock-right (Material Design Icons)
      icona: "M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2m0 14h11V6H4v12Z",
    },
  ];

  var arrel = document.documentElement;

  function esVisible(p) {
    return arrel.classList.contains(p.classe) === p.visibleSiActiva;
  }

  function actualitza(boto, p) {
    var text = esVisible(p) ? p.textAmaga : p.textMostra;
    boto.title = text;
    boto.setAttribute("aria-label", text);
    boto.setAttribute("aria-pressed", esVisible(p) ? "true" : "false");
  }

  function creaBoto(p) {
    var boto = document.createElement("button");
    boto.type = "button";
    boto.className = "md-header__button md-icon recursos-boto-panell";
    boto.innerHTML =
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" aria-hidden="true"><path d="' +
      p.icona + '"/></svg>';
    actualitza(boto, p);
    boto.addEventListener("click", function () {
      arrel.classList.toggle(p.classe);
      try {
        localStorage.setItem(p.clau, arrel.classList.contains(p.classe) ? "1" : "0");
      } catch (e) {}
      actualitza(boto, p);
    });
    return boto;
  }

  function inicia() {
    var capcalera = document.querySelector(".md-header__inner");
    if (!capcalera || capcalera.querySelector(".recursos-boto-panell")) return;
    var referencia =
      capcalera.querySelector('[data-md-component="palette"]') ||
      capcalera.querySelector(".md-search");

    PANELLS.forEach(function (p) {
      var panell = document.querySelector(p.selector);
      if (!panell || panell.hasAttribute("hidden")) return;
      capcalera.insertBefore(creaBoto(p), referencia);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicia);
  } else {
    inicia();
  }
})();
