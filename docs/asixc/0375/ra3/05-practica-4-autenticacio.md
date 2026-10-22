---
title: "Pràctica 4: autenticació i control d'accés"
description: Protegir la intranet amb usuaris, grups i restriccions per IP, i comprovar per què Basic necessita HTTPS.
tipus: practica
tags:
  - Servidors web
  - Apache
  - Ciberseguretat
  - Wireshark
---

# Pràctica 4: autenticació i control d'accés

!!! abstract "Objectius"

    - Protegir llocs i directoris amb autenticació HTTP Basic i Digest.
    - Combinar usuaris, grups i adreces IP amb `Require`, `RequireAll` i `RequireAny`.
    - Comparar la configuració central amb els fitxers `.htaccess`.
    - Demostrar per què l'autenticació Basic sense HTTPS és insegura.

    **Criteri d'avaluació:** 5 · **Durada orientativa:** 3 h · **Prerequisit:** [pràctica 2](03-practica-2-hosts-virtuals.md)

## Requisits de la intranet

| Zona | URL | Qui hi pot accedir |
| --- | --- | --- |
| Intranet general | `http://intranet.empresa.test/` | Qualsevol empleat autenticat |
| Administració | `http://intranet.empresa.test/admin/` | Només el grup `admins`, **i** des de la xarxa 192.168.56.0/24 |
| Documents públics | `http://intranet.empresa.test/publics/` | Tothom, sense contrasenya |

## Pas 1. Usuaris i grups

Els fitxers de credencials van en un directori **fora del `DocumentRoot`**:

```bash
sudo mkdir -p /etc/apache2/auth
sudo htpasswd -c /etc/apache2/auth/usuaris anna     # -c crea el fitxer: només la primera vegada!
sudo htpasswd /etc/apache2/auth/usuaris joan
sudo htpasswd /etc/apache2/auth/usuaris marta
sudo cat /etc/apache2/auth/usuaris
```

!!! question "Observeu"

    Com es desen les contrasenyes? Per què comencen per `$apr1$` o `$2y$`?

Creeu el fitxer de grups:

```text title="/etc/apache2/auth/grups"
admins: marta
empleats: anna joan marta
```

Protegiu els fitxers perquè només els pugui llegir Apache:

```bash
sudo chown root:www-data /etc/apache2/auth/*
sudo chmod 640 /etc/apache2/auth/*
sudo a2enmod authz_groupfile
```

## Pas 2. Contingut

```bash
sudo mkdir -p /var/www/intranet/admin /var/www/intranet/publics
echo "<h1>Administració</h1>"      | sudo tee /var/www/intranet/admin/index.html
echo "<h1>Documents públics</h1>"  | sudo tee /var/www/intranet/publics/index.html
```

## Pas 3. Configuració al host virtual

Substituïu el bloc `<Directory>` de `intranet.conf`:

```apache title="/etc/apache2/sites-available/intranet.conf (fragment)"
<Directory /var/www/intranet>
    Options -Indexes
    AllowOverride None

    AuthType Basic
    AuthName "Intranet de l'empresa"
    AuthUserFile  /etc/apache2/auth/usuaris
    AuthGroupFile /etc/apache2/auth/grups
    Require valid-user
</Directory>

<Directory /var/www/intranet/admin>
    <RequireAll>
        Require group admins
        Require ip 192.168.56.0/24
    </RequireAll>
</Directory>

<Directory /var/www/intranet/publics>
    Require all granted
</Directory>
```

```bash
sudo apache2ctl configtest && sudo systemctl reload apache2
```

## Pas 4. Proves

Des del client, completeu la taula provant amb el navegador (feu servir una finestra privada per a cada usuari) i amb `curl`:

```bash
curl -i http://intranet.empresa.test/
curl -i -u anna  http://intranet.empresa.test/
curl -i -u anna  http://intranet.empresa.test/admin/
curl -i -u marta http://intranet.empresa.test/admin/
curl -i          http://intranet.empresa.test/publics/
```

