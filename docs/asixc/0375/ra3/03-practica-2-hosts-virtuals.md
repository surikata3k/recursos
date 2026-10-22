---
title: "Pràctica 2: hosts virtuals"
description: Diversos llocs web en un mateix servidor, per nom i per port, i un lloc per defecte segur.
tipus: practica
tags:
  - Servidors web
  - Apache
  - DNS
---

# Pràctica 2: hosts virtuals

!!! abstract "Objectius"

    - Servir diversos llocs web des del mateix servidor Apache.
    - Configurar hosts virtuals **per nom** i **per port**.
    - Entendre com tria Apache el host virtual i configurar un lloc per defecte segur.

    **Criteri d'avaluació:** 4 · **Durada orientativa:** 2 h · **Prerequisit:** [pràctica 1](02-practica-1-installacio-apache.md)

## Llocs que crearem

| Lloc | Tipus | Arrel de documents | Accés |
| --- | --- | --- | --- |
| `www.empresa.test` (i `empresa.test`) | Per nom | `/var/www/empresa` | Port 80 |
| `intranet.empresa.test` | Per nom | `/var/www/intranet` | Port 80 |
| `proves.empresa.test` | Per port | `/var/www/proves` | Port 8080 |
| Lloc per defecte | Qualsevol altre nom o la IP | `/var/www/defecte` | Port 80 |

## Pas 1. Resolució de noms al client

Perquè el client trobi els noms, afegiu-los al `/etc/hosts` del `client`:

```text title="/etc/hosts (client)"
192.168.56.10   www.empresa.test empresa.test intranet.empresa.test proves.empresa.test
```

!!! tip "Amb el DNS del RA1"

    Si teniu el servidor BIND del [RA1](../ra1/index.md), és millor crear la zona `empresa.test` amb un registre `A` per a `www` i registres `CNAME` per als altres noms, i fer que el client el faci servir com a DNS.

Comproveu-ho: `getent hosts www.empresa.test`.

## Pas 2. Contingut dels llocs

A `srv-web`:

```bash
for lloc in empresa intranet proves defecte; do
  sudo mkdir -p /var/www/$lloc
  echo "<!doctype html><html lang=\"ca\"><head><meta charset=\"utf-8\"><title>$lloc</title></head><body><h1>Lloc: $lloc</h1></body></html>" \
    | sudo tee /var/www/$lloc/index.html > /dev/null
done
ls -l /var/www/
```

## Pas 3. Hosts virtuals per nom

```apache title="/etc/apache2/sites-available/empresa.conf"
<VirtualHost *:80>
    ServerName www.empresa.test
    ServerAlias empresa.test
    DocumentRoot /var/www/empresa

    <Directory /var/www/empresa>
        Options -Indexes
        AllowOverride None
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/empresa_error.log
    CustomLog ${APACHE_LOG_DIR}/empresa_access.log combined
</VirtualHost>
```

Creeu `intranet.conf` de la mateixa manera, canviant el nom, l'arrel i els noms dels registres. Activeu-los:

```bash
sudo a2ensite empresa.conf intranet.conf
sudo apache2ctl configtest
sudo systemctl reload apache2
```

Des del client, obriu `http://www.empresa.test`, `http://empresa.test` i `http://intranet.empresa.test`.

## Pas 4. Host virtual per port

Feu que Apache escolti també al port 8080 afegint `Listen 8080` a `/etc/apache2/ports.conf`, i creeu el lloc:

```apache title="/etc/apache2/sites-available/proves.conf"
<VirtualHost *:8080>
    ServerName proves.empresa.test
    DocumentRoot /var/www/proves

    <Directory /var/www/proves>
        Options -Indexes
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/proves_error.log
    CustomLog ${APACHE_LOG_DIR}/proves_access.log combined
</VirtualHost>
```

```bash
sudo a2ensite proves.conf
sudo ufw allow 8080/tcp        # si UFW està actiu
sudo apache2ctl configtest && sudo systemctl reload apache2
```

Proveu `http://proves.empresa.test:8080`.

## Pas 5. Un lloc per defecte segur

Quan arriba una petició amb un nom que cap host virtual no reconeix (o directament amb la IP), Apache respon amb el **primer** host virtual que ha carregat. Ara mateix és `000-default.conf`.

```bash
sudo apache2ctl -S
```

Modifiqueu `000-default.conf` perquè apunti a `/var/www/defecte` i no mostri la pàgina d'informació d'Ubuntu ni cap lloc real. Proveu-ho:

```bash
curl http://192.168.56.10/
curl -H "Host: inventat.empresa.test" http://192.168.56.10/
```

## Pas 6. La capçalera `Host` en acció

Des del client, sense passar pel navegador, podeu triar el lloc només canviant la capçalera:

```bash
curl -H "Host: www.empresa.test"      http://192.168.56.10/
curl -H "Host: intranet.empresa.test" http://192.168.56.10/
curl -H "Host: proves.empresa.test"   http://192.168.56.10/       # sense el port 8080!
```

!!! question "Observeu"

    Què passa amb l'última ordre? Per què?

## Ampliació: host virtual per IP

Afegiu una segona adreça a `srv-web` (`sudo ip addr add 192.168.56.12/24 dev enp0s8`, o permanentment amb Netplan) i creeu un host virtual `<VirtualHost 192.168.56.12:80>` amb un contingut diferent. Comproveu que, accedint per aquesta IP, sempre surt aquest lloc sigui quin sigui el nom.

## Preguntes

1. Expliqueu, amb la sortida d'`apache2ctl -S`, com decideix Apache quin host virtual atén cada petició.
2. Per què és important que el lloc per defecte no mostri el contingut d'un lloc real?
3. Quins avantatges té tenir registres separats per a cada host virtual?
4. Quina diferència hi ha entre `ServerName` i `ServerAlias`?
5. Quins inconvenients té fer servir hosts virtuals per port en un lloc públic?

## Lliurament

Fitxers de configuració dels quatre llocs, sortida d'`apache2ctl -S`, captures de les proves dels passos 3 a 6 i respostes a les preguntes.
