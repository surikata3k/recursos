---
title: "Pràctica 3: mòduls d'Apache"
description: Ampliar Apache amb mod_userdir, mod_rewrite i mod_headers, i reduir la superfície d'atac.
tipus: practica
tags:
  - Servidors web
  - Apache
  - Ciberseguretat
---

# Pràctica 3: ampliar Apache amb mòduls

!!! abstract "Objectius"

    - Gestionar els mòduls d'Apache: llistar, activar i desactivar.
    - Configurar pàgines personals (`mod_userdir`), redireccions (`mod_rewrite`) i capçaleres de seguretat (`mod_headers`).
    - Reduir la informació que el servidor revela.

    **Criteri d'avaluació:** 3 · **Durada orientativa:** 2 h · **Prerequisit:** [pràctica 2](03-practica-2-hosts-virtuals.md)

## Pas 1. Inventari de mòduls

```bash
apache2ctl -M                 # mòduls carregats
ls /etc/apache2/mods-available/
ls -l /etc/apache2/mods-enabled/
```

Fixeu-vos que cada mòdul té un fitxer `.load` (carrega el mòdul) i, de vegades, un `.conf` (la seva configuració). `a2enmod` només crea els enllaços a `mods-enabled/`.

## Pas 2. Pàgines personals amb `mod_userdir`

Volem que cada usuari del sistema pugui publicar una pàgina a `http://www.empresa.test/~usuari/`.

```bash
sudo a2enmod userdir
sudo systemctl reload apache2
cat /etc/apache2/mods-enabled/userdir.conf
```

Creeu un usuari de prova i la seva pàgina:

```bash
sudo adduser --gecos "" anna
sudo -u anna mkdir /home/anna/public_html
echo "<h1>Pàgina d'Anna</h1>" | sudo -u anna tee /home/anna/public_html/index.html
```

Proveu `http://www.empresa.test/~anna/`. Si obteniu un **403**, mireu el registre d'errors:

```bash
sudo tail -n 3 /var/log/apache2/empresa_error.log
ls -ld /home/anna
```

??? tip "Pista"

    A Ubuntu, els directoris personals es creen amb permisos `750`: l'usuari `www-data` no hi pot entrar. Necessita, com a mínim, permís d'execució (travessar) al directori personal: `sudo chmod 711 /home/anna`.

!!! warning "Seguretat"

    `mod_userdir` permet saber quins usuaris existeixen al sistema provant `/~nom/`. En un servidor de producció només s'hauria d'activar si és necessari, i amb `UserDir disabled root`.

## Pas 3. Redireccions amb `mod_rewrite`

L'empresa ha canviat l'adreça d'una secció: `/noticies/` ara és `/actualitat/`. Volem que els enllaços antics continuïn funcionant.

```bash
sudo a2enmod rewrite
sudo mkdir -p /var/www/empresa/actualitat
echo "<h1>Actualitat</h1>" | sudo tee /var/www/empresa/actualitat/index.html
```

Afegiu al host virtual `www.empresa.test`, dins de `<VirtualHost>`:

```apache
RewriteEngine On

# Redirecció permanent de la secció antiga
RewriteRule ^/noticies/?(.*)$ /actualitat/$1 [R=301,L]

# Unificar el domini: empresa.test → www.empresa.test
RewriteCond %{HTTP_HOST} ^empresa\.test$ [NC]
RewriteRule ^/(.*)$ http://www.empresa.test/$1 [R=301,L]
```

```bash
sudo apache2ctl configtest && sudo systemctl reload apache2
curl -I http://www.empresa.test/noticies/
curl -I http://empresa.test/contacte
```

!!! question "Observeu"

    Quin codi d'estat torna i quina capçalera indica el nou destí?

## Pas 4. Capçaleres de seguretat amb `mod_headers`

```bash
sudo a2enmod headers
```

Afegiu al host virtual `www.empresa.test`:

```apache
Header always set X-Content-Type-Options "nosniff"
Header always set X-Frame-Options "SAMEORIGIN"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
```

Comproveu-ho amb `curl -I http://www.empresa.test/` i amb les eines de desenvolupament del navegador (pestanya Xarxa).

## Pas 5. Que el servidor parli menys

Abans de canviar res, mireu què revela:

```bash
curl -I http://www.empresa.test/
curl http://www.empresa.test/no-existeix
```

Editeu `/etc/apache2/conf-available/security.conf`. A Ubuntu, `ServerTokens` val `OS` i `ServerSignature`, `On`; canvieu-los:

```apache
ServerTokens Prod
ServerSignature Off
# A Ubuntu, TraceEnable ja ve desactivat per defecte: comproveu-ho
TraceEnable Off
```

Recarregueu i torneu a fer les dues proves. Proveu també el mètode `TRACE` (ha de tornar **405**):

```bash
curl -X TRACE -i http://www.empresa.test/
```

## Pas 6. Desactivar el que no cal

Desactiveu un mòdul que no necessiteu (per exemple `autoindex`, que genera llistats de directoris):

```bash
sudo a2dismod autoindex
sudo apache2ctl configtest && sudo systemctl reload apache2
```

!!! note "`-f` per a mòduls essencials"

    `a2dismod` demana confirmació si el mòdul és crític. Si la configuració fa servir directives d'un mòdul desactivat, `configtest` donarà error: així sabreu de què depèn.

## Preguntes

1. Quina diferència hi ha entre una redirecció **301** i una **302**? Quina afecta els cercadors i les memòries cau?
2. Què fa el flag `[L]` en una `RewriteRule`? I `[NC]` en una `RewriteCond`?
3. Expliqueu de quin atac protegeix cadascuna de les tres capçaleres del pas 4.
4. Per què desactivar mòduls que no es fan servir millora la seguretat?
5. Compareu la capçalera `Server` i la pàgina d'error 404 abans i després del pas 5.

## Lliurament

Configuració final del host virtual `www.empresa.test`, fitxer `security.conf`, captures de les proves i respostes a les preguntes.
