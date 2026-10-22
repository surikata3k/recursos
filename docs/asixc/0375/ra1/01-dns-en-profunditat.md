---
title: DNS en profunditat
description: Arquitectura, resolució, registres, replicació, DNSSEC i DNS xifrat.
tipus: teoria
tags:
  - DNS
  - Serveis de xarxa
  - Ciberseguretat
---

# DNS en profunditat

## 1. Presentació i objectius

El DNS (Domain Name System) és el «llibre d'adreces» distribuït d'Internet. Gairebé cap servei funciona sense ell: web, correu, VPN, autenticació Active Directory, certificats, CDN… I, per això mateix, és un objectiu habitual d'atacs i una font d'informació de primer ordre en ciberseguretat.

**Objectius d'aprenentatge**

- Explicar l'arquitectura jeràrquica i distribuïda del DNS i el procés complet de resolució.
- Interpretar missatges i registres DNS i capturar-los amb eines (dig, Wireshark).
- Instal·lar, configurar i assegurar un servidor autoritatiu i un recursiu (BIND9).
- Configurar zones directes i inverses, i transferències de zona segures.
- Identificar els principals atacs al DNS i aplicar-hi contramesures (ACL, RRL, DNSSEC, DoT/DoH, RPZ).
- Diagnosticar incidències de resolució de manera sistemàtica.

!!! info "Coneixements previs"

    Model TCP/IP, adreçament IPv4/IPv6, UDP vs TCP, ús bàsic de Linux i de la línia d'ordres.

## 2. Per què existeix el DNS (context històric)

- Als anys 70 i principis dels 80 els noms es resolien amb un únic fitxer central, `HOSTS.TXT`, mantingut pel SRI-NIC i descarregat per tots els equips. Amb el creixement d'ARPANET era inviable: tràfic, consistència, col·lisions de noms.
- El 1983 Paul Mockapetris dissenya el DNS (RFC 882/883) i el 1987 queda consolidat a les **RFC 1034** (conceptes) i **RFC 1035** (implementació i format), encara vigents amb moltes actualitzacions.
- Principis de disseny: **jerarquia**, **delegació d'autoritat**, **distribució** de la base de dades, **replicació** i **memòria cau** (cache).
- Avui es manté el fitxer `/etc/hosts` (o `C:\Windows\System32\drivers\etc\hosts`) com a resolució local prioritària segons la configuració de `nsswitch.conf`.

!!! warning "Seguretat"

    El fitxer `hosts` també és un vector d'atac: qui el pot modificar pot redirigir qualsevol nom cap a on vulgui.

## 3. L'espai de noms

### 3.1 Estructura jeràrquica

El DNS organitza els noms com un arbre invertit. L'arrel s'escriu amb un punt final (`.`).

```text
                .  (arrel)
        ┌───────┼───────────┐
       cat     com         org   ... (TLD)
        │       │           │
     exemple  google     wikipedia   (dominis de segon nivell)
        │
       www, mail, ns1  (hosts / subdominis)
```

- **FQDN** (Fully Qualified Domain Name): nom complet i no ambigu, acabat en punt: `www.exemple.cat.`
- Cada etiqueta (label) fa com a màxim **63 octets**; el nom complet, com a màxim **253 caràcters** en forma textual (255 octets en format de xarxa).
- No distingeix majúscules i minúscules (però vegeu més endavant la tècnica 0x20).

### 3.2 Tipus de dominis de primer nivell (TLD)

- **gTLD** genèrics: `.com`, `.org`, `.net`, i els nous (`.app`, `.dev`…).
- **ccTLD** de codi de país: `.es`, `.fr`. El `.cat` és un gTLD patrocinat, no de país, però es comporta de forma semblant.
- **Infraestructura**: `.arpa` (resolució inversa).
- **Reservats per a ús especial** (RFC 6761 i altres): `.local` (mDNS), `.localhost`, `.invalid`, `.test`, `.example`.
- La gestió global del sistema d'identificadors és responsabilitat d'**ICANN/IANA**; cada TLD té un operador de registre (registry) i els particulars/empreses contracten a través d'un **registrador**.

