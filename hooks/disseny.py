"""Prepara les dades que fa servir la plantilla d'una sola columna (overrides/main.html).

- Treu el primer <h1> del contingut i el desa a page.meta["_h1"], perquè la
  plantilla el pugui posar abans de l'índex de la pàgina.
- Calcula la ruta (cicle › mòdul › RA) per a l'enllaç «← Índex».
- Calcula l'etiqueta del mòdul (p. ex. «ASIX Ciber 0375 · RA1») i el tipus de material.
"""
import re

H1 = re.compile(r"<h1[^>]*>(.*?)</h1>\s*", re.S)
ENLLAC_PERMANENT = re.compile(r'<a class="headerlink"[^>]*>.*?</a>', re.S)
TIPUS = {
    "teoria": "Teoria",
    "practica": "Pràctica",
    "activitat": "Activitat",
    "recurs": "Recurs",
    "solucions": "Solucions",
}


def _curt(pagina):
    """Etiqueta curta per a la ruta: «ASIX Ciber», «0375», «RA1»."""
    nivell = pagina.meta.get("nivell")
    titol = pagina.meta.get("title") or pagina.title or ""
    if nivell in ("modul", "ra"):
        return titol.split("·", 1)[0].strip()
    return titol


def on_page_content(html, page, config, files, **kwargs):
    trobat = H1.search(html)
    if trobat:
        page.meta["_h1"] = ENLLAC_PERMANENT.sub("", trobat.group(1)).strip()
        html = html[: trobat.start()] + html[trobat.end():]
    return html


def on_page_context(context, page, config, nav, **kwargs):
    per_ruta = {p.file.src_uri: p for p in nav.pages}
    parts = page.file.src_uri.split("/")
    es_index = parts[-1] == "index.md"
    directoris = parts[:-2] if es_index else parts[:-1]

    molles = []
    for i in range(1, len(directoris) + 1):
        pare = per_ruta.get("/".join(directoris[:i]) + "/index.md")
        if pare is not None:
            molles.append({"url": pare.url, "etiqueta": _curt(pare), "titol": pare.meta.get("title", pare.title)})
    page.meta["_molles"] = molles
    page.meta["_portada"] = page.is_homepage

    # Etiqueta del mòdul per a les pàgines de material i de RA
    if len(parts) >= 3 and not (es_index and len(parts) <= 3):
        cicle = per_ruta.get(parts[0] + "/index.md")
        modul = per_ruta.get(f"{parts[0]}/{parts[1]}/index.md")
        if cicle and modul:
            etiqueta = f"{_curt(cicle)} {parts[1]}"
            if len(parts) >= 4 and parts[2].startswith("ra"):
                etiqueta += f" · RA{parts[2][2:]}"
            page.meta["_modul"] = {
                "etiqueta": etiqueta,
                "titol": f"{_curt(cicle)} {modul.meta.get('title', modul.title)}",
            }

    tipus = str(page.meta.get("tipus", "")).lower()
    if tipus in TIPUS:
        page.meta["_tipus"] = TIPUS[tipus]
    return context
