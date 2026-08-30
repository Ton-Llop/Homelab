# Consum elèctric

El homelab està encès 24/7, així que el corrent és l'única despesa recurrent que té. Aquí apunto què gasta, què he provat per baixar-ho i sobretot **què no ha funcionat**, perquè d'aquí sis mesos no em torni a posar amb el mateix.

Ho mesuro tot amb el [Power Monitor](../P110/README.md), que llegeix la potència real a l'endoll. Això vol dir que el número inclou les pèrdues de la font d'alimentació, que com es veurà més avall no és cap detall menor.

## La regla que ho decideix tot

Amb el preu que tinc al `.env` (`ELECTRICITY_PRICE_EUR_KWH=0.20`):

```text
1 W les 24 h de tot l'any  =  8,76 kWh  =  1,75 €/any
```

Aquest és el número que faig servir per decidir qualsevol cosa del homelab. Cada servei nou, cada disc que afegeixi i cada watt que estalviï es tradueix a euros multiplicant per 1,75.

**Punt de partida: 36 W en repòs = 63 €/any.**

## Experiment: es pot baixar per software? (agost 2026)

### Hipòtesi

Les BIOS dels PC prefabricats sovint porten els C-states profunds capats de fàbrica, i Proxmox instal·la el governor de la CPU en `performance`. Si fos el cas, la CPU no arribaria a dormir mai de veritat i hi hauria 5-10 W per guanyar de franc.

### Què són els C-states

Són com de profund dorm la CPU quan no fa res. `C0` és desperta treballant, `C1`/`C1E` és fer la becaina amb el motor encès, i `C6` és pràcticament tallar-li el corrent al nucli guardant-ne l'estat.

No s'ha de confondre amb els **P-states** (el "governor"), que són a quina velocitat va la CPU *mentre treballa*. Com que el servidor està aturat el 98% del dia, els C-states pesen moltíssim més que el governor.

### Mesura

```bash
for s in /sys/devices/system/cpu/cpu0/cpuidle/state*; do
  printf '%-8s usage=%-10s time=%s us\n' "$(cat $s/name)" "$(cat $s/usage)" "$(cat $s/time)"
done
```

Amb 51,4 h d'uptime:

| Estat | Temps acumulat | % del repòs |
|---|---|---|
| POLL | 0,07 s | 0,00 % |
| C1 | 36 s | 0,02 % |
| C1E | 242 s | 0,13 % |
| C3 | 179 s | 0,10 % |
| **C6** | **50,7 h** | **99,75 %** |

La màquina està aturada el **98,7 %** del temps i, d'aquest temps, en passa el **99,75 % a C6**, l'estat més profund que exposa aquesta CPU.

**Hipòtesi descartada.** La CPU ja dormia perfectament des del primer dia. No hi havia res a guanyar.

### Altres coses que vaig provar

**`powertop --auto-tune`.** Va aplicar l'estalvi del còdec d'àudio i l'autosuspend dels USB. El SATA i el PCIe ASPM es van quedar igual (`[default]`, o sigui el que digui la BIOS).

Un detall a recordar: **powertop només sap estimar watts per dispositiu si hi ha una bateria** d'on llegir la descàrrega. En un sobretaula no pot mesurar res, només aplica ajustos a cegues. Qui mesura és el Tapo.

**Governor de la CPU.** Amb el driver `intel_pstate`, el governor que toca és `powersave`, que no és cap "mode lent": és el dinàmic normal, que puja a tope quan hi ha feina. El que fixa la freqüència al màxim sempre és `performance`. Estan mal batejats i confonen.

**Disc mecànic.** Amb `lsblk` vaig comprovar que el disc dur original de l'HP ja no hi és, només el SSD. Aquells 4-7 W ja me'ls havia estalviat sense saber-ho.

### Resultat

```text
Abans:   36,0 W
Després: 35,5 W
```

Mig watt, que està dins del soroll de mesura. **0,9 €/any.** No compensa ni deixar-ho fixat a l'arrencada.

Com que `powertop --auto-tune` no persisteix entre reinicis, no vaig afegir cap servei de systemd: al següent reinici es reverteix sol i m'estalvio el risc que l'ALPM agressiu del SATA li fes alguna cosa rara al SSD.

## Conclusió: on van els 35,5 W

Estimació aproximada, no mesurada dispositiu a dispositiu:

