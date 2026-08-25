# Hardware

## Servidor principal

El primer servidor del homelab és un **HP Pavilion p6-2301es** que tenia per casa.

No és res espectacular, però per començar a jugar amb Proxmox, contenidors i serveis em va perfecte.

### Especificacions

| Component | Hardware |
|---|---|
| CPU | Intel Core i3-3220 @ 3.30 GHz |
| RAM | 16 GB DDR3-1600 (2x8 GB) |
| Disc | Patriot Blast SSD 240 GB |
| Xarxa | Ethernet integrada |
| Hypervisor | Proxmox VE |

## Primera obertura

El PC portava bastant temps sense utilitzar-se i estava una mica ple de pols.

![Interior del PC](images/01-pc-obert-pols.jpg)

El primer cop que el vaig encendre feia 5 pitidos seguits, parava aproximadament un segon i tornava a començar.

Després d'obrir-lo vaig veure que els dos slots de RAM estaven buits.

![Slots RAM](images/02-slots-ram.jpg)

Vaig comprar dos mòduls DDR3 de 8 GB i, després d'una mica de guerra per poder-los posar perquè la gràfica estava just al costat, el PC va arrencar correctament.

![RAM detectada](images/03-16gb-detectats.jpg)

Ara té els **16 GB funcionant en dual channel**.

## Futur

Aquest hardware és només el punt de partida.

Si continuo amb el homelab, més endavant m'agradaria millorar coses com:

- CPU / servidor més modern
- més RAM
- més emmagatzematge
- algun NAS
- millor xarxa
- potser una GPU en un futur per fer proves amb IA local

Però de moment l'objectiu és aprendre amb el que tinc.