| Prova | Codi esperat | Codi obtingut |
| --- | --- | --- |
| `/` sense credencials | 401 | |
| `/` com a `anna` | 200 | |
| `/admin/` com a `anna` | 401 | |
| `/admin/` com a `marta` | 200 | |
| `/publics/` sense credencials | 200 | |
| `/` amb contrasenya incorrecta | 401 | |

Ara proveu `/admin/` com a `marta` canviant la xarxa: substituïu temporalment `Require ip 192.168.56.0/24` per una xarxa que no sigui la vostra i comproveu que, tot i tenir la contrasenya correcta, l'accés es denega. **Torneu a deixar-ho bé.**

Mireu com queden reflectits els intents al registre:

```bash
sudo tail -n 10 /var/log/apache2/intranet_access.log
sudo tail -n 10 /var/log/apache2/intranet_error.log
```

## Pas 5. El mateix amb `.htaccess`

Creeu un directori `/var/www/intranet/rrhh` protegit només per a `anna`, però aquesta vegada amb un fitxer `.htaccess`:

```apache title="/var/www/intranet/rrhh/.htaccess"
AuthType Basic
AuthName "Recursos humans"
AuthUserFile /etc/apache2/auth/usuaris
Require user anna
```

Proveu-ho. Funciona? Afegiu al host virtual un bloc que permeti els `.htaccess` només en aquest directori:

```apache
<Directory /var/www/intranet/rrhh>
    AllowOverride AuthConfig
</Directory>
```

## Pas 6. Per què Basic necessita HTTPS

Al servidor, captureu el trànsit HTTP mentre des del client accediu a la intranet:

```bash
sudo tcpdump -l -i any -A -n 'tcp port 80' | grep -i "authorization"
```

```bash
curl -u anna http://intranet.empresa.test/        # des del client
```

Copieu el valor que apareix després de `Authorization: Basic` i descodifiqueu-lo:

```bash
echo 'VALOR_CAPTURAT' | base64 -d
```

!!! danger "Conclusió"

    Base64 és una **codificació**, no un xifratge. Qualsevol persona a la xarxa pot llegir les credencials. Ho solucionarem a la [pràctica 5](06-practica-5-https.md).

## Pas 7. Comparació amb Digest

```bash
sudo a2enmod auth_digest
sudo htdigest -c /etc/apache2/auth/digest "Zona digest" joan
sudo chown root:www-data /etc/apache2/auth/digest && sudo chmod 640 /etc/apache2/auth/digest
sudo mkdir -p /var/www/intranet/digest
echo "<h1>Zona Digest</h1>" | sudo tee /var/www/intranet/digest/index.html
```

```apache
<Directory /var/www/intranet/digest>
    AuthType Digest
    AuthName "Zona digest"
    AuthDigestDomain /digest/
    AuthUserFile /etc/apache2/auth/digest
    Require valid-user
</Directory>
```

Repetiu la captura del pas 6 amb `curl --digest -u joan http://intranet.empresa.test/digest/`. Què veieu ara a la capçalera `Authorization`?

## Preguntes

1. Quina diferència hi ha entre l'autenticació i l'autorització? Quines directives del pas 3 corresponen a cadascuna?
2. Per què els fitxers de contrasenyes no poden estar dins del `DocumentRoot`?
3. Què passaria si al bloc d'`admin` féssiu servir `<RequireAny>` en lloc de `<RequireAll>`?
4. Avantatges i inconvenients de `.htaccess` respecte de la configuració al host virtual.
5. Digest és més segur que Basic sobre HTTP, però avui es recomana Basic sobre HTTPS. Per què?

## Lliurament

`intranet.conf`, el fitxer de grups, la taula de proves completada, la captura del pas 6 amb la contrasenya descodificada, la comparació amb Digest i les respostes a les preguntes.
