# Xarxa

Aquesta és la configuració de xarxa del homelab.

## Proxmox

- Hostname: `pve.home.arpa`
- IP de Proxmox: `192.168.68.251/24`
- Gateway: `192.168.68.1`
- Web UI: `https://192.168.68.251:8006`

El servidor està connectat per **Ethernet** i el meu PC pot continuar connectat per Wi-Fi. Mentre estiguin a la mateixa xarxa puc administrar Proxmox des del navegador o per SSH.

## Com està muntat ara mateix

```text
Internet
   |
TP-Link Deco
192.168.68.1
   |
   +---- Ethernet ---- Proxmox
   |                   192.168.68.251
   |                     |
   |                     +-- LXC Homarr
   |                     |   192.168.68.252
   |                     |
   |                     +-- LXC Pi-hole
   |                         192.168.68.253
   |
   +---- Wi-Fi -------- PC principal
```

## IPs del homelab

| Què és | IP | Notes |
|---|---|---|
| Router (TP-Link Deco) | `192.168.68.1` | Gateway i DHCP |
| Proxmox | `192.168.68.251` | Web UI al port 8006 |
| LXC Homarr | `192.168.68.252` | Dashboard al port 7575 |
| LXC Pi-hole | `192.168.68.253` | DNS i web `/admin` |

El DHCP del router reparteix IPs entre `192.168.68.100` i `192.168.68.250`.

Per això totes les màquines del homelab van **a partir de la `.251`**, fora del rang, perquè el router no els pugui donar la seva IP a cap altre dispositiu de casa.

Cada servei nou que munti hauria de continuar la sèrie: `.254`, `.255`... i quan s'acabin, replantejar-me el rang del DHCP.

## Història de la IP de Proxmox

Aquesta IP ha canviat dos cops, que és mig homelab resumit en una línia:

```text
192.168.100.2  ->  no era de la meva xarxa, no hi podia entrar
192.168.68.250 ->  ja funcionava, però queia dins del rang del DHCP
192.168.68.251 ->  la definitiva, fora del rang
```

Els detalls de cada canvi estan a [troubleshooting.md](troubleshooting.md).

## Noms locals

He posat `pve.home.arpa` com a FQDN del servidor.

Més endavant, quan tingui el DNS local ben configurat al Pi-hole i un reverse proxy, la idea és poder tenir noms tipus:

```text
pve.home.arpa
pihole.home.arpa
homarr.home.arpa
jellyfin.home.arpa
grafana.home.arpa
```

Així no hauré d'anar recordant IPs i ports tot el rato.
