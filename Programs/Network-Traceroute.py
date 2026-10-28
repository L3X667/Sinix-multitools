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
    from icmplib import traceroute
    import socket
except Exception as e:
    MissingModule(e)

Title("Traceroute")

Scroll(GradientBanner(network_banner))

try:
    target = input(f"{INPUT} Host {green}->{reset} ").strip()

    if not target:
        ErrorInput()

    target = target.removeprefix("https://").removeprefix("http://").rstrip("/")

    try:
        resolved = socket.gethostbyname(target)
    except Exception:
        print(f"{ERROR} Could not resolve host!", reset)
        Continue()
        Reset()

    print(f"{INFO} Resolved:{green} {resolved}", reset)
    print(f"{LOADING} Tracerouting..", reset)

    try:
        hops = traceroute(resolved, max_hops=30, timeout=2, privileged=False)

        if not hops:
            print(f"{ERROR} No hops found!", reset)
            Continue()
            Reset()

        last_distance = 0
        total_hops    = 0
        reached       = False

        for hop in hops:
            for missing in range(last_distance + 1, hop.distance):
                print(f"{ERROR} Hop:{green} {missing:<3}{white} | * * * No response.", reset)

            if hop.is_alive:
                try:
                    hostname = socket.gethostbyaddr(hop.address)[0]
                except Exception:
                    hostname = "None"
                print(f"{SUCCESS} Hop:{green} {hop.distance:<3}{white} | Ip:{green} {hop.address:<16}{white} | Time:{green} {round(hop.avg_rtt, 2)}ms{white} | Host:{green} {hostname}", reset)
                total_hops += 1
                if hop.address == resolved:
                    reached = True
            else:
                print(f"{ERROR} Hop:{green} {hop.distance:<3}{white} | * * * Request timed out.", reset)

            last_distance = hop.distance

        print(f"\n{SUCCESS} Hops:{green} {total_hops}{white} | Reached:{green} {'Yes' if reached else 'No'}", reset)

    except PermissionError:
        print(f"{ERROR} Traceroute requires elevated privileges!", reset)
    except Exception:
        print(f"{ERROR} Traceroute failed!", reset)

    Continue()
    Reset()

except Exception as e:
    Error(e)