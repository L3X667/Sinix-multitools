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
    import re
    import json
    import time
    import os
    import threading
    import requests
    from concurrent.futures import ThreadPoolExecutor, as_completed
    requests.packages.urllib3.disable_warnings()
except Exception as e:
    MissingModule(e)

Title("Maigret — Username Lookup")

maigret_banner = f"""{green}
    ███╗   ███╗ █████╗ ██╗ ██████╗ ██████╗ ███████╗████████╗
    ████╗ ████║██╔══██╗██║██╔════╝ ██╔══██╗██╔════╝╚══██╔══╝
    ██╔████╔██║███████║██║██║  ███╗██████╔╝█████╗     ██║
    ██║╚██╔╝██║██╔══██║██║██║   ██║██╔══██╗██╔══╝     ██║
    ██║ ╚═╝ ██║██║  ██║██║╚██████╔╝██║  ██║███████╗   ██║
    ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝   ╚═╝
               {white}Username Lookup — 3221 Sites{green}
{reset}"""

Scroll(Gradient(maigret_banner))

DATA_PATH   = os.path.join(tool_path, "Programs", "Maigret", "data.json")
TIMEOUT     = 10
MAX_WORKERS = 30

def load_db():
    if os.path.exists(DATA_PATH):
        print(f"{LOADING} Loading local database..", reset)
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
            sites = d.get("sites", {})
            print(f"{SUCCESS} Loaded {green}{len(sites)}{reset} sites (local)", reset)
            return sites
        except Exception as e:
            print(f"{ERROR} Local DB error: {green}{e}{reset} — trying remote..", reset)

    print(f"{LOADING} Downloading database..", reset)
    try:
        url = "https://raw.githubusercontent.com/soxoj/maigret/main/maigret/resources/data.json"
        r   = requests.get(url, timeout=20)
        if r.status_code == 200:
            d     = r.json()
            sites = d.get("sites", {})
            os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
            with open(DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(d, f)
            print(f"{SUCCESS} Downloaded and cached {green}{len(sites)}{reset} sites", reset)
            return sites
        else:
            print(f"{ERROR} Download failed (HTTP {r.status_code})", reset)
            return None
    except requests.exceptions.ConnectionError:
        print(f"{ERROR} No internet connection!", reset)
        return None
    except Exception as e:
        print(f"{ERROR} {e}", reset)
        return None

def check_site(site_name, site_data, username):
    if site_data.get("disabled"):
        return None

    # Regex check
    regex = site_data.get("regexCheck")
    if regex:
        try:
            if not re.match(regex, username):
                return ("illegal", site_name, site_data.get("url", "").replace("{username}", username))
        except re.error:
            pass

    # Prefer urlProbe for the actual HTTP check
    url_probe = site_data.get("urlProbe") or site_data.get("url", "")
    url_user  = site_data.get("url", "")
    if not url_probe:
        return None

    url_probe = url_probe.replace("{username}", username)
    url_user  = url_user.replace("{username}", username)

    encoding   = site_data.get("encoding", "utf-8")
    check_type = site_data.get("checkType", "message")

    headers = {"User-Agent": RandomUserAgents()}

    try:
        r = requests.get(
            url_probe,
            headers         = headers,
            timeout         = TIMEOUT,
            verify          = False,
            allow_redirects = True,
        )
        status = r.status_code

        try:
            text = r.content.decode(encoding, errors="replace")
        except Exception:
            text = r.text

        # WAF / rate limit
        if status in (403, 429) or "cloudflare" in text.lower()[:300]:
            return ("waf", site_name, url_user)

        if check_type == "status_code":
            if status == 200:
                return ("claimed", site_name, url_user)
            else:
                return ("available", site_name, url_user)

        elif check_type == "message":
            presence = site_data.get("presenseStrs", [])
            absence  = site_data.get("absenceStrs",  [])

            # Absence strings → not found
            if absence and any(s in text for s in absence):
                return ("available", site_name, url_user)
            # Presence strings → found
            if presence and any(s in text for s in presence):
                return ("claimed", site_name, url_user)
            # Fallback on status
            if status == 200:
                return ("claimed", site_name, url_user)
            return ("available", site_name, url_user)

        elif check_type == "response_url":
            error_url = site_data.get("errorUrl", "")
            if error_url and error_url in r.url:
                return ("available", site_name, url_user)
            if status == 200:
                return ("claimed", site_name, url_user)
            return ("available", site_name, url_user)

        else:
            # unknown checkType — best-effort
            presence = site_data.get("presenseStrs", [])
            absence  = site_data.get("absenceStrs",  [])
            if absence and any(s in text for s in absence):
                return ("available", site_name, url_user)
            if presence and any(s in text for s in presence):
                return ("claimed", site_name, url_user)
            if status == 200:
                return ("claimed", site_name, url_user)
            return ("available", site_name, url_user)

    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.ConnectionError:
        return None
    except Exception:
        return None

def run_maigret(username, sites, show_waf=False):
    found   = []
    waf     = []
    illegal = []
    lock    = threading.Lock()

    active_sites = {k: v for k, v in sites.items() if not v.get("disabled")}
    total        = len(active_sites)

    print(f"\n{LOADING} Scanning {green}{username}{reset} across {green}{total}{reset} active sites...\n", reset)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(check_site, name, data, username): name
            for name, data in active_sites.items()
        }
        for future in as_completed(futures):
            result = future.result()
            if result is None:
                continue
            status, site_name, url = result
            with lock:
                if status == "claimed":
                    found.append((site_name, url))
                    print(f"  {SUCCESS} {green}{site_name:<28}{reset} {url}", reset)
                elif status == "waf":
                    waf.append((site_name, url))
                    if show_waf:
                        print(f"  {PREFIX}~{SUFFIX} {white}WAF{reset}     {site_name:<28} blocked", reset)
                elif status == "illegal":
                    illegal.append((site_name, url))

    return found, waf, illegal

try:
    username = input(f"{INPUT} Username {green}->{reset} ").strip()

    if not username:
        ErrorInput()
    else:
        print()
        show_waf_input = input(f"{INPUT} Show WAF-blocked sites? {YESORNO} {green}->{reset} ").strip().lower()
        show_waf       = show_waf_input in ["y", "yes"]

        sites = load_db()

        if sites:
            print()
            start = time.monotonic()

            found, waf, illegal = run_maigret(username, sites, show_waf=show_waf)

            elapsed = time.monotonic() - start

            print()
            print(f"  {'─' * 64}", reset)
            print(f"  {SUCCESS} Found     : {green}{len(found)}{reset} account(s)", reset)
            print(f"  {PREFIX}~{SUFFIX} WAF       : {white}{len(waf)}{reset} site(s) blocked", reset)
            print(f"  {PREFIX}x{SUFFIX} Illegal   : {white}{len(illegal)}{reset} username format mismatch(es)", reset)
            print(f"  {INFO} Elapsed   : {green}{elapsed:.2f}s{reset}", reset)
            print(f"  {'─' * 64}", reset)

            if found:
                print(f"\n{INFO} Results:\n", reset)
                for site_name, url in sorted(found, key=lambda x: x[0].lower()):
                    print(f"  {green}+{reset}  {site_name:<28} {green}{url}{reset}", reset)

            if not found:
                print(f"\n{ERROR} No accounts found for {green}{username}{reset}", reset)

    Continue()
    Reset()

except KeyboardInterrupt:
    Reset()
except Exception as e:
    Error(e)