| Component | Consum aprox. |
|---|---|
| Placa base + chipset + xarxa + USB | 8-12 W |
| 16 GB de DDR3 (2 mòduls) | 3-5 W |
| CPU dormint en C6 | 3-5 W |
| SSD i ventiladors | 2-3 W |
| **Pèrdues de la font d'alimentació** | **~10-12 W** |

La lliçó de tot plegat: **amb la CPU ja dormint bé, el component que més gasta de la màquina és la font d'alimentació.** Una font OEM de 2012 de ~300 W treballant a 36 W està al 12 % de càrrega, molt per sota del rang on es certifica l'eficiència (el 80 PLUS ni tan sols mesura per sota del 20 %). Allà és normal anar pel 65-70 %: de cada 36 W que pago a l'endoll, uns 11 no arriben ni a la placa.

Per posar-ho en perspectiva, 35,5 W per un sobretaula del 2012 amb Proxmox **està bé**. El normal en aquesta generació és anar pels 50-60 W. La màquina ja estava afinada abans de començar, i per això no vaig trobar res.

## Què queda per fer

| Acció | Estalvi | Cost | Retorn |
|---|---|---|---|
| Treure el lector de DVD (`sr0`) i el de targetes (`sdb`) | ~2 W → 3,5 €/any | 10 min de tornavís | immediat |
| Canviar la font d'alimentació | 8-12 W → 14-21 €/any | 60-70 € | ~4 anys |
| Canviar la màquina per un mini PC N100 | ~26 W → 45 €/any | ~150 € | ~3 anys |

Sobre la font: abans de comprar res, cal obrir la caixa i **confirmar que el connector de la placa és ATX estàndard de 24 pins**, perquè alguns HP d'aquella època porten pinout propietari.

Sobre el mini PC: un N100 fa idle entre 6 i 10 W i, a més, la seva iGPU accelera HEVC i AV1 per hardware, cosa que resoldria de passada el problema del Jellyfin apuntat al [TODO](../TODO.md) (la HD 2500 d'aquest i3 només accelera H.264).

**Però cap de les dues és prioritat ara.** Gastar 60 € en una font per estalviar 17 €/any mentre tot el homelab penja d'un sol disc sense cap còpia de seguretat és invertir en el lloc equivocat. Si han de caure 60 € al homelab, que siguin per un disc de backup.

## A tenir en compte de cara al futur

Dues coses del TODO que van en direcció contrària a tot això:

- **El disc de 3,5" de 2-4 TB.** Són +4-8 W girant 24/7, o sigui +7-14 €/any. Si acaba sent per backups i multimèdia d'accés ocasional, val la pena configurar-li el spindown des del primer dia (`hdparm -S` o `hd-idle`) en comptes de descobrir-ho un any més tard a la gràfica.
- **Prometheus + Grafana.** Cada scrape desperta la CPU i li impedeix baixar a C6. Amb intervals de 15 s per defecte i uns quants exporters, el consum en repòs puja sol. Per un homelab, 30-60 s va perfecte i no es nota gens a les gràfiques.

## Comandes de referència

```bash
# Quins C-states té la CPU i quant els fa servir
for s in /sys/devices/system/cpu/cpu0/cpuidle/state*; do
  printf '%-8s usage=%-10s time=%s us\n' "$(cat $s/name)" "$(cat $s/usage)" "$(cat $s/time)"
done

# Governor i drivers
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_driver
cat /sys/devices/system/cpu/cpuidle/current_driver

# Vista completa amb consum del paquet de CPU (paquet linux-cpupower)
turbostat --quiet --show Busy%,Bzy_MHz,CPU%c1,CPU%c3,CPU%c6,PkgWatt --interval 5

# Estat dels ajustos de powertop
grep -H . /sys/class/scsi_host/host*/link_power_management_policy
cat /sys/module/pcie_aspm/parameters/policy
cat /sys/module/snd_hda_intel/parameters/power_save
```

## Metodologia

El que realment val d'aquest experiment no és el resultat, és el mètode: **canviar una sola cosa, esperar 20-30 minuts amb la màquina tranquil·la, i comparar a la gràfica.**

Si es toquen tres coses alhora no se sap quina ha servit. I si s'actualitza el kernel enmig de l'experiment, encara pitjor, perquè el kernel també influeix en el comportament dels C-states.

Per veure millor els efectes durant les proves es pot baixar una estona `STORE_SECONDS` a 15 al `.env` i tornar-ho a deixar com estava després.
