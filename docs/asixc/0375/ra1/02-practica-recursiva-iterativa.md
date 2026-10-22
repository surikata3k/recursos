---
title: "Pràctica: consultes recursives i iteratives"
description: Veure amb dig la diferència entre preguntar a un recursiu i seguir les referrals des de l'arrel.
tipus: practica
tags:
  - DNS
  - Línia d'ordres
---

# Pràctica: consultes recursives i iteratives amb `dig`

!!! abstract "Objectiu"

    Observar a la pràctica la diferència entre una consulta **recursiva** (RD=1) i una d'**iterativa** (RD=0), i seguir manualment el camí de la resolució des dels servidors arrel fins a l'autoritatiu.

    Repassa abans la teoria: [Consulta recursiva vs iterativa](01-dns-en-profunditat.md#51-consulta-recursiva-vs-iterativa).

## Passos

```bash
# 1. Consulta recursiva (per defecte, RD=1) a un recursiu públic
dig @8.8.8.8 www.exemple.cat A

# 2. Consulta iterativa a un servidor arrel (+norecurse → RD=0)
dig @a.root-servers.net www.exemple.cat A +norecurse

# 3. Seguir manualment la referral: ara al servidor de .cat
#    (agafeu un NS de la secció AUTHORITY del pas anterior)
dig @<ns-de-.cat> www.exemple.cat A +norecurse

# 4. Preguntar al servidor autoritatiu: ara sí, resposta amb flag aa
dig @ns1.exemple.cat www.exemple.cat A +norecurse

# 5. Tot el procés automàtic fet per dig, imitant un recursiu
dig +trace www.exemple.cat
```

## Què cal observar

- Als **flags** de la resposta: `rd` i `ra` a la recursiva; cap dels dos a la iterativa.
- Als passos 2 i 3 la resposta **no té secció ANSWER**, sinó **AUTHORITY** (els NS de la referral) i **ADDITIONAL** (els *glue records*).
- Només al pas 4 apareix el flag **`aa`** i la secció **ANSWER** amb la IP.
- Si proveu una consulta iterativa (`+norecurse`) a un recursiu sense la resposta en cache, veureu que no la resol.

## Preguntes

1. Per què els servidors arrel no accepten consultes recursives?
2. Quin tipus de consulta fa el navegador? I el resolutor de l'ISP?
3. Què passaria si el recursiu només sabés fer consultes iteratives? I si el client només sabés fer-ne de recursives però el servidor no les admetés?
