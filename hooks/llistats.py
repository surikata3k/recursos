"""Genera automàticament els llistats de la web.

Substitueix aquests marcadors quan MkDocs construeix la pàgina:

  <!-- cataleg -->           catàleg de tot el material amb cercador i filtres (portada)
  <!-- llistat-cicles -->    mòduls de cada cicle (portada)
  <!-- llistat-moduls -->    mòduls d'un cicle
  <!-- llistat-ras -->       taula dels RA d'un mòdul, amb el nombre de materials
  <!-- llistat-material -->  material d'un RA (els .md de la mateixa carpeta)

Per publicar material nou només cal deixar un fitxer .md a la carpeta del RA:
apareixerà sol al catàleg, als filtres, al llistat del RA i als comptadors.
"""
import re
from html import escape
from pathlib import Path

from mkdocs.utils import get_relative_url
from mkdocs.utils.meta import get_data

TIPUS = {
    "teoria": "Teoria",
    "practica": "Pràctica",
    "activitat": "Activitat",
    "solucions": "Solucions",
    "recurs": "Recurs",
}


# ---------------------------------------------------------------- utilitats

def _meta(cami: Path) -> dict:
    cos, meta = get_data(cami.read_text(encoding="utf-8"))
    meta = dict(meta or {})
    if "title" not in meta:
        for linia in cos.splitlines():
            if linia.startswith("# "):
                meta["title"] = linia[2:].strip()
                break
        else:
            meta["title"] = cami.stem.replace("-", " ").capitalize()
    return meta


def _materials(carpeta: Path) -> list:
    return sorted(p for p in carpeta.rglob("*.md") if p.name != "index.md")


def _subcarpetes_amb_index(carpeta: Path) -> list:
    return sorted(d for d in carpeta.iterdir() if d.is_dir() and (d / "index.md").exists())


def _numero_ra(carpeta: Path) -> int:
    try:
        return int(carpeta.name.removeprefix("ra"))
    except ValueError:
        return 999


