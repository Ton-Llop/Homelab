# Coses que vull fer al Homelab

Això és més una llista de desitjos que un pla seriós. La vaig actualitzant a mesura que munto coses noves o em venen idees.

## Què tinc muntat ara mateix

```text
[OK] Proxmox VE
[OK] Pi-hole en un LXC de Debian
[OK] Homarr com a dashboard
[OK] Monitor de consum amb el Tapo P110
```

Encara és poca cosa, però ja és un homelab que fa alguna cosa útil.

## Abans de res: no perdre-ho tot

Tinc ganes d'anar afegint serveis, però hi ha una cosa que hauria de fer primer: **còpies de seguretat**.

Ara mateix tot viu dins d'un únic SSD de 240 GB. Si aquest disc peta, perdo Proxmox, el LXC del Pi-hole i la base de dades del consum de cop. I no tinc cap còpia enlloc 😅.

1. **Fer backups de veritat**
   Com a mínim `vzdump` dels contenidors cap a un disc extern. I si m'animo, muntar un **Proxmox Backup Server** en un LXC amb el seu propi disc, que ja fa deduplicació i retenció.
   El més important no és fer la còpia, és **provar de restaurar-la**. Un backup que no s'ha provat mai no és un backup.

2. **Vigilar la salut del disc**
   Muntar **Scrutiny** per veure les dades SMART amb un dashboard i avisos.
   Amb un sol disc, assabentar-me que s'està morint *abans* que passi val molt.

3. **Posar-hi un disc dur**
   La caixa de l'HP té una badia de 3.5" lliure. Amb un disc de 2-4 TB de segona mà (uns 30-50 €) ja podria fer Jellyfin, fotos i backups sense anar tan just.
   Ara mateix l'espai és el que més em limita, molt més que la CPU o la RAM.

## Coses que vull aprendre

4. **Configurar DNS local + Reverse Proxy**
   Poder accedir a Pi-hole, Jellyfin, Grafana, Proxmox, etc. amb noms tipus `pihole.home.arpa` i no haver d'anar recordant IPs i ports tota l'estona.

5. **Muntar Jellyfin**
   Tenir el meu propi servidor multimèdia i aprofitar per aprendre una mica més sobre storage, permisos, mounts, xarxa, etc.
   Una cosa a tenir en compte: la gràfica integrada d'aquest i3 (HD 2500) només accelera **H.264**. Res d'HEVC ni AV1, així que hauré de pensar la biblioteca perquè vagi en direct play.

6. **Aprendre Prometheus + Grafana**
   Poder monitoritzar Proxmox, containers, Jellyfin, Pi-hole, consum elèctric, RAM, CPU, xarxa, temperatures, uptime, etc.

7. **Aprendre Docker bé**

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

## Serveis que vull anar afegint

### Els que posaria primer

Són lleugers, caben de sobres amb 16 GB de RAM i cadascun em serveix per aprendre alguna cosa.

* **Uptime Kuma**
  Va comprovant cada X segons si els serveis responen (ping, HTTP, DNS) i m'avisa per Telegram quan alguna cosa cau.
  És la manera fàcil de tenir monitorització abans de posar-me amb Prometheus.

* **Unbound darrere el Pi-hole**
  Un DNS recursiu meu, per deixar de dependre del 8.8.8.8 de Google.
  És mitja hora de feina i acabes entenent de veritat com es resol un domini.

* **Forgejo** (o Gitea)
  Tenir aquest mateix repo allotjat a casa, amb el seu **runner d'Actions**.
  Això lliga el punt 8 (automatització) amb el 12 (portfolio): push al repo, build, i desplegat sol. Crec que és el que més m'acostaria a entendre CI/CD de debò.

* **Vaultwarden**
  Gestor de contrasenyes compatible amb Bitwarden.
  A part de ser útil de veritat, m'obliga a fer bé l'HTTPS i els backups, perquè aquí ja fa mal perdre les dades.

* **Dockge**
  Per gestionar els stacks de Docker Compose des del navegador però deixant els YAML al disc, així els puc continuar tenint al Git.

### Quan tingui el proxy i el Grafana

* **Authelia**
  Login únic amb 2FA davant del reverse proxy, en comptes de tenir vuit contrasenyes diferents.
  Serveix per entendre com funcionen OIDC i les sessions. L'Authentik fa el mateix però es menja molta més RAM, per aquest PC no.

* **CrowdSec**
  Per quan exposi el portfolio a Internet. És com el punt 10 del firewall però reaccionant sol, i de pas veus els atacs reals que van arribant.

* **Loki**
  Logs centralitzats al costat de Grafana. Amb compte amb la retenció, que 240 GB s'omplen ràpid.

* **Semaphore UI**
  Una web per llançar els playbooks d'Ansible i tenir historial d'execucions. Just per omplir la carpeta `ansible/`, que ara està buida.

* **Tailscale**
  No per substituir el WireGuard: primer el vull muntar a mà, que és on s'aprèn. Tailscale seria el que faria servir el dia a dia perquè simplement funciona.
  Si em vull complicar la vida, hi ha **Headscale** per allotjar el servidor jo mateix.

### Coses útils per al dia a dia (quan tingui disc)

* **Home Assistant** — ja tinc el Tapo P110, així que té molt sentit. Podria fer automatismes tipus "avisa'm si el consum puja de X" o encendre el servidor amb Wake-on-LAN.
* **Immich** — el meu Google Fotos particular. Millor desactivar la part d'IA o aquest i3 plorarà.
* **Syncthing** — sincronitzar carpetes entre PC i mòbil. Molt més lleuger que muntar un Nextcloud sencer.
* **Paperless-ngx** — factures i papers escanejats amb OCR i cercador.
* **n8n** — automatitzacions. Un bon lloc per endollar-hi les dades del P110.

## Coses que de moment NO muntaré

No perquè siguin dolentes, sinó perquè en aquest hardware encara no tenen sentit:

* **Nextcloud sencer** i **Authentik** — massa pesats per a un i3 de dos nuclis.
* **Ollama / IA local** — sense GPU no val la pena ni provar-ho.
* **k3s ara mateix** — amb 2 nuclis seria gairebé tot overhead. Millor esperar a tenir més serveis i alguna màquina més.

## Ordre aproximat

```text
Proxmox + Pi-hole            [fet]
        ↓
Dashboard (Homarr)           [fet]
        ↓
Smart Plug + consum          [fet]
        ↓
Backups (vzdump / PBS)
        ↓
DNS local + Reverse Proxy
        ↓
Unbound darrere el Pi-hole
        ↓
Uptime Kuma
        ↓
Forgejo + CI
        ↓
Vaultwarden
        ↓
Disc dur nou + Jellyfin
        ↓
Prometheus + Grafana
        ↓
Ansible + automatització
        ↓
Networking + Firewall
        ↓
WireGuard
        ↓
Authelia
        ↓
Self-hosting del portfolio
        ↓
k3s / Kubernetes
```

La idea és que cada cosa nova que monti tingui una utilitat real i, de pas, em serveixi per anar aprenent infraestructura, networking, DevOps i seguretat.
