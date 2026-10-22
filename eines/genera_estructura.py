#!/usr/bin/env python3
"""Crea l'estructura de carpetes i pàgines a partir de eines/curriculum.yml.

Només crea el que encara no existeix: no sobreescriu cap fitxer, així que
el pots tornar a executar sempre que afegeixis un cicle, un mòdul o un RA.

    python3 eines/genera_estructura.py
"""
from pathlib import Path

import yaml

ARREL = Path(__file__).resolve().parent.parent
DOCS = ARREL / "docs"
DADES = ARREL / "eines" / "curriculum.yml"


def escriu_si_no_existeix(cami: Path, contingut: str, creats: list) -> None:
    if cami.exists():
        return
    cami.parent.mkdir(parents=True, exist_ok=True)
    cami.write_text(contingut, encoding="utf-8")
    creats.append(cami.relative_to(ARREL))


def cometes(text: str) -> str:
    return '"' + text.replace('"', '\\"') + '"'


def main() -> None:
    dades = yaml.safe_load(DADES.read_text(encoding="utf-8"))
    creats: list = []

    for ordre, cicle in enumerate(dades["cicles"], start=1):
        dir_cicle = DOCS / cicle["id"]
        escriu_si_no_existeix(
            dir_cicle / ".nav.yml",
            f"title: {cometes(cicle['nom'])}\n",
            creats,
        )
        escriu_si_no_existeix(
            dir_cicle / "index.md",
            "---\n"
            f"title: {cometes(cicle['nom'])}\n"
            f"description: {cometes(cicle['titol'])}\n"
            "nivell: cicle\n"
            f"ordre: {ordre}\n"
            f"icona: {cicle['icona']}\n"
            "---\n\n"
            f"# {cicle['nom']}\n\n"
            f"**{cicle['grau']} · {cicle['titol']}**\n\n"
            "<!-- llistat-moduls -->\n",
            creats,
        )

        for modul in cicle["moduls"]:
            codi, nom = modul["codi"], modul["nom"]
            dir_modul = dir_cicle / codi
            escriu_si_no_existeix(
                dir_modul / ".nav.yml",
                f"title: {cometes(f'{codi} · {nom}')}\n",
                creats,
            )
            escriu_si_no_existeix(
                dir_modul / "index.md",
                "---\n"
                f"title: {cometes(f'{codi} · {nom}')}\n"
                f"description: {cometes(nom)}\n"
                "nivell: modul\n"
                "---\n\n"
                f"# MP{codi} · {nom}\n\n"
                f"Mòdul professional del cicle **{cicle['nom']}** "
                f"({cicle['titol']}).\n\n"
                "## Resultats d'aprenentatge\n\n"
                "<!-- llistat-ras -->\n",
                creats,
            )

            for n, ra in enumerate(modul["ras"], start=1):
                dir_ra = dir_modul / f"ra{n}"
                titol_ra = f"RA{n} · {ra['curt']}"
                escriu_si_no_existeix(
                    dir_ra / ".nav.yml",
                    f"title: {cometes(titol_ra)}\n",
                    creats,
                )
                criteris = "\n".join(
                    f"    {i}. {c}" for i, c in enumerate(ra["criteris"], start=1)
                )
                escriu_si_no_existeix(
                    dir_ra / "index.md",
                    "---\n"
                    f"title: {cometes(titol_ra)}\n"
                    f"description: {cometes(ra['text'])}\n"
                    "nivell: ra\n"
                    "---\n\n"
                    f"# {titol_ra}\n\n"
                    f"!!! abstract \"Resultat d'aprenentatge {n}\"\n\n"
                    f"    {ra['text']}\n\n"
                    "??? info \"Criteris d'avaluació\"\n\n"
                    f"{criteris}\n\n"
                    "## Material\n\n"
                    "<!-- llistat-material -->\n",
                    creats,
                )

    if creats:
        print(f"S'han creat {len(creats)} fitxers:")
        for cami in creats:
            print(f"  {cami}")
    else:
        print("Tot l'estructura ja existia; no s'ha creat res.")


if __name__ == "__main__":
    main()
