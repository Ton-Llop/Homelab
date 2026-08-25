# Homelab

Aquest repo és per anar documentant el meu petit homelab de casa.

La idea no és muntar res superprofessional des del primer dia. Vull aprofitar un PC vell que tenia per casa per aprendre coses de Linux, xarxes, virtualització, Docker, serveis, automatització i una mica de DevOps en general.

Ara mateix el servidor és un **HP Pavilion p6-2301es** bastant antic, però per començar ja em serveix de sobres.

![PC obert](docs/images/01-pc-obert-pols.jpg)

## Hardware actual

- HP Pavilion p6-2301es
- Intel Core i3-3220 @ 3.30 GHz
- 16 GB DDR3-1600 (2x8 GB)
- SSD Patriot Blast de 240 GB
- Proxmox VE com a sistema base

La RAM no hi era quan vaig recuperar el PC, així que el primer problema del homelab van ser **5 pitidos al fer boot**. Al final era simplement que no tenia RAM instal·lada 😭.

![16 GB detectats](docs/images/03-16gb-detectats.jpg)

## Què vull muntar

Per ara la idea és anar a poc a poc:

- [ ] Pi-hole
- [ ] Una VM amb Ubuntu Server
- [ ] Docker / Docker Compose
- [ ] Jellyfin
- [ ] Uptime Kuma
- [ ] Monitoring amb Prometheus / Grafana
- [ ] Ansible per automatitzar configuracions
- [ ] Més endavant provar k3s / Kubernetes

No tinc intenció de muntar-ho tot de cop. Prefereixo entendre cada cosa abans d'afegir la següent.

## Estructura del repo

```text
homelab/
├── README.md
├── docs/
│   ├── hardware.md
│   ├── network.md
│   ├── troubleshooting.md
│   └── images/
├── proxmox/
├── docker/
├── ansible/
└── scripts/
```

## Objectiu

La gràcia és que el servidor físic pugui canviar amb el temps, però les configuracions i el que vaig aprenent quedin aquí guardats.

Ara és un i3 vell amb 16 GB de RAM. Si algun dia tinc més pressupost, la idea és ampliar hardware i continuar fent créixer el homelab sense començar de zero.