### 3.3 Domini vs zona

!!! question "Un concepte que sovint es confon"

    - **Domini**: subarbre de l'espai de noms (p. ex. `exemple.cat` i tot el que penja d'ell).
    - **Zona**: la part d'aquest arbre que administra un conjunt concret de servidors autoritatius. Una zona pot ser més petita que el domini si s'ha **delegat** un subdomini (`aula.exemple.cat` pot ser una zona pròpia amb altres servidors).
    - La **delegació** es fa amb registres NS (i, si cal, registres **glue**) a la zona pare.

## 4. Actors del sistema DNS

| Actor | Funció | Exemples |
| --- | --- | --- |
| **Stub resolver** | Client mínim del sistema operatiu; fa la consulta i espera la resposta final | libc, systemd-resolved, client DNS de Windows |
| **Resolutor recursiu** (recursive resolver) | Fa tota la feina de resolució per compte del client i la guarda en cache | servidor de l'ISP, 1.1.1.1, 8.8.8.8, 9.9.9.9, BIND/Unbound a l'empresa |
| **Servidor autoritatiu** | Té la còpia oficial d'una zona i respon amb autoritat (flag AA) | ns1.exemple.cat |
| **Servidors arrel** | Coneixen els servidors dels TLD | 13 identitats (a–m.root-servers.net), centenars d'instàncies via **anycast** |
| **Forwarder** | Resolutor que reenvia les consultes a un altre resolutor | DNS del router → DNS de l'ISP |

!!! tip "Punt clau"

    Un mateix programari (BIND) pot fer de recursiu i d'autoritatiu, però **és una mala pràctica barrejar els dos rols al mateix servidor exposat a Internet**. Separar-los redueix molt la superfície d'atac.

## 5. Com es resol un nom: pas a pas

### 5.1 Consulta recursiva vs iterativa

En el DNS hi ha dos tipus de consulta segons **qui fa la feina** de buscar la resposta. No són dos protocols diferents: és el mateix missatge DNS, i només canvia un bit de la capçalera (**RD**, *Recursion Desired*) i el comportament que s'espera del servidor.

#### Consulta recursiva

