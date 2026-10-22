# Recursos d'informàtica

Web de material didàctic dels cicles **SMX**, **ASIX** i **ASIX Ciberseguretat**, feta amb [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) i publicada a GitHub Pages:

**https://surikata3k.github.io/recursos/**

Cada cop que puges un canvi a la branca `main`, GitHub reconstrueix i publica la web sola en un o dos minuts.

---

## Com està organitzada

```text
docs/
├── index.md                  ← portada
├── temes.md                  ← índex per temàtiques (etiquetes)
├── smx/                      ← un cicle
│   ├── index.md
│   └── 0224/                 ← un mòdul (pel codi)
│       ├── index.md
│       └── ra1/              ← un resultat d'aprenentatge
│           ├── index.md      ← enunciat del RA i criteris (no cal tocar-lo)
│           ├── 01-teoria.md  ← el teu material
│           ├── 02-practica.md
│           └── fitxers/      ← PDF, plantilles, fitxers per descarregar
├── asix/
└── asixc/
```

Les pàgines de cicle, mòdul i RA ja existeixen per a tots els teus mòduls, amb els RA i criteris oficials. **Els llistats es generen sols**: quan deixes un fitxer `.md` a la carpeta d'un RA, apareix al menú, a la pàgina del RA i als comptadors del mòdul.

---

## Afegir material

1. Crea un fitxer `.md` a la carpeta del RA. Posa-li un número davant per ordenar-lo: `01-…`, `02-…`.
2. Comença'l amb aquesta capçalera:

    ```yaml
    ---
    title: "Pràctica: instal·lació de BIND9"
    description: Una frase que surt al llistat del RA.
    tipus: practica        # teoria | practica | activitat | solucions | recurs
    tags:
      - DNS
      - Linux
    ---
    ```

3. Escriu el contingut en Markdown i puja el canvi.

Mira el material del RA1 de 0375 (`docs/asixc/0375/ra1/`) com a exemple: hi tens teoria, pràctiques, solucions protegides i fitxers descarregables.

### Etiquetes (temàtiques)

Les etiquetes de `tags:` creen l'índex de [Temàtiques](https://surikata3k.github.io/recursos/temes/). Intenta reutilitzar sempre les mateixes: `DNS`, `Serveis de xarxa`, `Ciberseguretat`, `Línia d'ordres`, `Wireshark`, `Linux`, `Bases de dades`…

### Fitxers descarregables

Desa'ls a la subcarpeta `fitxers/` del RA i enllaça'ls així:

```markdown
[Descarrega la plantilla](fitxers/plantilla.odt)
```

### Elements útils

````markdown
```bash
dig @8.8.8.8 exemple.cat A
```

!!! warning "Seguretat"
    Text de l'avís.

??? question "Preguntes (desplegable)"
    1. Primera pregunta

=== "Linux"
    Contingut de la pestanya
=== "Windows"
    Contingut de la pestanya
````

Tipus d'avís disponibles: `note`, `abstract`, `info`, `tip`, `example`, `question`, `warning`, `danger`.

---

## Contingut protegit amb contrasenya

Afegeix `level:` a la capçalera:

```yaml
level: solucions   # o: examens
```

La pàgina es publica **xifrada**: l'alumnat la veu al menú, però el text només apareix si escriu la contrasenya, i no surt al cercador.

Les contrasenyes **no són al repositori**. Es guarden com a *secrets* de GitHub:

**Settings → Secrets and variables → Actions → New repository secret**

| Secret | Per a les pàgines amb |
| --- | --- |
| `CONTRASENYA_SOLUCIONS` | `level: solucions` |
| `CONTRASENYA_EXAMENS` | `level: examens` |

Per canviar una contrasenya (per exemple, a final de curs), edita el secret i torna a publicar (pestanya **Actions → Publica la web → Run workflow**).

> **Important:** el xifratge protegeix la web, però els fitxers `.md` originals tenen les solucions en clar. Per això el repositori ha de ser **privat**. Publicar GitHub Pages des d'un repositori privat requereix GitHub Pro, que és gratuït per a docents amb [GitHub Education](https://education.github.com/teachers).
>
> Els fitxers adjunts (PDF, ZIP…) **no es xifren**: posa les solucions dins la pàgina, no com a fitxer.

---

## Afegir un mòdul o un cicle nou

1. Afegeix-lo a `eines/curriculum.yml` (codi, nom i RA amb els seus criteris).
2. Executa:

    ```bash
    python3 eines/genera_estructura.py
    ```

    Crea només les carpetes i pàgines que falten; mai sobreescriu res.

---

## Configuració inicial (només un cop)

1. **Settings → Pages → Build and deployment → Source:** tria **GitHub Actions**.
2. Crea els dos secrets de contrasenya (vegeu més amunt).
3. Puja el contingut a `main`. A la pestanya **Actions** veuràs com es publica.

## Veure la web al teu ordinador abans de publicar

```bash
python3 -m venv .venv
source .venv/bin/activate        # a Windows: .venv\Scripts\activate
pip install -r requirements.txt
mkdocs serve
```

Obre http://127.0.0.1:8000. En local, la contrasenya de les solucions és `proves-local`.
