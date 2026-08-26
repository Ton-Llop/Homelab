# Homarr

Dashboard principal del homelab per tenir tots els serveis en un sol lloc i no haver d'anar recordant IPs, ports i panells diferents.

La idea és que **Homarr sigui la porta d'entrada al homelab**.

Ara mateix hi tinc integrats:

* Proxmox
* Pi-hole
* Estat dels LXC
* Ús de CPU i RAM
* Consultes DNS
* Dominis bloquejats

Més endavant hi aniran apareixent Jellyfin, monitorització del consum elèctric i la resta de serveis que vagi muntant.

---

## Estructura

Homarr està executant-se dins d'un LXC Debian separat.

```text
TP-Link Deco
192.168.68.1
│
└── Proxmox
    192.168.68.251
    │
    ├── LXC Homarr
    │   192.168.68.252
    │   │
    │   └── Docker
    │       └── Homarr :7575
    │
    └── LXC Pi-hole
        192.168.68.253
```

La interfície web de Homarr està disponible a:

```text
http://192.168.68.252:7575
```

---

## Contenidor

Configuració aproximada del LXC:

```text
Sistema: Debian
CPU: 1 core
RAM: 1 GiB
Swap: 512 MiB
Disc: 8 GiB

IPv4: 192.168.68.252/24
Gateway: 192.168.68.1
```

També he activat **Nesting** al LXC perquè Docker pugui funcionar dins del contenidor.

L'estructura acaba sent:

```text
Proxmox
└── LXC Debian
    └── Docker
        └── Homarr
```

---

Per generar secret key fer:

```bash
openssl rand -hex 32
```

## Integració amb Pi-hole

Homarr està connectat amb el Pi-hole que corre a:

```text
192.168.68.253
```

Això permet veure directament al dashboard coses com:

```text
Consultes DNS
Consultes bloquejades
Percentatge bloquejat
Dominis a les blocklists
Estat del bloqueig
```

També hi ha un control ràpid per activar o desactivar temporalment el bloqueig de Pi-hole.

---

## Integració amb Proxmox

Homarr també està connectat amb:

```text
https://192.168.68.251:8006
```

Per seguretat no he utilitzat l'usuari `root`.

He creat un usuari específic:

```text
homarr@pve
```

amb el rol:

```text
PVEAuditor
```

Aquest rol permet consultar informació de Proxmox però no modificar la infraestructura.

Homarr pot veure:

```text
CPU
RAM
Nodes
VMs
LXCs
Emmagatzematge
Uptime
```

---

## API Token

Per connectar Homarr amb Proxmox també he creat un **API Token** específic.

La idea és:

```text
Homarr
   │
   │ API Token
   ▼
Proxmox
   │
   └── PVEAuditor
       només lectura
```

Així Homarr no necessita guardar la contrasenya d'administrador de Proxmox.

El secret del token **no es guarda al repositori**.

---

## Certificat de Proxmox

Durant la integració, Homarr no confiava inicialment en el certificat HTTPS de Proxmox.

Proxmox utilitza la seva pròpia CA interna.

El certificat públic de la CA està a:

```text
/etc/pve/pve-root-ca.pem
```

Aquest certificat es va afegir a Homarr perquè pogués validar correctament la connexió HTTPS amb Proxmox.

També vaig haver de regenerar el certificat del node perquè encara contenia una IP antiga:

```bash
pvecm updatecerts --force
systemctl restart pveproxy
```

---

## Dashboard actual



![Dashboard actual de Homarr](./images/ig1.png)

Actualment mostra principalment:

```text
Pi-hole
├── Consultes
├── Bloquejos
├── Percentatge bloquejat
└── Estat

Proxmox
├── CPU
├── RAM
├── Nodes
├── LXCs
└── Emmagatzematge

Apps
├── Pi-hole
└── Proxmox
```

La idea és anar afegint serveis només quan realment existeixin al homelab.

---

## Futur

Algunes coses que m'agradaria afegir:

```text
[ ] Jellyfin
[ ] Consum elèctric real del servidor
[ ] Cost diari / mensual del homelab
[ ] Home Assistant
[ ] Monitorització més completa
[ ] Jaull ?¿?¿?¿
[ ] Lipopotamo ?¿?¿
```

També m'agradaria automatitzar en el futur el desplegament amb scripts o Ansible.

---

## Estat

```text
[OK] LXC Debian
[OK] Docker
[OK] Docker Compose
[OK] Homarr
[OK] IP estàtica
[OK] Integració Pi-hole
[OK] Integració Proxmox
[OK] API Token de només lectura
[OK] Certificat Proxmox
[OK] Dashboard inicial

[PENDENT] Monitorització del consum elèctric
[PENDENT] Jellyfin
[PENDENT] Automatització del desplegament
```

Per ara Homarr ja funciona com a **panell central del homelab**.