El client demana: **«dona'm la resposta final, i no em diguis com l'aconsegueixes»**. El servidor que la rep es compromet a retornar una de dues coses: la **resposta definitiva** (l'adreça IP) o un **error** (NXDOMAIN, SERVFAIL…). Mai respon «pregunta a un altre».

- Qui la fa: el *stub resolver* del client (PC, mòbil) cap al resolutor recursiu (el de l'ISP, 8.8.8.8, 1.1.1.1, el de l'empresa…).
- El client activa el bit **RD=1**; el servidor, si ofereix el servei, respon amb el bit **RA=1** (*Recursion Available*).
- Avantatge: el client és molt senzill, només espera una resposta.
- Inconvenient: tota la càrrega de treball recau sobre el recursiu, que a més ha de guardar la informació en cache i protegir-se d'abusos.

!!! note "Analogia: el taxista"

    Demanes a un **taxista** que et porti a una adreça. Tu només dius la destinació; ell es busca el camí i et deixa a la porta.

#### Consulta iterativa

El client demana: **«digues-me el que sàpigues»**. El servidor respon amb la **millor informació que té**: la resposta, si és autoritatiu per a aquell nom, o bé una **referral** (derivació), és a dir, «jo no ho sé, però pregunta a aquests servidors, que s'hi acosten més». Qui pregunta és qui ha de continuar la cerca.

- Qui la fa: el resolutor recursiu cap als servidors arrel, TLD i autoritatius.
- El bit **RD=0**: no es demana que el servidor faci cap feina addicional.
- Els servidors arrel, TLD i autoritatius **no fan recursió** per a clients d'Internet: això els permet atendre milions de consultes sense col·lapsar-se.

!!! note "Analogia: el vianant"

    Preguntes el camí a un **vianant**: «jo no sé on és el carrer, però pregunta al quiosc de la cantonada». Vas al quiosc i allà et diuen: «és al final d'aquesta plaça, pregunta al porter de l'edifici». Tu mateix vas fent cada pas.

#### Com es combinen en una resolució real

Quan escrius `www.exemple.cat` al navegador, les dues modalitats treballen **en cadena**:

```text
                 RECURSIVA                          ITERATIVA
 Client  ─────────────────────►  Resolutor  ──►  Arrel         (referral cap a .cat)
 (stub)  ◄─────────────────────  recursiu   ──►  Servidor .cat (referral cap a exemple.cat)
          resposta final                     ──►  ns1.exemple.cat (resposta amb AA)
```

1. El client fa **una sola** consulta recursiva al resolutor.
2. El resolutor fa **diverses consultes iteratives**: arrel → TLD → autoritatiu.
3. Quan té la resposta, la desa a la cache i **la retorna al client**.

#### Comparació

| | Recursiva | Iterativa |
| --- | --- | --- |
| Qui la fa | Stub resolver → resolutor recursiu | Resolutor recursiu → arrel / TLD / autoritatius |
| Bit RD a la consulta | 1 | 0 |
| Què retorna el servidor | Resposta final o error | Resposta o *referral* |
| Qui fa la feina | El servidor consultat | El qui pregunta |
| Càrrega del servidor | Alta (cerca + cache) | Baixa |
| Servidors que la permeten | Només recursius (amb ACL) | Autoritatius, TLD i arrel |

!!! warning "Nota de seguretat"

    Un recursiu obert a tot Internet pot ser utilitzat per a atacs d'amplificació i enverinament de cache. Per això un recursiu només hauria de respondre als seus clients (ACL), mentre que els autoritatius no haurien d'acceptar consultes recursives.

!!! example "Pràctica"

    Comprova-ho tu mateix amb `dig`: [Pràctica: consultes recursives i iteratives](02-practica-recursiva-iterativa.md).

### 5.2 Exemple: el client demana `www.exemple.cat` (cache buida)

1. L'aplicació crida el sistema (`getaddrinfo`). Es mira primer la cache local i el fitxer `hosts`.
2. El stub envia una consulta recursiva `www.exemple.cat A` al resolutor configurat.
3. El recursiu no ho té en cache i pregunta a un **servidor arrel**: «qui sap de `www.exemple.cat`?» → resposta: referral amb els NS de `.cat`.
4. Pregunta a un servidor de `.cat` → referral amb els NS de `exemple.cat` (més els *glue records* si cal).
5. Pregunta a `ns1.exemple.cat` → resposta **autoritativa** (AA) amb el registre A.
6. El recursiu desa la resposta en cache durant el **TTL** i la retorna al client.
7. El client connecta amb la IP obtinguda.

Ho podem veure en directe:

```bash
dig +trace www.exemple.cat
```

### 5.3 Cache i TTL

- Cada registre porta un **TTL** (segons) que indica quant de temps es pot reutilitzar.
- Hi ha cache a molts nivells: navegador, SO, recursiu. Per això un canvi de DNS «triga a propagar-se»: no es propaga, **caduca**.
- **Negative caching** (RFC 2308): també es guarda que un nom **no existeix** (NXDOMAIN) o que no té aquell tipus (NODATA); el temps el marca el camp *minimum* del SOA.
- Bona pràctica prèvia a una migració: baixar el TTL (p. ex. a 300 s) uns dies abans i tornar-lo a pujar després.

### 5.4 Glue records

Si `ns1.exemple.cat` és el servidor de `exemple.cat`, per resoldre'l caldria… resoldre `exemple.cat`. Es trenca el cercle posant a la zona pare (`.cat`) un registre A **glue** amb la IP de `ns1`. És un bon exemple de dependència circular: fes-ne un dibuix i ho veuràs clar.

## 6. El missatge DNS

Transport: **UDP/53** per defecte; **TCP/53** quan la resposta és truncada (flag TC), per a transferències de zona (AXFR/IXFR) i cada cop més també per a respostes grans (DNSSEC). Amb **EDNS0** (RFC 6891) es poden anunciar mides UDP superiors als 512 bytes clàssics.

Estructura del missatge:

| Secció | Contingut |
| --- | --- |
| Capçalera (12 bytes) | ID (16 bits), flags, comptadors de cada secció |
| Question | Nom consultat, tipus (QTYPE) i classe (QCLASS, normalment IN) |
| Answer | Registres que responen la pregunta |
| Authority | Registres NS amb autoritat (referrals) o SOA en negatives |
| Additional | Informació extra (glue, OPT d'EDNS0) |

**Flags principals**: QR (consulta/resposta), Opcode, AA (resposta autoritativa), TC (truncada), RD (recursió desitjada), RA (recursió disponible), AD (dades autenticades, DNSSEC), CD (comprovació desactivada).

**Codis de resposta (RCODE)**: NOERROR (0), FORMERR (1), SERVFAIL (2), NXDOMAIN (3), NOTIMP (4), REFUSED (5).

!!! example "Activitat"

    Captura amb Wireshark una consulta feta amb `dig` i identifica l'ID, els flags i les seccions.

## 7. Registres de recurs (RR)

Format: `nom  TTL  classe  tipus  dades`

| Tipus | Significat | Exemple |
| --- | --- | --- |
| **SOA** | Inici d'autoritat de la zona: primari, contacte, serial, temporitzadors | vegeu la [zona inversa](#9-zones-inverses) |
| **NS** | Servidor de noms autoritatiu de la zona | `exemple.cat. IN NS ns1.exemple.cat.` |
| **A** | Nom → IPv4 | `www IN A 192.0.2.20` |
| **AAAA** | Nom → IPv6 | `www IN AAAA 2001:db8::20` |
| **CNAME** | Àlies cap a un altre nom (no pot coexistir amb altres registres al mateix nom, ni a l'apex) | `web IN CNAME www` |
| **MX** | Servidors de correu amb prioritat | `@ IN MX 10 mail.exemple.cat.` |
| **TXT** | Text lliure: SPF, DKIM, DMARC, verificacions de propietat | `@ IN TXT "v=spf1 mx -all"` |
| **PTR** | IP → nom (zones inverses) | `20 IN PTR www.exemple.cat.` |
| **SRV** | Localització de serveis (host, port, prioritat, pes) | `_ldap._tcp IN SRV 0 100 389 dc1` |
| **CAA** | Quines CA poden emetre certificats | `@ IN CAA 0 issue "letsencrypt.org"` |
| **DS / DNSKEY / RRSIG / NSEC(3)** | DNSSEC | [secció 11](#11-dnssec-en-profunditat) |
| **TLSA, SSHFP, HTTPS/SVCB** | Associacions de seguretat i paràmetres de servei | — |

Observacions importants:

- Un **MX o NS no pot apuntar a un CNAME** (la RFC ho desaconsella/prohibeix).
- Els registres SRV són la base de la localització de controladors de domini en **Active Directory** (`_ldap._tcp.dc._msdcs.domini`). Un DNS mal configurat = un AD que no funciona.
- SPF, DKIM i DMARC viuen en registres TXT: connexió directa amb la seguretat del correu.

## 8. Replicació: primari i secundari

- Una zona hauria de tenir **com a mínim dos NS** en xarxes/ubicacions diferents (resiliència).
- El **primari** (abans «master») té la còpia editable; els **secundaris** (abans «slave») la repliquen.
- Mecanismes: **AXFR** (transferència completa, sobre TCP), **IXFR** (incremental) i **NOTIFY** (el primari avisa els secundaris d'un canvi).
- Com saben els secundaris que estan al dia? Comparant el **serial** del registre SOA: si el del primari és més gran, demanen la transferència.

!!! warning "Seguretat de les transferències"

    Cal restringir les transferències amb `allow-transfer` i, millor encara, autenticar-les amb **TSIG** (clau compartida HMAC). Una transferència oberta lliura a qualsevol atacant el mapa complet de la xarxa.

!!! example "Pràctica"

    [Pràctica: localitzar i consultar els servidors de noms d'un domini](03-practica-servidors-de-noms.md).

## 9. Zones inverses

Permeten obtenir el nom a partir d'una IP (registres PTR). Es fan servir sobretot en registres de logs, antispam (comprovació del PTR del servidor de correu) i diagnòstic.

- IPv4: s'**inverteixen els octets** sota `in-addr.arpa`. Per a 192.0.2.0/24: `2.0.192.in-addr.arpa`. L'adreça 192.0.2.20 és `20.2.0.192.in-addr.arpa.`
- IPv6: es llisten els **nibbles** (4 bits) invertits sota `ip6.arpa`.
- La delegació inversa la fa qui té assignat el bloc IP (normalment l'ISP/RIR), no el registrador del domini.
- Els octets s'inverteixen perquè la jerarquia DNS es llegeix de dreta a esquerra (de més general a més específic), mentre que una IP va del més general (xarxa) al més específic (host) d'esquerra a dreta.

Exemple de zona inversa ([descarrega el fitxer](fitxers/zona-inversa-2.0.192.db)):

```zone
$ORIGIN 2.0.192.in-addr.arpa.
@   IN SOA ns1.exemple.cat. admin.exemple.cat. ( 2026102001 7200 3600 1209600 3600 )
    IN NS  ns1.exemple.cat.
20  IN PTR www.exemple.cat.
30  IN PTR mail.exemple.cat.
```

!!! example "Pràctica"

    [Pràctica: consultes inverses d'un domini](04-practica-consultes-inverses.md).

## 10. Eines de diagnòstic

| Eina | Ús |
| --- | --- |
| `dig` | La més completa. Mostra flags, seccions, TTL, temps |
| `nslookup` | Disponible a Windows i Linux, més limitada |
| `host` | Consultes ràpides |
| `resolvectl` | Estat i servidors DNS amb systemd-resolved |
| Wireshark / `tcpdump -i any port 53` | Anàlisi a nivell de paquet |
| `ipconfig /displaydns`, `/flushdns` | Cache a Windows |

Ordres `dig` imprescindibles:

```bash
dig exemple.cat A
dig @8.8.8.8 exemple.cat MX +short
dig exemple.cat NS +noall +answer
dig -x 192.0.2.20                 # consulta inversa
dig +trace www.exemple.cat        # recorregut des de l'arrel
dig exemple.cat SOA +multiline
dig exemple.cat DNSKEY +dnssec    # comprovar DNSSEC
dig @ns1.exemple.cat exemple.cat AXFR
```

**Metodologia de diagnòstic** (de l'aplicació cap avall):

1. Hi ha connectivitat IP cap al servidor DNS? (`ping`, `nc -zvu`)
2. Quin servidor fa servir el client? (`resolvectl status`, `/etc/resolv.conf`)
3. Respon el recursiu? Respon l'autoritatiu directament? Compareu amb `dig @ns ...`.
4. El serial coincideix entre primari i secundaris?
5. Hi ha cache obsoleta o TTL alt?
6. Falla DNSSEC? (SERVFAIL que es resol amb `+cd`)
7. Hi ha un tallafocs bloquejant UDP/TCP 53 o respostes fragmentades?

## 11. DNSSEC en profunditat

### 11.1 Què aporta i què no

DNSSEC (RFC 4033/4034/4035) afegeix **autenticitat i integritat** a les respostes mitjançant signatures criptogràfiques. **No xifra** res ni dona confidencialitat, i no protegeix la disponibilitat.

### 11.2 Registres nous

| Registre | Funció |
| --- | --- |
| **DNSKEY** | Clau pública de la zona |
| **RRSIG** | Signatura d'un conjunt de registres (RRset) |
| **DS** | Hash de la clau KSK, publicat a la zona **pare** per enllaçar la cadena |
| **NSEC / NSEC3** | Prova autenticada de **no existència** (NSEC3 dificulta l'enumeració de la zona) |

### 11.3 Claus

- **KSK** (Key Signing Key): signa el conjunt DNSKEY; el seu hash és el DS al pare. Canvia poc.
- **ZSK** (Zone Signing Key): signa la resta de registres. Es rota amb més freqüència.
- Algorismes recomanats actualment: **ECDSAP256SHA256 (13)** i **ED25519 (15)**; RSA/SHA-256 encara és comú.

### 11.4 Cadena de confiança

```text
Arrel (.)  ← àncora de confiança (trust anchor) del validador
  └─ DS de .cat  →  DNSKEY de .cat
        └─ DS de exemple.cat  →  DNSKEY de exemple.cat
              └─ RRSIG de www.exemple.cat A
```

El **recursiu validador** comprova la cadena de dalt a baix. Si falla, retorna **SERVFAIL** al client; si té èxit, activa el flag **AD**.

### 11.5 Operació i riscos

- Les signatures **caduquen**: cal re-signar automàticament (BIND 9 ho fa amb `dnssec-policy`).
- **Rotació de claus** (*key rollover*) mal feta = domini «inexistent» per a tots els validadors.
- Respostes més grans → més TCP i possibles problemes de fragmentació.
- Compatibilitat: avui es valida a gran part d'Internet (recursius públics inclosos).

Exemple de comprovació:

```bash
dig exemple.cat A +dnssec +multiline
dig @8.8.8.8 exemple.cat A     # buscar el flag ad
```

Eines útils: dnsviz.net, Verisign DNSSEC Debugger.

## 12. Privacitat: DNS xifrat

El DNS clàssic (sovint anomenat **Do53**) va en clar per UDP/53: qualsevol a la ruta (la wifi pública, l'ISP, un atacant) veu quins noms consultem i pot manipular les respostes. Els protocols de DNS xifrat posen un «sobre tancat» al voltant de la mateixa consulta DNS: el contingut (el missatge DNS) és idèntic, però viatja protegit.

| Protocol | Port | Transport | Notes |
| --- | --- | --- | --- |
| **DoT** (DNS over TLS, RFC 7858) | TCP 853 | TLS | Fàcil d'identificar i de controlar a la xarxa |
| **DoH** (DNS over HTTPS, RFC 8484) | TCP 443 | HTTPS (HTTP/2 o HTTP/3) | Es barreja amb trànsit web; més difícil de filtrar |
| **DoQ** (DNS over QUIC, RFC 9250) | UDP 853 | QUIC (inclou TLS 1.3) | Menys latència |

### 12.1 Com funciona cada protocol

**Idea comuna a tots tres**

1. El client estableix una connexió segura amb el resolutor i **verifica el seu certificat** (així sap que parla amb qui toca i no amb un impostor).
2. Client i resolutor acorden claus de xifrat.
3. Les consultes i respostes DNS viatgen dins d'aquest túnel xifrat.

Un observador a la xarxa només veu **amb quin servidor** parlem i quantes dades enviem, però **no** quins noms es consulten. Convé recordar que el xifrat protegeix el tram client → resolutor; el resolutor sí que veu les consultes i, si després pregunta als servidors autoritatius, aquest tram pot continuar sent en clar.

=== "DoT"

    **DNS dins d'un túnel TLS dedicat**

    - *Analogia*: una línia telefònica privada, només per al DNS.
    - Com funciona: el client obre una connexió TCP al port **853**, hi fa la negociació TLS (la mateixa tecnologia que protegeix HTTPS) i, un cop xifrat el canal, hi envia els missatges DNS normals, cadascun precedit de la seva longitud.
    - Avantatge per a l'administrador: com que fa servir un port exclusiu, és molt fàcil de **veure, permetre o bloquejar** amb el tallafocs.
    - Inconvenient: si algú bloqueja el port 853, el DNS xifrat deixa de funcionar (en alguns clients, es torna al DNS en clar si no es configura el mode estricte).

=== "DoH"

    **DNS disfressat de trànsit web**

    - *Analogia*: enviar la pregunta dins d'una carta com les que ja passen cada dia pel mateix canal que la navegació web.
    - Com funciona: el client fa una petició **HTTPS** (port 443) a una URL del resolutor, per exemple `https://dns.exemple.cat/dns-query`. El missatge DNS va dins de la petició (en una petició `POST` o codificat a la URL amb `GET`) i la resposta torna dins de la resposta HTTP.
    - Avantatge: és pràcticament indistingible de la resta de trànsit web, i per això és difícil de censurar o bloquejar; a més, els navegadors l'han adoptat fàcilment.
    - Inconvenient per a una organització: l'administrador perd visibilitat i control, perquè una aplicació pot saltar-se el DNS corporatiu i usar el seu propi resolutor.

=== "DoQ"

    **DNS sobre QUIC**

    - *Analogia*: una autopista més ràpida, amb el xifrat ja integrat.
    - Com funciona: **QUIC** és un protocol modern sobre UDP que ja incorpora TLS 1.3. El client connecta al port **UDP 853** i obre un «flux» independent per a cada consulta.
    - Avantatge: la connexió s'estableix amb menys intercanvis (menys latència) i, com que cada consulta va en un flux independent, si es perd un paquet no es bloqueja la resta de consultes (el *head-of-line blocking* del TCP).
    - Inconvenient: és el més recent i encara el menys implantat en clients i resolutors.

**Comparació ràpida**

| | Do53 (clàssic) | DoT | DoH | DoQ |
| --- | --- | --- | --- | --- |
| Xifrat | No | Sí | Sí | Sí |
| Port | UDP/TCP 53 | TCP 853 | TCP 443 | UDP 853 |
| Visible com a DNS a la xarxa | Sí | Sí (port propi) | No (sembla web) | Sí (port propi) |
| Facilitat de bloqueig per l'administrador | — | Alta | Baixa | Alta |

**Prova ràpida al laboratori**

```bash
# DoT: consulta amb kdig (paquet knot-dnsutils)
kdig -d @1.1.1.1 +tls-host=cloudflare-dns.com +tls exemple.cat A

# DoH: petició HTTPS al format JSON
curl -s -H 'accept: application/dns-json' \
  'https://cloudflare-dns.com/dns-query?name=exemple.cat&type=A'

# Comprovar que per port 53 ja no veiem el contingut
sudo tcpdump -i any -n port 853 or port 443
```

Capturant amb Wireshark es veu clarament la diferència: amb UDP/53 es llegeix el nom consultat; amb DoT/DoH/DoQ només es veu el handshake TLS/QUIC i dades il·legibles.

!!! question "Debat"

    DoH millora la privacitat de l'usuari davant l'ISP, però **centralitza** la resolució en pocs proveïdors i fa que l'administrador perdi visibilitat i capacitat de filtratge a les xarxes corporatives. Com ho gestionaria un SOC? (bloquejar proveïdors DoH coneguts, oferir DoH/DoT intern, endpoints gestionats.)

També cal esmentar **EDNS Client Subnet (ECS)** i la minimització del *qname* (RFC 9156) com a mesures de privacitat entre recursiu i autoritatiu.

## 13. DNS i el món real: casos d'ús

- **Balanceig i alta disponibilitat**: múltiples registres A (round-robin), GeoDNS, *health checks*.
- **CDN i cloud**: CNAME cap a `*.cloudfront.net` o equivalent.
- **Active Directory**: SRV per localitzar DC/Kerberos/LDAP; el DNS de domini és crític.
- **Correu**: MX, SPF, DKIM, DMARC, MTA-STS, PTR del servidor.
- **Dynamic DNS / DHCP**: actualitzacions dinàmiques (RFC 2136) assegurades amb TSIG/GSS-TSIG.
- **Seguretat defensiva**: *sinkholing*, RPZ, anàlisi de logs DNS i **passive DNS**.
- **Seguretat ofensiva (reconeixement)**: enumeració de subdominis, AXFR, brute-force de noms, certificats transparents.
