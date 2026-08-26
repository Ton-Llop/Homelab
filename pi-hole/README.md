# Pi-hole

Primer servei del homelab: un **Pi-hole** per bloquejar anuncis, trackers i altres dominis directament des de la xarxa.

La idea és que els dispositius de casa utilitzin Pi-hole com a servidor DNS, així el bloqueig no depèn només d'un AdBlock del navegador.

## Estructura

Pi-hole està executant-se dins d'un contenidor LXC de Debian a Proxmox.

```text
Internet
   |
TP-Link Deco
192.168.68.1
   |
   +-- Proxmox
   |   192.168.68.251
   |
   +-- LXC Debian
       Pi-hole
       192.168.68.253
```

### Xarxa

El DHCP del router reparteix IPs entre:

```text
192.168.68.100 - 192.168.68.250
```

Per això les IPs del homelab les he deixat fora d'aquest rang:

```text
192.168.68.251 -> Proxmox
192.168.68.253 -> Pi-hole
```

Al principi vaig posar Pi-hole també a `.251` i evidentment van començar a passar coses rares perquè Proxmox ja tenia aquesta IP 😅.

Una bona mini lliçó sobre conflictes d'IP.

## Contenidor

Configuració aproximada del LXC:

```text
Sistema: Debian
CPU: 1 core
RAM: 1 GiB
Swap: 512 MiB
Disc: 8 GiB
IP: 192.168.68.253/24
Gateway: 192.168.68.1
```

Per un Pi-hole és més que suficient.

No he utilitzat una VM completa perquè per aquest servei un LXC és més lleuger i ja fa perfectament la feina.

## Instal·lació

Primer vaig actualitzar Debian:

```bash
apt update && apt upgrade -y
```

Després vaig instal·lar `curl`:

```bash
apt install curl -y
```

I finalment Pi-hole amb l'instal·lador oficial:

```bash
curl -sSL https://install.pi-hole.net | bash
```

Durant la instal·lació vaig deixar activat:

* Query Logging
* Show everything
* Interfície `eth0`
* IP estàtica

## Comprovacions

Per veure si Pi-hole estava funcionant:

```bash
pihole status
```

També vaig comprovar els ports:

```bash
ss -lntup | grep -E ':(53|80|443)\b'
```

Pi-hole utilitza principalment:

```text
53  -> DNS
80  -> Web
443 -> Web HTTPS
```

## Prova DNS

Abans de posar Pi-hole a tota la xarxa, el vaig provar només des del meu PC.

```powershell
nslookup google.com 192.168.68.253
```

Resultat:

```text
Servidor: pi.hole
Address: 192.168.68.253
```

També:

```powershell
nslookup pi.hole 192.168.68.253
```

resolia correctament cap a:

```text
192.168.68.253
```

Després vaig configurar el DNS del Wi-Fi del PC manualment a:

```text
192.168.68.253
```

i vaig buidar la caché DNS:

```powershell
ipconfig /flushdns
```

A partir d'aquí Pi-hole ja apareixia com a DNS per defecte del PC.

## Dashboard

La interfície web està disponible a:

```text
http://192.168.68.253/admin
```

Després de navegar una mica sense l'AdBlock del navegador, Pi-hole ja havia començat a bloquejar consultes DNS.

Per tant:

```text
PC
 |
 | DNS
 v
Pi-hole
192.168.68.253
 |
 v
DNS extern
```

funciona correctament.

## Configuració pendent

Encara falta configurar el **TP-Link Deco** perquè reparteixi Pi-hole com a DNS a tots els dispositius de casa.

La idea serà:

```text
DNS principal:   192.168.68.253
DNS secundari:   8.8.8.8
```

El secundari servirà perquè la xarxa continuï resolent DNS si el PC del homelab està apagat.

La pega és que alguns dispositius poden utilitzar directament `8.8.8.8` i saltar-se Pi-hole, però de moment prefereixo tenir Internet si el servidor està apagat.

Aquesta configuració queda pendent perquè l'app de Deco avui ha decidit no col·laborar :)

## Notes

Pi-hole no necessita codi propi.

Aquest projecte és sobretot una pràctica de:

* Proxmox
* Linux/Debian
* LXC
* DNS
* DHCP
* IPs estàtiques
* administració de xarxa

Més endavant es poden afegir scripts, backups o automatització, però per ara l'objectiu era entendre com funciona i deixar-lo operatiu.

## Estat

```text
[OK] Debian LXC
[OK] Pi-hole instal·lat
[OK] IP estàtica
[OK] Resolució DNS
[OK] Bloqueig de dominis
[OK] Dashboard web
[OK] PC utilitzant Pi-hole
[PENDENT] Configurar DNS al TP-Link Deco
[PENDENT] Provar Pi-hole amb tota la xarxa
```
