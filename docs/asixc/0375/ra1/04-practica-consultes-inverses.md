---
title: "Pràctica: consultes inverses"
description: De nom a IP i d'IP a nom; comprovació FCrDNS d'un servidor de correu i captura amb Wireshark.
tipus: practica
tags:
  - DNS
  - Línia d'ordres
  - Wireshark
---

# Pràctica: consultes inverses d'un domini

!!! abstract "Objectiu"

    Partint d'un nom de domini, obtenir-ne les adreces IP i fer la consulta inversa per veure si el PTR coincideix amb el nom original.

    Repassa abans la teoria: [Zones inverses](01-dns-en-profunditat.md#9-zones-inverses).

Substituïu `<domini>` pel domini assignat (per exemple, `wikipedia.org`).

## Pas 1. Obtenir l'adreça IP del domini (consulta directa)

```bash
dig <domini> A +short
dig <domini> AAAA +short
```

## Pas 2. Consulta inversa de l'IPv4

```bash
dig -x <IPv4> +short
host <IPv4>
nslookup <IPv4>
```

Fixeu-vos que `dig -x` construeix automàticament el nom `…in-addr.arpa` i demana un registre PTR. Comproveu-ho:

```bash
dig <octet4>.<octet3>.<octet2>.<octet1>.in-addr.arpa PTR +noall +answer
```

És equivalent a `dig -x`, amb els octets de la IP en ordre invers.

## Pas 3. Consulta inversa de l'IPv6

```bash
dig -x <IPv6> +short
```

Observeu el nom llarg sota `ip6.arpa` que s'ha generat (32 nibbles invertits separats per punts).

## Pas 4. Recorregut de la consulta inversa des de l'arrel

```bash
dig +trace -x <IPv4>
```

Identifiqueu els salts: arrel → `arpa.` → `in-addr.arpa.` → registre regional d'Internet (RIR) → ISP/propietari del bloc. Compareu-ho amb el recorregut d'una consulta directa i comenteu la diferència (qui gestiona cada zona).

## Pas 5. Servidor de correu: comprovació FCrDNS

La comprovació FCrDNS (*forward-confirmed reverse DNS*) verifica que el nom i la IP del servidor de correu «es confirmen» en tots dos sentits.

```bash
dig <domini> MX +short            # obtenir el servidor de correu
dig <servidor-mx> A +short        # IP del servidor de correu
dig -x <IP-del-mx> +short         # el PTR retorna el mateix nom?
```

Si el PTR de la IP no coincideix amb el nom del servidor (o no existeix), molts servidors antispam rebutjaran el correu.

## Pas 6. Capturar la consulta amb Wireshark

```bash
sudo tcpdump -i any -n port 53 -w inversa.pcap
```

Mentre captureu, feu un `dig -x <IPv4>` i identifiqueu al paquet el tipus de registre (**PTR**) i el nom consultat (`…in-addr.arpa`).

## Lliurament

Completeu aquesta taula amb almenys tres dominis diferents. Podeu fer servir la [plantilla en CSV :material-download:](fitxers/resultats-consultes-inverses.csv).

| Domini | IP (A/AAAA) | Resultat PTR | Coincideix amb el nom? |
| --- | --- | --- | --- |
|  |  |  |  |

## Preguntes

1. Retorna el PTR el mateix nom del domini que heu consultat? Per què pot ser diferent (CDN, hosting compartit, ISP)?
2. Una mateixa IP pot tenir diversos noms directes, però el PTR sol ser únic. Quines conseqüències té?
3. Qui ha delegat la zona inversa del bloc d'IP que heu consultat?
