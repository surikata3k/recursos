---
title: "Pràctica 6: registres i monitoratge"
description: Formats de registre propis, anàlisi amb awk i GoAccess, mod_status, proves de càrrega i detecció d'escanejos.
tipus: practica
tags:
  - Servidors web
  - Apache
  - Línia d'ordres
  - Ciberseguretat
---

# Pràctica 6: registres i monitoratge del servei

!!! abstract "Objectius"

    - Definir un format de registre propi amb el temps de resposta.
    - Analitzar els registres per obtenir estadístiques i detectar incidències i comportaments sospitosos.
    - Monitorar l'estat del servidor amb `mod_status` i fer proves de càrrega.
    - Comprovar periòdicament la disponibilitat del servei.

    **Criteris d'avaluació:** 8, 9 · **Durada orientativa:** 3 h · **Prerequisit:** [pràctica 5](06-practica-5-https.md)

## Pas 1. Un format de registre amb el temps de resposta

Creeu un fragment de configuració global:

```apache title="/etc/apache2/conf-available/registres.conf"
# host virtual, IP, usuari, data, petició, estat, mida, temps (µs), origen, client
LogFormat "%v %h %l %u %t \"%r\" %>s %b %D \"%{Referer}i\" \"%{User-Agent}i\"" ampliat
```

```bash
sudo a2enconf registres
```

Al `<VirtualHost *:443>` de `www.empresa.test`, **afegiu** una segona línia `CustomLog` (deixeu la que ja hi ha amb el format `combined`, que farem servir amb GoAccess):

```apache
CustomLog ${APACHE_LOG_DIR}/empresa_ampliat.log ampliat
```

```bash
sudo apache2ctl configtest && sudo systemctl reload apache2
```

## Pas 2. Generar trànsit

Des del client, executeu aquest script per generar peticions variades (correctes, errors, redireccions i autenticacions):

```bash title="trafic.sh"
#!/usr/bin/env bash
URL=https://www.empresa.test
for i in $(seq 1 200); do
  curl -s -o /dev/null "$URL/"
  curl -s -o /dev/null "$URL/actualitat/"
  curl -s -o /dev/null "$URL/noticies/"
  (( i % 5 == 0 )) && curl -s -o /dev/null "$URL/no-existeix-$i"
  (( i % 10 == 0 )) && curl -s -o /dev/null -u anna:incorrecta https://intranet.empresa.test/
done
echo "Fet"
```

```bash
bash trafic.sh
```

## Pas 3. Analitzar els registres amb la línia d'ordres

Al servidor, sobre `empresa_ampliat.log`. Recordeu la posició dels camps: `$2` és la IP, `$8` el camí, `$10` el codi d'estat i `$12` el temps en µs.

```bash
LOG=/var/log/apache2/empresa_ampliat.log

# Peticions per codi d'estat
sudo awk '{print $10}' $LOG | sort | uniq -c | sort -rn

# Les 10 IP que fan més peticions
sudo awk '{print $2}' $LOG | sort | uniq -c | sort -rn | head

# Les URL que donen més errors 404
sudo awk '$10 == 404 {print $8}' $LOG | sort | uniq -c | sort -rn | head

# Temps mitjà i màxim de resposta (en mil·lisegons)
sudo awk '{s+=$12; if ($12>m) m=$12} END {printf "mitjana %.2f ms, màxim %.2f ms\n", s/NR/1000, m/1000}' $LOG

# Peticions per minut
sudo awk '{print substr($5, 2, 17)}' $LOG | uniq -c | tail
```

I al registre d'accessos de la intranet, els intents d'autenticació fallits:

```bash
sudo awk '$9 == 401 {print $1}' /var/log/apache2/intranet_access.log | sort | uniq -c | sort -rn
sudo grep -i "password mismatch\|not found" /var/log/apache2/intranet_error.log | tail
```

## Pas 4. Informe gràfic amb GoAccess

```bash
sudo apt install -y goaccess
sudo goaccess /var/log/apache2/empresa_access.log --log-format=COMBINED -o /tmp/informe.html
```

Copieu `/tmp/informe.html` al client i obriu-lo amb el navegador. Identifiqueu-hi els visitants, les pàgines més demanades, els codis d'estat i els 404.

!!! tip "En directe"

    `sudo goaccess /var/log/apache2/empresa_access.log --log-format=COMBINED` mostra el mateix informe al terminal, actualitzat en temps real.

## Pas 5. Estat del servidor amb `mod_status`

