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
    import whois
except Exception as e:
    MissingModule(e)

Title("Whois Lookup")

Scroll(GradientBanner(osint_banner))

try:
    target = input(f"{INPUT} Domain {green}->{reset} ").strip()

    if not target:
        ErrorInput()

    target = target.removeprefix("https://").removeprefix("http://").rstrip("/")

    print(f"{LOADING} Looking up..", reset)

    def Clean(value):
        if not value:
            return "None"
        if isinstance(value, list):
            unique = list(dict.fromkeys([str(v).strip() for v in value if v]))
            return ", ".join(unique[:3]) + (" ..." if len(unique) > 3 else "")
        return str(value).strip() or "None"

    try:
        data = whois.whois(target)

        if not data or not data.domain_name:
            print(f"{ERROR} Could not fetch Whois information!", reset)
            Continue()
            Reset()

        name_servers = data.name_servers
        if isinstance(name_servers, (list, set)):
            name_servers = ", ".join(sorted(set(str(n).lower() for n in name_servers if n)))
        else:
            name_servers = str(name_servers) if name_servers else "None"

        Scroll(f"""
 {SUCCESS} Domain       :{green} {Clean(data.domain_name)}{white}
 {SUCCESS} Registrar    :{green} {Clean(data.registrar)}{white}
 {SUCCESS} Created      :{green} {Clean(data.creation_date)}{white}
 {SUCCESS} Expires      :{green} {Clean(data.expiration_date)}{white}
 {SUCCESS} Updated      :{green} {Clean(data.updated_date)}{white}
 {SUCCESS} Status       :{green} {Clean(data.status)}{white}
 {SUCCESS} Name Servers :{green} {name_servers}{white}
 {SUCCESS} Emails       :{green} {Clean(data.emails)}{white}
 {SUCCESS} Country      :{green} {Clean(data.country)}{white}
 {SUCCESS} State        :{green} {Clean(data.state)}{white}
 {SUCCESS} City         :{green} {Clean(data.city)}{white}
 {SUCCESS} Org          :{green} {Clean(data.org)}{white}
 {SUCCESS} Address      :{green} {Clean(data.address)}{white}
 {SUCCESS} Zipcode      :{green} {Clean(data.zipcode)}{white}
 {SUCCESS} Dnssec       :{green} {Clean(data.dnssec)}{white}
 {SUCCESS} Whois Server :{green} {Clean(data.whois_server)}{white}
""")

    except whois.parser.PywhoisError as e:
        print(f"{ERROR} Whois error:{green} {e}", reset)
    except ConnectionResetError:
        print(f"{ERROR} Connection reset by Whois server!", reset)
    except Exception:
        print(f"{ERROR} Could not fetch Whois information!", reset)

    Continue()
    Reset()

except Exception as e:
    Error(e)