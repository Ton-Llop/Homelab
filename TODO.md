# Coses que vull fer al Homelab

1. **Configurar DNS local + Reverse Proxy**
   Poder accedir a Pi-hole, Jellyfin, Grafana, Proxmox, etc. amb noms tipus pihole.ton i no haver d'anar recordant IPs i ports tota l'estona.

2. **Muntar un Dashboard principal del Homelab**
   Una web/portal visual des d'on pugui veure i accedir fàcilment a tots els serveis que tinc muntats al Proxmox.

3. **Muntar Jellyfin**
   Tenir el meu propi servidor multimèdia i aprofitar per aprendre una mica més sobre storage, permisos, mounts, xarxa, etc.

4. **Monitoritzar el consum elèctric del Homelab**
   Pillar un endoll intel·ligent amb mesurament de consum i poder veure:

   * W en temps real
   * kWh diaris/mensuals
   * cost aproximat en €
   * gràfiques del consum
   * estimació mensual/anual

   Si pot ser, integrar-ho amb Home Assistant / Grafana.

5. **Aprendre Prometheus + Grafana**
   Poder monitoritzar Proxmox, containers, Jellyfin, Pi-hole, consum elèctric, RAM, CPU, xarxa, temperatures, uptime, etc.

6. **Aprendre Docker bé**
   
8. **Automatitzar els serveis perquè tot sigui recreable**
   Fer scripts/playbooks per cada servei que vaig muntant perquè, si algun dia canvio de hardware o rebento alguna cosa, pugui reconstruir-ho fàcilment.

   La idea seria anar aprenent:

   * Bash per scripts petits
   * Ansible per configuració idempotent
   * més endavant OpenTofu/Terraform per crear VMs/LXC automàticament

9. **Aprendre networking de veritat**
   Amb Pi-hole ja he tocat alguna cosa, però molt bàsica. M'agradaria entendre bé:

   * LAN / WAN
   * subnets
   * gateway
   * DNS / DHCP
   * NAT
   * ports
   * TCP / UDP
   * routing

10. **Configurar bé el firewall del Homelab**
   Aprendre `nftables` i també el firewall de Proxmox per controlar què pot accedir a què i evitar exposar serveis que no toca a Internet.

11. **Configurar WireGuard per entrar al Homelab des de fora**
    Poder connectar-me des del portàtil/mòbil quan no estic a casa i accedir a Proxmox, Pi-hole, Jellyfin, Grafana, etc. com si estigués dins de la LAN, sense haver d'exposar tots els serveis.

12. **Hostejar el meu portfolio al Homelab**
    Provar de treure'l de Vercel i servir-lo jo mateix amb Docker + reverse proxy + HTTPS.
    Primer podria fer una prova amb algun subdomini abans de moure `tonllop.dev` completament.

13. **Aprendre Kubernetes / k3s més endavant**
    No muntar-lo perquè sí. Primer tenir bastants serveis amb Docker/Compose i, quan realment tingui sentit, començar amb k3s/Kubernetes.

14. **Deixar tot el Homelab documentat a Git**
    Tenir configs, scripts, Ansible, Docker Compose, documentació i decisions al repo perquè tot el que vaig fent quedi registrat i sigui fàcil de reproduir.

## Ordre aproximat

```text
Proxmox + Pi-hole
        ↓
DNS local + Reverse Proxy
        ↓
Dashboard
        ↓
Jellyfin
        ↓
Smart Plug + consum elèctric
        ↓
Prometheus + Grafana
        ↓
Docker / Docker Compose
        ↓
Ansible + automatització
        ↓
Networking + Firewall
        ↓
WireGuard
        ↓
Self-hosting del portfolio
        ↓
k3s / Kubernetes
```

La idea és que cada cosa nova que monti tingui una utilitat real i, de pas, em serveixi per anar aprenent infraestructura, networking, DevOps i seguretat.

Docker / Docker Compose
        ↓
Ansible + automatització
        ↓
Networking + Firewall
        ↓
WireGuard
        ↓
Self-hosting del portfolio
        ↓
k3s / Kubernetes
