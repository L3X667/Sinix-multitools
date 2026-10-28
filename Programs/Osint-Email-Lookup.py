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
    import socket
    import smtplib
    import random
    import string
    import re
    import dns.resolver
except Exception as e:
    MissingModule(e)

Title("Email Lookup")

Scroll(GradientBanner(osint_banner))

try:
    email = input(f"{INPUT} Email {green}->{reset} ").strip()

    if not email or "@" not in email:
        print(f"{ERROR} Invalid email!", reset)
        Continue()
        Reset()

    print(f"{LOADING} Analysing..", reset)

    try:
        domain_all = email.split("@")[-1]
    except Exception:
        domain_all = None

    try:
        name = email.split("@")[0]
    except Exception:
        name = None

    try:
        domain = re.search(r"@([^@.]+)\.", email).group(1)
    except Exception:
        domain = None

    try:
        tld = f".{email.split('.')[-1]}"
    except Exception:
        tld = None

    try:
        valid_syntax = re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) is not None
    except Exception:
        valid_syntax = None

    domain_ip = None
    domain_reverse_dns = None
    try:
        domain_ip = socket.gethostbyname(domain_all)
    except Exception:
        pass

    try:
        domain_reverse_dns = socket.gethostbyaddr(domain_ip)[0] if domain_ip else None
    except Exception:
        pass

    domain_mx_servers    = None
    domain_smtp_banner   = None
    domain_starttls      = None
    domain_smtp_check    = None
    domain_catch_all     = None

    try:
        domain_mx_servers = [str(r.exchange).rstrip(".") for r in dns.resolver.resolve(domain_all, "MX")]
        if domain_mx_servers:
            for server in domain_mx_servers:
                try:
                    s = smtplib.SMTP(timeout=10)
                    _, banner           = s.connect(server)
                    domain_smtp_banner  = banner.decode() if isinstance(banner, bytes) else str(banner)
                    s.ehlo()
                    domain_starttls     = s.has_extn("starttls")
                    # SMTP probing is sent directly from the user public IP and may be logged.\n                    s.mail("test@test.com")
                    code_real, _        = s.rcpt(email)
                    fake_local          = "".join(random.choices(string.ascii_lowercase, k=10))
                    code_fake, _        = s.rcpt(f"{fake_local}@{domain_all}")
                    domain_smtp_check   = (code_real == 250)
                    domain_catch_all    = (code_fake == 250)
                    s.quit()
                    break
                except Exception:
                    continue
    except Exception:
        pass

    results = {
        "Email"              : email,
        "Name"               : name,
        "Domain"             : domain,
        "Domain all"         : domain_all,
        "TLD"                : tld,
        "Valid syntax"       : valid_syntax,
        "Domain IP"          : domain_ip,
        "Domain reverse DNS" : domain_reverse_dns,
        "MX servers"         : ", ".join(domain_mx_servers) if domain_mx_servers else None,
        "SMTP banner"        : domain_smtp_banner,
        "STARTTLS"           : domain_starttls,
        "SMTP valid"         : domain_smtp_check,
        "Catch-all"          : domain_catch_all,
    }

    output_lines = []
    for key, val in results.items():
        if val is not None:
            line = f" {SUCCESS} {key:<22}:{green} {val}{white}"
            output_lines.append(line)

    Scroll("\n" + "\n".join(output_lines) + "\n")

    Continue()
    Reset()

except Exception as e:
    Error(e)