def _plural(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _cicles(docs: Path) -> list:
    """Llista de (carpeta, meta) dels cicles, en l'ordre definit al currículum."""
    cicles = []
    for d in _subcarpetes_amb_index(docs):
        meta = _meta(d / "index.md")
        if meta.get("nivell") == "cicle":
            cicles.append((meta.get("ordre", 99), d.name, d, meta))
    return [(d, m) for _, _, d, m in sorted(cicles)]


class Enllacos:
    """Calcula enllaços relatius des de la pàgina actual cap a qualsevol fitxer .md."""

    def __init__(self, docs: Path, page, files):
        self.docs, self.page, self.files = docs, page, files

    def __call__(self, cami: Path) -> str:
        fitxer = self.files.get_file_from_path(cami.relative_to(self.docs).as_posix())
        return get_relative_url(fitxer.url, self.page.url) if fitxer else "#"


def _etiqueta(text: str, classe: str = "", titol: str = "") -> str:
    attr_titol = f' title="{escape(titol)}"' if titol else ""
    return f'<span class="card-etiqueta {classe}"{attr_titol}>{escape(text)}</span>'


def _targeta(titol, href, descripcio="", etiquetes=(), dades=None) -> str:
    attrs = "".join(f' data-{k}="{escape(v)}"' for k, v in (dades or {}).items())
    desc = f"<p>{escape(descripcio)}</p>" if descripcio else ""
    ets = f'<div class="card-etiquetes">{"".join(etiquetes)}</div>' if etiquetes else ""
    return f'<li{attrs}><a href="{escape(href)}">{escape(titol)}</a>{desc}{ets}</li>'


def _graella(targetes: list, classe: str = "") -> str:
    return f'<ul class="cataleg {classe}">' + "".join(targetes) + "</ul>"


# ---------------------------------------------------------------- catàleg

def _items_cataleg(docs: Path) -> list:
    items = []
    for d_cicle, m_cicle in _cicles(docs):
        for d_modul in _subcarpetes_amb_index(d_cicle):
            m_modul = _meta(d_modul / "index.md")
            nom_modul = m_modul["title"].split("·", 1)[-1].strip()
            for f in _materials(d_modul):
                meta = _meta(f)
                rel = f.relative_to(d_modul).parts
                ra = _numero_ra(Path(rel[0])) if len(rel) > 1 and rel[0].startswith("ra") else None
                items.append({
                    "cami": f,
                    "titol": meta["title"],
                    "descripcio": meta.get("description", ""),
                    "tipus": TIPUS.get(str(meta.get("tipus", "")).lower(), ""),
                    "tags": list(meta.get("tags") or []),
                    "modul_id": f"{_slug(m_cicle['title'])}-{d_modul.name}",
                    "modul_curt": f"{m_cicle['title']} {d_modul.name}",
                    "modul_nom": f"{m_cicle['title']} {d_modul.name} · {nom_modul}",
                    "ra": ra,
                })
    return items


def _cataleg(docs: Path, enllac) -> str:
    items = _items_cataleg(docs)
    total = len(items)

    temes = {}
    for it in items:
        for t in it["tags"]:
            temes[t] = temes.get(t, 0) + 1
    moduls = {}
    for it in items:
        moduls.setdefault(it["modul_id"], [it["modul_curt"], it["modul_nom"], 0])[2] += 1

    xips_temes = [f'<span class="cercador-tag actiu" data-tag="" role="button" tabindex="0">Tots <span class="n">{total}</span></span>']
    for t in sorted(temes, key=str.lower):
        xips_temes.append(
            f'<span class="cercador-tag" data-tag="{escape(_slug(t))}" role="button" tabindex="0">'
            f'{escape(t)} <span class="n">{temes[t]}</span></span>'
        )
    xips_moduls = [f'<span class="cercador-tag actiu" data-modul="" role="button" tabindex="0">Tots els mòduls <span class="n">{total}</span></span>']
    for mid, (curt, nom, n) in moduls.items():
        xips_moduls.append(
            f'<span class="cercador-tag" data-modul="{escape(mid)}" title="{escape(nom)}" role="button" tabindex="0">'
            f'{escape(curt)} <span class="n">{n}</span></span>'
        )

    targetes = []
    for it in items:
        ets = []
        if it["tipus"]:
            ets.append(_etiqueta(it["tipus"], "card-etiqueta-tipus"))
        ets += [_etiqueta(t) for t in it["tags"]]
        ra = f" · RA{it['ra']}" if it["ra"] else ""
        ets.append(_etiqueta(it["modul_curt"] + ra, "card-etiqueta-modul", it["modul_nom"]))
        text = " ".join([it["titol"], it["descripcio"], it["tipus"], *it["tags"], it["modul_nom"]]).lower()
        targetes.append(_targeta(
            it["titol"], enllac(it["cami"]), it["descripcio"], ets,
            {"text": text, "tags": "|".join(_slug(t) for t in it["tags"]), "modul": it["modul_id"]},
        ))

    return "\n".join([
        '<div class="cercador-barra">'
        '<input type="search" class="cercador-input" id="cercador-input" '
        'placeholder="Cerca un document (nom o descripció)..." autocomplete="off" aria-label="Cerca un document">'
        f'<span class="cercador-comptador" id="cercador-comptador">{total} / {total}</span>'
        "</div>",
        '<div class="cercador-tags cercador-temes">' + "".join(xips_temes) + "</div>",
        '<div class="cercador-tags cercador-moduls">' + "".join(xips_moduls) + "</div>",
        _graella(targetes, "cataleg--material"),
        '<p class="cercador-sense-resultats" id="cercador-sense-resultats">Cap document coincideix amb la cerca.</p>',
    ])


# ---------------------------------------------------------------- llistats d'estructura

def _targetes_moduls(d_cicle: Path, m_cicle: dict, enllac) -> list:
    targetes = []
    for d in _subcarpetes_amb_index(d_cicle):
        meta = _meta(d / "index.md")
        ras = [r for r in _subcarpetes_amb_index(d) if r.name.startswith("ra")]
        nom = meta["title"].split("·", 1)[-1].strip()
        n = len(_materials(d))
        targetes.append(_targeta(
            f"{d.name} · {nom}", enllac(d / "index.md"),
            f"{_plural(len(ras), 'resultat', 'resultats')} d'aprenentatge · {_plural(n, 'material', 'materials')}",
            [_etiqueta(f"{m_cicle['title']} {d.name}", "card-etiqueta-modul", f"{m_cicle['title']} · {m_cicle.get('description', '')}")],
        ))
    return targetes


def _llistat_cicles(docs: Path, enllac) -> str:
    blocs = []
    for d_cicle, m_cicle in _cicles(docs):
        blocs.append(
            f'<h3 class="cicle-titol"><a href="{escape(enllac(d_cicle / "index.md"))}">{escape(m_cicle["title"])}</a>'
            f' <span class="cicle-subtitol">{escape(m_cicle.get("description", ""))}</span></h3>'
        )
        blocs.append(_graella(_targetes_moduls(d_cicle, m_cicle, enllac)))
    return "\n".join(blocs)


def _llistat_moduls(carpeta: Path, enllac) -> str:
    targetes = _targetes_moduls(carpeta, _meta(carpeta / "index.md"), enllac)
    if not targetes:
        return '!!! info "Encara no hi ha mòduls en aquest cicle."'
    return _graella(targetes)


def _llistat_ras(carpeta: Path) -> str:
    ras = [r for r in _subcarpetes_amb_index(carpeta) if r.name.startswith("ra")]
    if not ras:
        return '!!! info "Encara no hi ha resultats d\'aprenentatge definits."'
    linies = ["| RA | Resultat d'aprenentatge | Material |", "| --- | --- | :---: |"]
    for r in sorted(ras, key=_numero_ra):
        meta = _meta(r / "index.md")
        n = len(_materials(r))
        titol = meta["title"].split("·", 1)[-1].strip()
        linies.append(f"| [RA{_numero_ra(r)}]({r.name}/index.md) | {titol} | {f'**{n}**' if n else '—'} |")
    return "\n".join(linies)


def _llistat_material(carpeta: Path, enllac) -> str:
    fitxers = _materials(carpeta)
    if not fitxers:
        return '!!! info "Encara no hi ha material publicat per a aquest RA."\n\n    Torna-hi més endavant.'
    targetes = []
    for f in fitxers:
        meta = _meta(f)
        tipus = TIPUS.get(str(meta.get("tipus", "")).lower(), "")
        ets = ([_etiqueta(tipus, "card-etiqueta-tipus")] if tipus else []) + [_etiqueta(t) for t in meta.get("tags") or []]
        targetes.append(_targeta(meta["title"], enllac(f), meta.get("description", ""), ets))
    return _graella(targetes)


def on_page_markdown(markdown, page, config, files, **kwargs):
    if "<!-- llistat-" not in markdown and "<!-- cataleg -->" not in markdown:
        return markdown
    docs = Path(config["docs_dir"])
    carpeta = (docs / page.file.src_uri).parent
    enllac = Enllacos(docs, page, files)
    substitucions = {
        "<!-- cataleg -->": lambda: _cataleg(docs, enllac),
        "<!-- llistat-cicles -->": lambda: _llistat_cicles(docs, enllac),
        "<!-- llistat-moduls -->": lambda: _llistat_moduls(carpeta, enllac),
        "<!-- llistat-ras -->": lambda: _llistat_ras(carpeta),
        "<!-- llistat-material -->": lambda: _llistat_material(carpeta, enllac),
    }
    for marcador, genera in substitucions.items():
        if marcador in markdown:
            markdown = markdown.replace(marcador, genera())
    return markdown
