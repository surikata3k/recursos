/* Botó a la capçalera per mostrar o amagar l'índex de la dreta ("En aquesta pàgina").
   Per defecte l'índex està amagat; la preferència es recorda en aquest navegador. */
(function () {
  var CLAU = "recursos-index-visible";
  var ICONA =
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" aria-hidden="true">' +
    '<path d="M3 9h14V7H3v2m0 4h14v-2H3v2m0 4h14v-2H3v2m16 0h2v-2h-2v2m0-10v2h2V7h-2m0 6h2v-2h-2v2Z"/></svg>';

  function visible() {
    return document.documentElement.classList.contains("mostra-index");
  }

  function actualitza(boto) {
    var text = visible() ? "Amaga l'índex de la pàgina" : "Mostra l'índex de la pàgina";
    boto.title = text;
    boto.setAttribute("aria-label", text);
    boto.setAttribute("aria-pressed", visible() ? "true" : "false");
  }

  function inicia() {
    var index = document.querySelector(".md-sidebar--secondary");
    var capcalera = document.querySelector(".md-header__inner");
    if (!index || index.hasAttribute("hidden") || !capcalera) return;
    if (capcalera.querySelector(".recursos-boto-index")) return;

    var boto = document.createElement("button");
    boto.type = "button";
    boto.className = "md-header__button md-icon recursos-boto-index";
    boto.innerHTML = ICONA;
    actualitza(boto);

    boto.addEventListener("click", function () {
      document.documentElement.classList.toggle("mostra-index");
      try {
        localStorage.setItem(CLAU, visible() ? "1" : "0");
      } catch (e) {}
      actualitza(boto);
    });

    var paleta = capcalera.querySelector('[data-md-component="palette"]');
    capcalera.insertBefore(boto, paleta || capcalera.querySelector(".md-search"));
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicia);
  } else {
    inicia();
  }
})();
