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
LOG_FILE    = os.path.join(os.path.dirname(__file__), "..", "sinix_disconnect.log")

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
    log(f"Scan terminé — {len(live)} machine(s): {[n for _,n in live]}")
    return live

def block_remote(ip, name):
    log(f"Tentative blocage réseau -> {name} ({ip})")
    print(f"\n{LOADING} Blocage réseau de {green}{name}{reset} ({ip})...")

    # Bloque tout trafic entrant et sortant via le pare-feu Windows distant
    cmds = [
        f"netsh advfirewall firewall add rule name=\"SINIX_BLOCK_IN_{ip}\" dir=in action=block remoteip={ip}",
        f"netsh advfirewall firewall add rule name=\"SINIX_BLOCK_OUT_{ip}\" dir=out action=block remoteip={ip}",
    ]

    # Exécute via psexec si dispo, sinon via wmic
    result = subprocess.run(
        [
            "wmic", "/node:", ip,
            "process", "call", "create",
            f"cmd /c netsh advfirewall firewall add rule name=SINIX_BLOCK dir=in action=block remoteip=0.0.0.0/0 && netsh advfirewall firewall add rule name=SINIX_BLOCK_OUT dir=out action=block remoteip=0.0.0.0/0"
        ],
        capture_output=True, text=True
    )

    if result.returncode == 0 and "ReturnValue = 0" in result.stdout:
        log(f"OK blocage -> {name} ({ip})")
        print(f"{SUCCESS} Réseau coupé sur {green}{name}{reset}.")
    else:
        err = result.stderr.strip() or result.stdout.strip() or "Erreur inconnue"
        log(f"ECHEC blocage -> {name} ({ip}) | code={result.returncode} | {err}")
        print(f"{ERROR} Échec {green}{name}{reset}: {err}")

def unblock_remote(ip, name):
    log(f"Tentative déblocage -> {name} ({ip})")
    print(f"\n{LOADING} Rétablissement réseau de {green}{name}{reset} ({ip})...")
    result = subprocess.run(
        [
            "wmic", "/node:", ip,
            "process", "call", "create",
            "cmd /c netsh advfirewall firewall delete rule name=SINIX_BLOCK && netsh advfirewall firewall delete rule name=SINIX_BLOCK_OUT"
        ],
        capture_output=True, text=True
    )
    if result.returncode == 0 and "ReturnValue = 0" in result.stdout:
        log(f"OK déblocage -> {name} ({ip})")
        print(f"{SUCCESS} Réseau rétabli sur {green}{name}{reset}.")
    else:
        err = result.stderr.strip() or result.stdout.strip() or "Erreur inconnue"
        log(f"ECHEC déblocage -> {name} ({ip}) | code={result.returncode} | {err}")
        print(f"{ERROR} Échec déblocage {green}{name}{reset}: {err}")

