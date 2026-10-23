/* Cercador i filtres del catàleg de la portada.
   Filtra les targetes (ul.cataleg--material > li) per text, temàtica i mòdul. */
(function () {
  function inicia() {
    var llista = document.querySelector("ul.cataleg--material");
    if (!llista) return;

    var input = document.getElementById("cercador-input");
    var comptador = document.getElementById("cercador-comptador");
    var buit = document.getElementById("cercador-sense-resultats");
    var targetes = Array.prototype.slice.call(llista.children);
    var estat = { text: "", tag: "", modul: "" };

    function normalitza(s) {
      return (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
    }

    targetes.forEach(function (li) {
      li._text = normalitza(li.dataset.text);
      li._tags = (li.dataset.tags || "").split("|");
    });

    function aplica() {
      var paraules = normalitza(estat.text).split(/\s+/).filter(Boolean);
      var visibles = 0;
      targetes.forEach(function (li) {
        var ok =
          (!estat.tag || li._tags.indexOf(estat.tag) !== -1) &&
          (!estat.modul || li.dataset.modul === estat.modul) &&
          paraules.every(function (p) { return li._text.indexOf(p) !== -1; });
        li.classList.toggle("card-oculta", !ok);
        if (ok) visibles++;
      });
      comptador.textContent = visibles + " / " + targetes.length;
      buit.style.display = visibles ? "none" : "block";
    }

    function xips(selector, clau) {
      var elements = document.querySelectorAll(selector + " .cercador-tag");
      Array.prototype.forEach.call(elements, function (x) {
        function tria() {
          Array.prototype.forEach.call(elements, function (y) { y.classList.remove("actiu"); });
          x.classList.add("actiu");
          estat[clau] = x.dataset[clau] || "";
          aplica();
        }
        x.addEventListener("click", tria);
        x.addEventListener("keydown", function (e) {
          if (e.key === "Enter" || e.key === " ") { e.preventDefault(); tria(); }
        });
      });
    }

    input.addEventListener("input", function () { estat.text = input.value; aplica(); });
    xips(".cercador-temes", "tag");
    xips(".cercador-moduls", "modul");
    aplica();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", inicia);
  } else {
    inicia();
  }
})();
