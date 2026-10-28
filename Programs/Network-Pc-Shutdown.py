# Copyright (c) 2025-2026 v4lkyr0 — SINIX
# See the file 'LICENSE' for copying permission.

import subprocess
import socket
import ipaddress
import time
import traceback
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from Core.Utils import *

TIMEOUT     = 0.5
MAX_WORKERS = 100
SINIX_MSG   = "SINIX vous hante."
LOG_FILE    = os.path.join(os.path.dirname(__file__), "..", "sinix_shutdown.log")

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")

def ping(ip):
    result = subprocess.run(
        ["ping", "-n", "1", "-w", str(int(TIMEOUT * 1000)), str(ip)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0

def resolve_name(ip):
    try:
        return socket.gethostbyaddr(str(ip))[0].split(".")[0]
    except socket.herror:
        return str(ip)

def scan_network(network):
    live  = []
    hosts = list(ipaddress.ip_network(network, strict=False).hosts())
    log(f"Scan démarré sur {network} — {len(hosts)} hôtes")
    print(f"\n{LOADING} Scan en cours sur {green}{network}{reset}...\n")

    def check(ip):
        if ping(ip):
            return (str(ip), resolve_name(ip))
        return None

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(check, ip): ip for ip in hosts}
        for f in as_completed(futures):
            r = f.result()
            if r:
                live.append(r)

    live.sort(key=lambda x: socket.inet_aton(x[0]))
    log(f"Scan terminé — {len(live)} machine(s) trouvée(s): {[n for _,n in live]}")
    return live

def shutdown_remote(ip, name):
    log(f"Tentative shutdown -> {name} ({ip})")
    print(f"\n{LOADING} Extinction de {green}{name}{reset} ({ip})...")
    result = subprocess.run(
        ["shutdown", "/s", "/m", f"\\\\{ip}", "/t", "10", "/f", "/c", SINIX_MSG],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        log(f"OK -> {name} ({ip})")
        print(f"{SUCCESS} Commande envoyée à {green}{name}{reset}.")
    else:
        err = result.stderr.strip() or result.stdout.strip() or "Erreur inconnue"
        log(f"ECHEC -> {name} ({ip}) | code={result.returncode} | {err}")
        print(f"{ERROR} Échec {green}{name}{reset}: {err}")

def shutdown_self():
    log("Shutdown self déclenché")
    print(f"\n{LOADING} Extinction de cette machine...")
    subprocess.Popen(
        ["cmd", "/c", f"msg %username% {SINIX_MSG}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(1)
    subprocess.run(
        ["shutdown", "/s", "/t", "5", "/f", "/c", SINIX_MSG],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def shutdown_all(machines):
    log(f"Shutdown ALL déclenché — {len(machines)} machine(s)")
    print(f"\n{LOADING} Extinction de {green}{len(machines)}{reset} machine(s) + cette machine...\n")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(shutdown_remote, ip, name): (ip, name) for ip, name in machines}
        for f in as_completed(futures):
            pass
    print(f"\n{SUCCESS} Commandes envoyées.")
    print(f"{LOADING} Cette machine s'éteint dans 5 secondes...\n")
    time.sleep(2)
    shutdown_self()

def display_machines(machines):
    print(f"\n{green}╓{'─' * 52}╖{reset}")
    print(f"{green}║{white}  {'N°':<6} {'NOM PC':<28} {'IP':<16}{green}║{reset}")
    print(f"{green}╙{'─' * 52}╜{reset}")
    for i, (ip, name) in enumerate(machines, 1):
        print(f"  {PREFIX1}{i}{SUFFIX1} {white}{name:<28}{reset} {green}{ip}{reset}")
    print(f"{green}{'─' * 54}{reset}")

def main():
    log("=== Lancement Network-Pc-Shutdown ===")
    Title("Network PC Shutdown")
    Clear()

    print(f"""
{green}╓──────────────────────────────────────╖{reset}
{green}║{white}       Network PC Shutdown             {green}║{reset}
{green}╙──────────────────────────────────────╜{reset}
""")

    try:
        my_ip = socket.gethostbyname(socket.gethostname())
        log(f"IP locale détectée: {my_ip}")
    except Exception as e:
        my_ip = "192.168.1.1"
        log(f"Erreur détection IP: {e}")

    parts = my_ip.rsplit(".", 1)
    default_net = parts[0] + ".0/24" if len(parts) == 2 else "192.168.1.0/24"

    network = input(f"{INPUT} Plage réseau [{green}{default_net}{reset}] {green}->{reset} ").strip()
    if not network:
        network = default_net

    log(f"Plage choisie: {network}")
    machines = scan_network(network)

    if not machines:
        log("Aucune machine détectée")
        print(f"\n{ERROR} Aucune machine détectée. Vérifie la plage ou le pare-feu.\n")
        input(f"{INPUT} Appuie sur Entrée pour quitter {green}->{reset} ")
        return

    while True:
        Clear()
        display_machines(machines)

        print(f"\n  {PREFIX}A{SUFFIX} Shutdown ALL   {PREFIX}S{SUFFIX} Shutdown moi   {PREFIX}R{SUFFIX} Rescanner   {PREFIX}0{SUFFIX} Quitter\n")
        choice = input(f"{PREFIX}{socket.gethostname()}@SINIX{SUFFIX} {green}->{reset} ").strip().upper()
        log(f"Choix: {choice}")

        if choice == "0":
            log("Quitter")
            break

        if choice == "R":
            machines = scan_network(network)
            continue

        if choice == "S":
            confirm = input(f"\n{INPUT} Éteindre CETTE machine ? {YESORNO} {green}->{reset} ").strip().lower()
            if confirm in ["y", "yes", "o", "oui"]:
                shutdown_self()
            else:
                log("Shutdown self annulé")
                print(f"{ERROR} Annulé.")
            continue

        if choice == "A":
            confirm = input(f"\n{INPUT} Éteindre {green}TOUS{reset} les PC + cette machine ? {YESORNO} {green}->{reset} ").strip().lower()
            if confirm in ["y", "yes", "o", "oui"]:
                shutdown_all(machines)
            else:
                log("Shutdown ALL annulé")
                print(f"{ERROR} Annulé.")
            continue

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(machines):
                ip, name = machines[idx]
                confirm  = input(f"\n{INPUT} Éteindre {green}{name}{reset} ({ip}) ? {YESORNO} {green}->{reset} ").strip().lower()
                if confirm in ["y", "yes", "o", "oui"]:
                    shutdown_remote(ip, name)
                    input(f"\n{INPUT} Entrée pour continuer {green}->{reset} ")
                else:
                    log(f"Shutdown {name} annulé")
                    print(f"{ERROR} Annulé.")
            else:
                print(f"{ERROR} Numéro invalide. Entre 1 et {green}{len(machines)}{reset}.")
                input(f"{INPUT} Entrée pour continuer {green}->{reset} ")
        else:
            print(f"{ERROR} Entrée invalide.")

try:
    main()
except Exception:
    err = traceback.format_exc()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n=== CRASH ===\n{err}\n")
    print(f"\n{ERROR} Erreur critique — consulte {green}sinix_shutdown.log{reset} à la racine du projet.")
    input(f"\n{INPUT} Entrée pour quitter {green}->{reset} ")