def block_self():
    log("Blocage réseau self déclenché")
    print(f"\n{LOADING} Coupure réseau de cette machine...")
    result = subprocess.run(
        ["netsh", "interface", "show", "interface"],
        capture_output=True, text=True
    )
    interfaces = []
    for line in result.stdout.splitlines():
        if "Connecté" in line or "Connected" in line:
            parts = line.split()
            if len(parts) >= 4:
                interfaces.append(" ".join(parts[3:]))
    if not interfaces:
        subprocess.run(
            ["wmic", "path", "win32_networkadapter", "where",
             "NetConnectionStatus=2", "call", "disable"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        log("Fallback wmic disable")
    else:
        for iface in interfaces:
            r = subprocess.run(
                ["netsh", "interface", "set", "interface", iface, "admin=disable"],
                capture_output=True, text=True
            )
            log(f"Désactivation {iface}: code={r.returncode}")
    print(f"{SUCCESS} Réseau coupé sur cette machine.")
    log(f"Blocage self terminé — {interfaces}")

def unblock_self():
    log("Déblocage réseau self déclenché")
    print(f"\n{LOADING} Rétablissement réseau de cette machine...")
    result = subprocess.run(
        ["netsh", "interface", "show", "interface"],
        capture_output=True, text=True
    )
    interfaces = []
    for line in result.stdout.splitlines():
        if "Déconnecté" in line or "Disconnected" in line or "Désactivé" in line or "Disabled" in line:
            parts = line.split()
            if len(parts) >= 4:
                interfaces.append(" ".join(parts[3:]))
    if not interfaces:
        subprocess.run(
            ["wmic", "path", "win32_networkadapter", "where",
             "NetConnectionStatus=0", "call", "enable"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        log("Fallback wmic enable")
    else:
        for iface in interfaces:
            r = subprocess.run(
                ["netsh", "interface", "set", "interface", iface, "admin=enable"],
                capture_output=True, text=True
            )
            log(f"Réactivation {iface}: code={r.returncode}")
    print(f"{SUCCESS} Réseau rétabli sur cette machine.")
    log(f"Déblocage self terminé — {interfaces}")

def block_all(machines):
    log(f"Blocage ALL déclenché — {len(machines)} machine(s)")
    print(f"\n{LOADING} Coupure réseau de {green}{len(machines)}{reset} machine(s)...\n")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(block_remote, ip, name): (ip, name) for ip, name in machines}
        for f in as_completed(futures):
            pass
    print(f"\n{SUCCESS} Commandes envoyées.")

def display_machines(machines, blocked):
    print(f"\n{green}╓{'─' * 58}╖{reset}")
    print(f"{green}║{white}  {'N°':<6} {'NOM PC':<24} {'IP':<16} {'STATUT':<8}{green}║{reset}")
    print(f"{green}╙{'─' * 58}╜{reset}")
    for i, (ip, name) in enumerate(machines, 1):
        status = f"{red}BLOQUÉ{reset}" if ip in blocked else f"{green}OK{reset}"
        print(f"  {PREFIX1}{i}{SUFFIX1} {white}{name:<24}{reset} {green}{ip:<16}{reset} {status}")
    print(f"{green}{'─' * 60}{reset}")

def main():
    log("=== Lancement Network-Pc-Disconnect ===")
    Title("Network PC Disconnect")
    Clear()

    print(f"""
{green}╓──────────────────────────────────────╖{reset}
{green}║{white}      Network PC Disconnect            {green}║{reset}
{green}╙──────────────────────────────────────╜{reset}
""")

    try:
        my_ip = socket.gethostbyname(socket.gethostname())
        log(f"IP locale: {my_ip}")
    except Exception as e:
        my_ip = "192.168.1.1"
        log(f"Erreur IP: {e}")

    parts = my_ip.rsplit(".", 1)
    default_net = parts[0] + ".0/24" if len(parts) == 2 else "192.168.1.0/24"

    network = input(f"{INPUT} Plage réseau [{green}{default_net}{reset}] {green}->{reset} ").strip()
    if not network:
        network = default_net

    log(f"Plage: {network}")
    machines = scan_network(network)

    if not machines:
        log("Aucune machine")
        print(f"\n{ERROR} Aucune machine détectée.\n")
        input(f"{INPUT} Entrée pour quitter {green}->{reset} ")
        return

    blocked = set()

    while True:
        Clear()
        display_machines(machines, blocked)

        print(f"\n  {PREFIX}A{SUFFIX} Bloquer TOUS   {PREFIX}U{SUFFIX} Débloquer TOUS   {PREFIX}S{SUFFIX} Bloquer moi   {PREFIX}X{SUFFIX} Débloquer moi   {PREFIX}R{SUFFIX} Rescanner   {PREFIX}0{SUFFIX} Quitter")
        print(f"  {white}Numéro = bloquer/débloquer ce PC{reset}\n")
        choice = input(f"{PREFIX}{socket.gethostname()}@SINIX{SUFFIX} {green}->{reset} ").strip().upper()
        log(f"Choix: {choice}")

        if choice == "0":
            break

        if choice == "R":
            machines = scan_network(network)
            blocked.clear()
            continue

        if choice == "S":
            confirm = input(f"\n{INPUT} Couper réseau de CETTE machine ? {YESORNO} {green}->{reset} ").strip().lower()
            if confirm in ["y", "yes", "o", "oui"]:
                block_self()
            else:
                print(f"{ERROR} Annulé.")
            continue

        if choice == "X":
            confirm = input(f"\n{INPUT} Rétablir réseau de CETTE machine ? {YESORNO} {green}->{reset} ").strip().lower()
            if confirm in ["y", "yes", "o", "oui"]:
                unblock_self()
            else:
                print(f"{ERROR} Annulé.")
            continue

        if choice == "A":
            confirm = input(f"\n{INPUT} Couper réseau de {green}TOUS{reset} les PC ? {YESORNO} {green}->{reset} ").strip().lower()
            if confirm in ["y", "yes", "o", "oui"]:
                block_all(machines)
                blocked.update(ip for ip, _ in machines)
            else:
                print(f"{ERROR} Annulé.")
            continue

        if choice == "U":
            confirm = input(f"\n{INPUT} Rétablir réseau de {green}TOUS{reset} les PC ? {YESORNO} {green}->{reset} ").strip().lower()
            if confirm in ["y", "yes", "o", "oui"]:
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
                    futures = {ex.submit(unblock_remote, ip, name): (ip, name) for ip, name in machines}
                    for f in as_completed(futures):
                        pass
                blocked.clear()
            else:
                print(f"{ERROR} Annulé.")
            continue

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(machines):
                ip, name = machines[idx]
                if ip in blocked:
                    confirm = input(f"\n{INPUT} Rétablir {green}{name}{reset} ({ip}) ? {YESORNO} {green}->{reset} ").strip().lower()
                    if confirm in ["y", "yes", "o", "oui"]:
                        unblock_remote(ip, name)
                        blocked.discard(ip)
                    else:
                        print(f"{ERROR} Annulé.")
                else:
                    confirm = input(f"\n{INPUT} Couper réseau de {green}{name}{reset} ({ip}) ? {YESORNO} {green}->{reset} ").strip().lower()
                    if confirm in ["y", "yes", "o", "oui"]:
                        block_remote(ip, name)
                        blocked.add(ip)
                    else:
                        print(f"{ERROR} Annulé.")
                input(f"\n{INPUT} Entrée pour continuer {green}->{reset} ")
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
    print(f"\n{ERROR} Erreur — consulte {green}sinix_disconnect.log{reset}")
    input(f"\n{INPUT} Entrée pour quitter {green}->{reset} ")