```bash
sudo a2enmod status          # a Ubuntu ja ve activat
cat /etc/apache2/mods-enabled/status.conf
```

Per defecte només es pot consultar des del mateix servidor (`Require local`). Feu-la accessible **només** des del client, dins del `<VirtualHost *:443>` de `www.empresa.test`:

```apache
<Location /server-status>
    SetHandler server-status
    Require ip 192.168.56.20
</Location>
```

```bash
sudo apache2ctl configtest && sudo systemctl reload apache2
```

Obriu `https://www.empresa.test/server-status?refresh=2` al client. Proveu també la versió per a scripts: `curl -s https://www.empresa.test/server-status?auto`.

!!! warning "Seguretat"

    La pàgina d'estat mostra les URL que s'estan servint i les IP dels clients. Mai no ha de ser pública. Comproveu des d'una altra IP (o canviant temporalment la del `Require`) que es denega l'accés.

## Pas 6. Proves de càrrega

Des del client (`apache2-utils` inclou `ab`), mentre teniu oberta la pàgina d'estat:

```bash
sudo apt install -y apache2-utils
ab -n 2000 -c 10  https://www.empresa.test/
ab -n 2000 -c 100 https://www.empresa.test/
```

Completeu la taula:

| Concurrència | Peticions/s | Temps mitjà per petició | Peticions fallides | 95 % de les peticions en menys de |
| --- | --- | --- | --- | --- |
| 10 | | | | |
| 100 | | | | |

!!! danger "Només al laboratori"

    Una prova de càrrega contra un servidor que no és vostre és, a efectes pràctics, un atac de denegació de servei.

## Pas 7. Detectar un escaneig

Simuleu des del client el que faria una eina automàtica buscant fitxers sensibles:

```bash
for ruta in .env .git/config wp-login.php admin phpmyadmin backup.zip config.php server-status; do
  curl -s -o /dev/null -w "%{http_code} /$ruta\n" "https://www.empresa.test/$ruta"
done
```

Al servidor, localitzeu-ho als registres: quina IP ha generat més 404 en poc temps? Quines rutes ha provat?

```bash
sudo awk '$10 == 404 {print $2, $8}' /var/log/apache2/empresa_ampliat.log | tail -20
```

Investigueu com `fail2ban` podria bloquejar automàticament aquesta IP (no cal implementar-ho).

## Pas 8. Comprovació periòdica de disponibilitat

Un script senzill de monitoratge que es pot executar amb `cron` des del client:

```bash title="comprova-web.sh"
#!/usr/bin/env bash
for url in https://www.empresa.test/ https://intranet.empresa.test/publics/; do
  resultat=$(curl -s -o /dev/null -w "%{http_code} %{time_total}" --max-time 5 "$url")
  echo "$(date '+%F %T') $url $resultat" >> ~/monitoratge-web.log
done
```

```bash
chmod +x comprova-web.sh
crontab -e     # afegiu:  */1 * * * * /home/USUARI/comprova-web.sh
```

Atureu Apache uns minuts (`sudo systemctl stop apache2`), torneu-lo a engegar i observeu què ha quedat registrat a `~/monitoratge-web.log`.

## Pas 9. Registre d'errors i rotació

Augmenteu temporalment el detall del registre d'errors per a un sol mòdul, per depurar les regles de reescriptura:

```apache
LogLevel warn rewrite:trace3
```

Feu una petició a `/noticies/` i mireu `empresa_error.log`. **Torneu a deixar `LogLevel warn`**: el nivell `trace` genera moltíssimes línies.

Finalment, reviseu la política de rotació:

```bash
cat /etc/logrotate.d/apache2
ls -l /var/log/apache2/
```

## Preguntes

1. Quins avantatges té afegir `%D` i `%v` al format de registre?
2. Amb les dades del pas 3, quin percentatge de peticions han acabat en error (4xx o 5xx)?
3. Com ha canviat el rendiment entre concurrència 10 i 100? On podria estar el coll d'ampolla?
4. Quins indicis del pas 7 permeten distingir un escaneig automàtic d'un usuari normal?
5. Per què els registres són dades personals? Quines mesures s'haurien d'aplicar segons l'RGPD?
6. Quina diferència hi ha entre el monitoratge del pas 5 i el del pas 8? Quin detectaria una caiguda del servidor?

## Lliurament

`registres.conf`, la sortida de les ordres del pas 3, l'informe de GoAccess, captures de `server-status`, la taula del pas 6, el fitxer `monitoratge-web.log` i respostes a les preguntes.
