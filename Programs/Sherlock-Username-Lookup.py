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
    import threading
    import requests
    from concurrent.futures import ThreadPoolExecutor, as_completed
except Exception as e:
    MissingModule(e)

Title("Sherlock — Username Lookup")

sherlock_banner = f"""{green}
         ███████╗██╗  ██╗███████╗██████╗ ██╗      ██████╗  ██████╗██╗  ██╗
         ██╔════╝██║  ██║██╔════╝██╔══██╗██║     ██╔═══██╗██╔════╝██║ ██╔╝
         ███████╗███████║█████╗  ██████╔╝██║     ██║   ██║██║     █████╔╝
         ╚════██║██╔══██║██╔══╝  ██╔══██╗██║     ██║   ██║██║     ██╔═██╗
         ███████║██║  ██║███████╗██║  ██║███████╗╚██████╔╝╚██████╗██║  ██╗
         ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝
                        {white}Username Lookup — 482 Sites{green}
{reset}"""

Scroll(Gradient(sherlock_banner))

SHERLOCK_DATA_URL = "https://data.sherlockproject.xyz"
TIMEOUT           = 10
MAX_WORKERS       = 30

def load_sites():
    try:
        print(f"{LOADING} Loading site database..", reset)
        response = requests.get(SHERLOCK_DATA_URL, timeout=15)
        if response.status_code != 200:
            print(f"{ERROR} Failed to load site database (HTTP {response.status_code})", reset)
            return None
        data = response.json()
        data.pop("$schema", None)
        print(f"{SUCCESS} Loaded {green}{len(data)}{reset} sites", reset)
        return data
    except requests.exceptions.ConnectionError:
        print(f"{ERROR} No internet connection!", reset)
        return None
    except Exception as e:
        print(f"{ERROR} Failed to load site database: {green}{e}", reset)
        return None

def check_site(site_name, site_data, username):
    url_format = site_data.get("url", "")
    if not url_format:
        return None

    url = url_format.replace("{}", username)

    error_type = site_data.get("errorType", "")
    error_msg  = site_data.get("errorMsg",  "")
    error_code = site_data.get("errorCode",  0)
    error_url  = site_data.get("errorUrl",  "")

    # Username regex check
    regex = site_data.get("regexCheck")
    if regex:
        try:
            if not re.match(regex, username):
                return ("illegal", site_name, url)
        except re.error:
            pass

    headers = {"User-Agent": RandomUserAgents()}

    try:
        response = requests.get(
            url,
            headers         = headers,
            timeout         = TIMEOUT,
            allow_redirects = True,
        )

        status_code = response.status_code

        # WAF detection
        if status_code in (403, 429) or "cloudflare" in response.text.lower()[:500]:
            return ("waf", site_name, url)

        if error_type == "status_code":
            if status_code == 200:
                return ("claimed", site_name, url)
            else:
                return ("available", site_name, url)

        elif error_type == "message":
            if isinstance(error_msg, list):
                found = any(msg in response.text for msg in error_msg)
            else:
                found = error_msg in response.text
            if found:
                return ("available", site_name, url)
            elif status_code == 200:
                return ("claimed", site_name, url)
            else:
                return ("available", site_name, url)

        elif error_type == "response_url":
            if error_url and error_url in response.url:
                return ("available", site_name, url)
            elif status_code == 200:
                return ("claimed", site_name, url)
            else:
                return ("available", site_name, url)

        else:
            if status_code == 200:
                return ("claimed", site_name, url)
            else:
                return ("available", site_name, url)

    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.ConnectionError:
        return None
    except Exception:
        return None

def run_sherlock(username, site_data, only_found=True, show_waf=False):
    found   = []
    waf     = []
    illegal = []
    errors  = 0
    total   = len(site_data)
    done    = 0
    lock    = threading.Lock()

    print(f"\n{LOADING} Scanning {green}{username}{reset} across {green}{total}{reset} sites...\n", reset)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(check_site, site_name, data, username): site_name
            for site_name, data in site_data.items()
        }

        for future in as_completed(futures):
            result = future.result()
            with lock:
                done += 1
                if result is None:
                    errors += 1
                    continue

                status, site_name, url = result

                if status == "claimed":
                    found.append((site_name, url))
                    print(f"  {SUCCESS} {green}{site_name:<24}{reset} {url}", reset)
                elif status == "waf":
                    waf.append((site_name, url))
                    if show_waf:
                        print(f"  {PREFIX}~{SUFFIX} {white}WAF{reset}     {site_name:<24} blocked", reset)
                elif status == "illegal":
                    illegal.append((site_name, url))

    return found, waf, illegal, errors

try:
    username = input(f"{INPUT} Username {green}->{reset} ").strip()

    if not username:
        ErrorInput()
    else:
        print()
        show_waf_choice = input(f"{INPUT} Show WAF-blocked sites? {YESORNO} {green}->{reset} ").strip().lower()
        show_waf        = show_waf_choice in ["y", "yes"]

        site_data = load_sites()

        if site_data:
            print()
            start_time = time.monotonic()

            found, waf, illegal, errors = run_sherlock(username, site_data, show_waf=show_waf)

            elapsed = time.monotonic() - start_time

            print()
            print(f"  {'─' * 60}", reset)
            print(f"  {SUCCESS} Found     : {green}{len(found)}{reset} account(s)", reset)
            print(f"  {PREFIX}~{SUFFIX} WAF       : {white}{len(waf)}{reset} site(s) blocked", reset)
            print(f"  {PREFIX}x{SUFFIX} Illegal   : {white}{len(illegal)}{reset} username format mismatch(es)", reset)
            print(f"  {INFO} Elapsed   : {green}{elapsed:.2f}s{reset}", reset)
            print(f"  {'─' * 60}", reset)

            if found:
                print(f"\n{INFO} Results:\n", reset)
                for site_name, url in sorted(found, key=lambda x: x[0].lower()):
                    print(f"  {green}+{reset}  {site_name:<24} {green}{url}{reset}", reset)

            if not found:
                print(f"\n{ERROR} No accounts found for {green}{username}{reset}", reset)

    Continue()
    Reset()

except KeyboardInterrupt:
    Reset()
except Exception as e:
    Error(e)
