---
title: "Solucions: consultes recursives i iteratives"
description: Respostes orientatives a les preguntes de la pràctica de consultes recursives i iteratives.
tipus: solucions
level: solucions
tags:
  - DNS
---

# Solucions: consultes recursives i iteratives

Respostes orientatives a les preguntes de la [pràctica](02-practica-recursiva-iterativa.md).

## 1. Per què els servidors arrel no accepten consultes recursives?

Per **escala** i per **seguretat**:

- Si un servidor arrel fes recursió, hauria de resoldre de principi a fi les consultes de tot Internet i guardar-ne els resultats en cache. Cap infraestructura podria absorbir aquesta càrrega.
- La seva funció és només **delegar**: saben quins servidors són responsables de cada TLD, i amb una *referral* ja han fet la seva feina. Això els permet respondre molt ràpid i sense estat.
- Un servidor que fa recursió per a tothom és un objectiu fàcil per a **atacs d'amplificació** i d'**enverinament de cache**. Mantenint-los sense recursió, se'n redueix la superfície d'atac.

Si se'ls envia una consulta amb RD=1, l'ignoren: responen igualment amb una *referral* i sense el flag `ra`.

## 2. Quin tipus de consulta fa el navegador? I el resolutor de l'ISP?

- El **navegador** (a través del *stub resolver* del sistema, o del seu propi client DoH) fa una consulta **recursiva** (RD=1) al resolutor configurat i espera la resposta final.
- El **resolutor de l'ISP** rep aquesta consulta recursiva i, per respondre-la, fa consultes **iteratives** (RD=0) a l'arrel, al TLD i a l'autoritatiu. Té, per tant, els dos papers: servidor recursiu cap als clients i client iteratiu cap a la resta del DNS.

## 3. Escenaris hipotètics

**Si el recursiu només sabés fer consultes iteratives** (és a dir, si als clients els contestés amb *referrals* en lloc de la resposta final), el *stub resolver* del client no sabria què fer-ne: no està preparat per seguir derivacions. La resolució fallaria i el client quedaria sense resposta. En la pràctica, aquest servidor es comportaria com un autoritatiu, no com un resolutor.

**Si el client només sabés fer consultes recursives però el servidor no les admetés**, el servidor respondria amb `REFUSED` (o amb una *referral* sense el flag `ra`) i el client no obtindria la resposta. És exactament el que passa quan un client queda fora de l'ACL d'un recursiu: cal configurar-li un altre resolutor que sí que li ofereixi recursió.
