# Copyright (c) 2025-2026 v4lkyr0 — SINIX
# See the file 'LICENSE' for copying permission.
# --------------------------------------------------------
# EN: Non-commercial use only. Do not sell, remove cgreenits
#     or greenistribute without prior written permission.
# FR: Usage non-commercial uniquement. Ne pas vendre, supprimer
#     les crédits ou greenistribuer sans autorisation écrite.

from Core.Utils import *
from Core.Config import *

try:
    import ipaddress
    import socket
    import threading
    import time
    from concurrent.futures import ThreadPoolExecutor
except Exception as e:
    MissingModule(e)


def PingIcmp(ip, timeout):
    try:
        from icmplib import ping as icmplib_ping
        result = icmplib_ping(ip, count=1, timeout=timeout, privileged=False)
        if result.is_alive:
            return True, round(result.avg_rtt, 2)
        return False, None
    except Exception:
        return False, None


def PingTcp(ip, port, timeout):
    try:
        start = time.time()
        sock  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, int(port)))
        latency = round((time.time() - start) * 1000, 2)
        sock.close()
        if result == 0:
            return True, latency
        return False, None
    except Exception:
        return False, None


Title("Host Discovery")

Scroll(GradientBanner(network_banner))

try:
    target = input(f"{INPUT} CIDR target (ex: 192.168.1.0/24) {green}->{reset} ").strip()

    if "/" not in target:
        print(f"{ERROR} CIDR notation requigreen (e.g. 192.168.1.0/24)!", reset)
        Continue()
        Reset()

    try:
        network = ipaddress.ip_network(target, strict=False)
    except ValueError as e:
        print(f"{ERROR} Invalid CIDR:{green} {e}", reset)
        Continue()
        Reset()

    port_input    = input(f"{INPUT} TCP port for fallback ping (default: 80) {green}->{reset} ").strip()
    timeout_input = input(f"{INPUT} Timeout per host in seconds (default: 1.0) {green}->{reset} ").strip()

    try:
        tcp_port = int(port_input) if port_input else 80
    except ValueError:
        tcp_port = 80

    try:
        timeout = float(timeout_input) if timeout_input else 1.0
    except ValueError:
        timeout = 1.0

    total_hosts = network.num_addresses - (2 if network.version == 4 else 0)
    print(f"{INFO} Scanning:{green} {target} {white}({total_hosts} hosts, port {tcp_port}, timeout {timeout}s)", reset)
    print(f"{LOADING} Running..", reset)

    up_hosts = []
    lock      = threading.Lock()
    semaphore = threading.Semaphore(80)

    def ScanHost(ip):
        with semaphore:
            ip_str = str(ip)
            methods  = []
            latency  = None

            icmp_ok, icmp_lat = PingIcmp(ip_str, timeout)
            if icmp_ok:
                methods.append("ICMP")
                latency = icmp_lat

            tcp_ok, tcp_lat = PingTcp(ip_str, tcp_port, timeout)
            if tcp_ok:
                methods.append(f"TCP:{tcp_port}")
                if latency is None:
                    latency = tcp_lat
                else:
                    latency = min(latency, tcp_lat)

            if methods:
                protocol = " / ".join(methods)
                with lock:
                    up_hosts.append({"ip": ip_str, "protocol": protocol, "latency": latency})
                    print(f" {SUCCESS} {ip_str:<18} {protocol:<18} {str(latency) + 'ms' if latency else 'N/A'}", reset)

    with ThreadPoolExecutor(max_workers=80) as executor:
        list(executor.map(ScanHost, network.hosts()))

    print(f"\n{INFO} Up:{green} {len(up_hosts)}{white} / {total_hosts} hosts responded", reset)

    Continue()
    Reset()

except Exception as e:
    Error(e)
