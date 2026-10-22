---
title: "Activitat final: desplegament web segur"
description: Projecte integrador del RA3 per a una empresa fictícia, amb documentació tècnica i rúbrica d'avaluació.
tipus: activitat
tags:
  - Servidors web
  - Apache
  - Nginx
  - HTTPS
  - Ciberseguretat
---

# Activitat final: desplegament web segur per a Ebre Logística

!!! abstract "Plantejament"

    Treballeu com a tècnics de sistemes d'una consultora. L'empresa **Ebre Logística SL** us ha encarregat la posada en marxa i la documentació de la seva infraestructura web. Heu d'aplicar tot el que heu après al RA3 en un escenari nou, des de zero, i lliurar-ne la documentació tècnica.

    **Criteris d'avaluació:** tots (1–10) · **Modalitat:** individual · **Durada orientativa:** 8 h

## Escenari

Partiu de màquines netes (no reutilitzeu les de les pràctiques):

| Màquina | Funció |
| --- | --- |
| `ebre-proxy` | Nginx: punt d'entrada únic des de l'exterior, terminació TLS |
| `ebre-web` | Apache: servidor dels llocs |
| `client` | Proves |

Domini: **`ebrelogistica.test`**. Trieu vosaltres l'adreçament de la xarxa interna i justifiqueu-lo.

## Requisits

### Llocs web

| Lloc | Contingut | Accés |
| --- | --- | --- |
| `www.ebrelogistica.test` | Web corporativa (mínim tres pàgines) | Públic |
| `clients.ebrelogistica.test` | Portal de seguiment d'enviaments (pot ser estàtic) | Usuaris del grup `clients` |
| `clients.ebrelogistica.test/gestio/` | Zona de gestió | Grup `gestors` **i** només des de la xarxa interna |
| `intern.ebrelogistica.test` | Pàgina d'estat del servidor (`mod_status`) | Només des de l'equip d'administració |

### Requisits tècnics

1. Tot el trànsit ha de ser **HTTPS** (TLS 1.2 i 1.3) amb certificats emesos per una **CA pròpia** d'Ebre Logística. Les peticions HTTP es redirigeixen a HTTPS.
2. El **proxy Nginx** és l'únic punt d'entrada. `ebre-web` no ha d'acceptar connexions que no vinguin del proxy.
3. Apache ha de registrar la **IP real** dels clients.
4. `ebrelogistica.test` sense `www` redirigeix a `www`, i l'antiga adreça `/tarifes.html` redirigeix permanentment a `/preus/`.
5. **Bastionat**: sense versions a les capçaleres, sense llistats de directoris, `TRACE` desactivat, capçaleres de seguretat (HSTS, `nosniff`, protecció contra *clickjacking*, `Referrer-Policy`) i només els mòduls necessaris.
6. **Registres** separats per lloc, amb un format que inclogui el temps de resposta.
7. Un **script de monitoratge** que comprovi cada minut que els tres llocs responen i en registri el codi i el temps.

## Proves que heu de demostrar

- [ ] Cada lloc respon amb el contingut correcte i amb un certificat vàlid (sense avisos al navegador del client).
- [ ] Les redireccions HTTP → HTTPS, sense `www` → amb `www` i `/tarifes.html` → `/preus/` funcionen i tornen 301.
- [ ] Taula de proves d'accés al portal de clients i a la zona de gestió (usuaris correctes, incorrectes, sense credencials, des de dins i des de fora).
- [ ] Accés directe a `ebre-web` des del client denegat.
- [ ] La IP real del client apareix als registres d'Apache, i una capçalera `X-Forwarded-For` falsificada no s'accepta.
- [ ] Versions de TLS antigues rebutjades (`curl --tls-max 1.1` o `nmap --script ssl-enum-ciphers`).
- [ ] Prova de càrrega amb `ab` i interpretació dels resultats.
- [ ] Anàlisi dels registres: peticions per codi d'estat, IP més actives, 404 més freqüents, temps mitjà de resposta.

## Lliurament

1. **Document tècnic** (PDF) amb aquesta estructura:
    1. Introducció i esquema de la infraestructura.
    2. Fonaments: HTTP, HTTPS i el paper de cada component (proxy, servidor, CA).
    3. Instal·lació i configuració, pas a pas, de cada servei.
    4. Certificats: creació de la CA, emissió i instal·lació.
    5. Seguretat aplicada i justificació de cada mesura.
    6. Proves realitzades amb les evidències (captures i sortides d'ordres).
    7. Monitoratge i anàlisi dels registres.
    8. **Recomanacions d'ús i manteniment** per a l'equip d'Ebre Logística: renovació de certificats, alta i baixa d'usuaris, actualitzacions, revisió de registres.
2. **Fitxers de configuració** finals en un ZIP: llocs d'Apache, configuració de Nginx, `security.conf`, `ssl.conf`, scripts.
3. **Defensa oral** de 10 minuts amb demostració en directe.

## Rúbrica

| Criteri | Excel·lent (4) | Notable (3) | Suficient (2) | Insuficient (1) |
| --- | --- | --- | --- | --- |
| **1. Fonaments i protocols** | Explica HTTP, TLS i el paper de cada component amb precisió i ho relaciona amb la seva configuració | Explicació correcta i completa | Explicació correcta però superficial | Explicació absent o amb errors greus |
| **2. Instal·lació i configuració** | Apache i Nginx funcionen sense errors, configuració neta i comentada | Funcionen amb petites mancances | Funcionen parcialment | No funcionen |
| **3. Mòduls** | Només els mòduls necessaris, tots justificats; `rewrite`, `headers`, `ssl`, `remoteip` i `status` ben configurats | Mòduls correctes amb alguna mancança de justificació | La majoria funcionen | Mòduls absents o mal configurats |
| **4. Llocs virtuals** | Tots els llocs funcionen, amb registres separats i lloc per defecte segur | Tots els llocs funcionen | Funcionen la majoria | Menys de la meitat funcionen |
| **5. Autenticació i control d'accés** | Tots els requisits complerts i taula de proves exhaustiva | Requisits complerts, proves incompletes | Falla un requisit | Fallen diversos requisits |
| **6. Certificats** | CA i certificats correctes (SAN, permisos), CA instal·lada al client, sense avisos | Certificats correctes amb petites mancances | Funciona HTTPS però amb avisos | Sense HTTPS |
| **7. Comunicacions segures** | Només TLS 1.2/1.3, redireccions, HSTS, proxy→backend xifrat i backend tancat | Falta una mesura | Falten diverses mesures | Comunicacions no protegides |
| **8. Monitoratge** | `mod_status` restringit, script de monitoratge amb cron i prova de càrrega ben interpretada | Tot funciona, interpretació justa | Falta un element | No hi ha monitoratge |
| **9. Anàlisi de registres** | Format propi, anàlisi completa i conclusions sobre rendiment i seguretat | Anàlisi completa sense conclusions | Anàlisi parcial | Sense anàlisi |
| **10. Documentació** | Document clar, complet i reproduïble per un tercer; recomanacions d'ús útils | Complet amb petites mancances | Incomplet però comprensible | Absent o incomprensible |

La nota de l'activitat és la mitjana dels deu criteris, sobre 4, convertida a escala de 10.
