# Xarxa

Aquesta és la configuració inicial de xarxa del homelab.

## Proxmox

- Hostname: `pve.home.arpa`
- IP de Proxmox: `192.168.68.250/24`
- Gateway: `192.168.68.1`
- Web UI: `https://192.168.68.250:8006`

El servidor està connectat per **Ethernet** i el meu PC pot continuar connectat per Wi-Fi. Mentre estiguin a la mateixa xarxa puc administrar Proxmox des del navegador o per SSH.

```text
Internet
   |
Router / xarxa de casa
   |
   +---- Ethernet ---- HP / Proxmox
   |                    192.168.68.250
   |
   +---- Wi-Fi -------- PC principal
```

## Nota sobre la IP

Durant la instal·lació vaig posar inicialment `192.168.100.2`, però la meva xarxa real era `192.168.68.0/24`.

Per això des del PC no podia entrar a Proxmox encara que la instal·lació estigués bé.

La IP es va canviar a:

```text
192.168.68.250/24
```

amb gateway:

```text
192.168.68.1
```

Més endavant vull deixar aquesta IP ben reservada al router perquè no l'agafi cap altre dispositiu.

## Noms locals

He posat `pve.home.arpa` com a FQDN del servidor.

Més endavant, quan tingui Pi-hole / DNS local, la idea és poder tenir noms tipus:

```text
pve.home.arpa
pihole.home.arpa
jellyfin.home.arpa
grafana.home.arpa
```

Així no hauré d'anar recordant IPs i ports tot el rato.
