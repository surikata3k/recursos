---
title: "Pràctica: servidors de noms d'un domini"
description: Localitzar els NS autoritatius d'un domini real, consultar-los directament i comparar-los amb un recursiu.
tipus: practica
tags:
  - DNS
  - Línia d'ordres
  - Ciberseguretat
---

# Pràctica: localitzar els servidors de noms d'un domini i consultar-los directament

!!! abstract "Objectiu"

    Descobrir quins són els servidors autoritatius (ns1, ns2…) d'un domini real, comprovar que tots dos responen amb la mateixa informació i veure la diferència entre preguntar a un recursiu i preguntar a un autoritatiu.

Substituïu `<domini>` pel domini que us assigni el professor (per exemple, el de l'institut o un de públic com `wikipedia.org`).

## Pas 1. Trobar els servidors de noms (registres NS)

```bash
dig <domini> NS +short
```

Obtindreu una llista de noms, normalment dos o més (`ns1.…`, `ns2.…`). Anoteu-los.

## Pas 2. Obtenir l'adreça IP de cada servidor de noms

```bash
dig ns1.<proveïdor> A +short
dig ns2.<proveïdor> A +short
```

Substituïu `ns1.<proveïdor>` i `ns2.<proveïdor>` pels noms obtinguts al pas 1. Si els noms es troben dins del mateix domini, recordeu que la IP és al *glue record* de la delegació.

## Pas 3. Consultar directament un dels servidors autoritatius

```bash
dig @ns1.<proveïdor> <domini> A
dig @ns1.<proveïdor> <domini> MX +short
dig @ns1.<proveïdor> <domini> SOA +multiline
```

Observeu a la resposta:

- El flag **`aa`** (*authoritative answer*) als flags de la capçalera: confirma que el servidor és autoritatiu per a la zona.
- Que **no** apareix el flag `ra` (recursió disponible) en la majoria d'autoritatius: no resolen noms d'altres dominis.
- El **TTL** original (no decreix perquè no hi ha cache).

## Pas 4. Comparar amb l'altre servidor i amb un recursiu

```bash
dig @ns2.<proveïdor> <domini> SOA +short
dig @8.8.8.8 <domini> A
```

- Coincideix el **serial** del SOA a ns1 i ns2? Si no, la replicació va endarrerida.
- Quines diferències veieu entre la resposta de l'autoritatiu (`aa`) i la del recursiu (`ra`, TTL que baixa)?

## Pas 5. Prova de reconeixement

!!! danger "Només en entorn de laboratori o amb autorització"

    Intentar una transferència de zona contra servidors de tercers sense permís pot considerar-se un intent d'intrusió.

```bash
dig @ns1.<proveïdor> <domini> AXFR
```

El resultat esperat en un servidor ben configurat és `Transfer failed` o `REFUSED`. Si us retornés tota la zona, seria un error de configuració greu (`allow-transfer` obert).

## Preguntes

1. Quants servidors de noms té el domini? Estan en xarxes diferents?
2. Quin és el serial de la zona? Coincideix en tots els NS?
3. Què canvia entre preguntar a `ns1` i preguntar a `8.8.8.8`?
4. Per què és important que l'AXFR sigui rebutjat?
