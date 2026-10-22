"""Genera automàticament els llistats de la web.

Substitueix aquests marcadors quan MkDocs construeix la pàgina:

  <!-- llistat-cicles -->    targetes dels cicles (portada)
  <!-- llistat-moduls -->    targetes dels mòduls d'un cicle
  <!-- llistat-ras -->       taula dels RA d'un mòdul, amb el nombre de materials
  <!-- llistat-material -->  material d'un RA (els .md de la mateixa carpeta)

Així, per publicar material nou només cal deixar un fitxer .md a la carpeta
del RA: apareixerà sol al menú, al llistat del RA i als comptadors.
"""
from pathlib import Path

from mkdocs.utils.meta import get_data

TIPUS = {
    "teoria": (":material-book-open-variant:", "Teoria"),
    "practica": (":material-console:", "Pràctica"),
    "activitat": (":material-pencil-outline:", "Activitat"),
    "solucions": (":material-check-circle-outline:", "Solucions"),
    "recurs": (":material-paperclip:", "Recurs"),
}


def _meta(cami: Path) -> dict:
    text = cami.read_text(encoding="utf-8")
    cos, meta = get_data(text)
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
    return sorted(
        p for p in carpeta.rglob("*.md") if p.name != "index.md"
    )


def _subcarpetes_amb_index(carpeta: Path) -> list:
    return sorted(
        d for d in carpeta.iterdir() if d.is_dir() and (d / "index.md").exists()
    )


def _numero_ra(carpeta: Path) -> int:
    try:
        return int(carpeta.name.removeprefix("ra"))
    except ValueError:
        return 999


def _plural(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _targetes(elements: list) -> str:
    linies = ['<div class="grid cards" markdown>', ""]
    for icona, titol, subtitol, detall, enllac in elements:
        linies += [
            f"-   :{icona.replace('/', '-')}:{{ .lg .middle }} **{titol}**",
            "",
            "    ---",
            "",
            f"    {subtitol}",
            "",
            f"    <small>{detall}</small>",
            "",
            f"    [:octicons-arrow-right-24: Entra]({enllac})",
            "",
        ]
    linies.append("</div>")
    return "\n".join(linies)


def _llistat_cicles(docs: Path) -> str:
    cicles = []
    for d in _subcarpetes_amb_index(docs):
        meta = _meta(d / "index.md")
        if meta.get("nivell") == "cicle":
            cicles.append((meta.get("ordre", 99), d, meta))
    elements = []
    for _, d, meta in sorted(cicles, key=lambda c: (c[0], c[1].name)):
        moduls = _subcarpetes_amb_index(d)
        elements.append((
            meta.get("icona", "material/school"),
            meta["title"],
            meta.get("description", ""),
            f"{_plural(len(moduls), 'mòdul', 'mòduls')} · "
            f"{_plural(len(_materials(d)), 'material', 'materials')}",
            f"{d.name}/index.md",
        ))
    return _targetes(elements)


def _llistat_moduls(carpeta: Path) -> str:
    elements = []
    for d in _subcarpetes_amb_index(carpeta):
        meta = _meta(d / "index.md")
        ras = [r for r in _subcarpetes_amb_index(d) if r.name.startswith("ra")]
        elements.append((
            "material/folder-outline",
            meta["title"],
            "",
            f"{_plural(len(ras), 'RA', 'RA')} · "
            f"{_plural(len(_materials(d)), 'material', 'materials')}",
            f"{d.name}/index.md",
        ))
    if not elements:
        return '!!! info "Encara no hi ha mòduls en aquest cicle."'
    return _targetes(elements)


def _llistat_ras(carpeta: Path) -> str:
    ras = [r for r in _subcarpetes_amb_index(carpeta) if r.name.startswith("ra")]
    if not ras:
        return '!!! info "Encara no hi ha resultats d\'aprenentatge definits."'
    linies = ["| RA | Resultat d'aprenentatge | Material |", "| --- | --- | :---: |"]
    for r in sorted(ras, key=_numero_ra):
        meta = _meta(r / "index.md")
        n = len(_materials(r))
        titol = meta["title"].split("·", 1)[-1].strip()
        material = f"**{n}**" if n else "—"
        linies.append(
            f"| [RA{_numero_ra(r)}]({r.name}/index.md) | {titol} | {material} |"
        )
    return "\n".join(linies)


def _llistat_material(carpeta: Path) -> str:
    fitxers = _materials(carpeta)
    if not fitxers:
        return (
            '!!! info "Encara no hi ha material publicat per a aquest RA."\n\n'
            "    Torna-hi més endavant."
        )
    linies = []
    for f in fitxers:
        meta = _meta(f)
        icona, etiqueta = TIPUS.get(str(meta.get("tipus", "")).lower(), TIPUS["recurs"])
        enllac = f.relative_to(carpeta).as_posix()
        linia = f"- {icona} [{meta['title']}]({enllac}) <small>· {etiqueta}</small>"
        if meta.get("description"):
            linia += f"  \n  <small>{meta['description']}</small>"
        linies.append(linia)
    return "\n".join(linies)


def on_page_markdown(markdown, page, config, files, **kwargs):
    if "<!-- llistat-" not in markdown:
        return markdown
    docs = Path(config["docs_dir"])
    carpeta = (docs / page.file.src_uri).parent
    substitucions = {
        "<!-- llistat-cicles -->": lambda: _llistat_cicles(docs),
        "<!-- llistat-moduls -->": lambda: _llistat_moduls(carpeta),
        "<!-- llistat-ras -->": lambda: _llistat_ras(carpeta),
        "<!-- llistat-material -->": lambda: _llistat_material(carpeta),
    }
    for marcador, genera in substitucions.items():
        if marcador in markdown:
            markdown = markdown.replace(marcador, genera())
    return markdown
