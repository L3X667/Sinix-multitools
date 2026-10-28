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
    import os
    import time
    import requests
    from urllib.parse import urlparse, urljoin
    from bs4 import BeautifulSoup
    requests.packages.urllib3.disable_warnings()
except Exception as e:
    MissingModule(e)

Title("BlackWidow — Web Spider")

blackwidow_banner = f"""{green}
          ██████╗ ██╗      █████╗  ██████╗██╗  ██╗    ██╗    ██╗██╗██████╗  ██████╗ ██╗    ██╗
          ██╔══██╗██║     ██╔══██╗██╔════╝██║ ██╔╝    ██║    ██║██║██╔══██╗██╔═══██╗██║    ██║
          ██████╔╝██║     ███████║██║     █████╔╝     ██║ █╗ ██║██║██║  ██║██║   ██║██║ █╗ ██║
          ██╔══██╗██║     ██╔══██║██║     ██╔═██╗     ██║███╗██║██║██║  ██║██║   ██║██║███╗██║
          ██████╔╝███████╗██║  ██║╚██████╗██║  ██╗    ╚███╔███╔╝██║██████╔╝╚██████╔╝╚███╔███╔╝
          ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝     ╚══╝╚══╝ ╚═╝╚═════╝  ╚═════╝  ╚══╝╚══╝
                         {white}Web Spider — URLs · Subdomains · Emails · Forms{green}
{reset}"""

Scroll(Gradient(blackwidow_banner))

OUTPUT_DIR = os.path.join(tool_path, "Programs", "Output", "BlackWidow")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TIMEOUT    = 10
MAX_DEPTH  = 3

visited    = set()
urls_found       = set()
dynamic_found    = set()
subdomains_found = set()
emails_found     = set()
phones_found     = set()
forms_found      = set()

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(?:\+?\d[\d\s\-().]{7,}\d)")

def parse_url(raw):
    try:
        parsed = urlparse(raw)
        return parsed
    except Exception:
        return None

def crawl(url, base_domain, cookie="", depth=0, max_depth=MAX_DEPTH):
    if url in visited or depth > max_depth:
        return
    visited.add(url)

    try:
        headers = {"User-Agent": RandomUserAgents()}
        if cookie:
            headers["Cookie"] = cookie

        response = requests.get(url, headers=headers, timeout=TIMEOUT, verify=False)
        html     = response.text
    except requests.exceptions.Timeout:
        return
    except requests.exceptions.ConnectionError:
        return
    except Exception:
        return

    soup = BeautifulSoup(html, "lxml")

    print(f"\n  {green}{'─' * 70}{reset}", reset)
    print(f"  {INFO} {green}{url}{reset}", reset)
    print(f"  {green}{'─' * 70}{reset}", reset)

    # --- FORMS ---
    for form in soup.find_all("form"):
        if url not in forms_found:
            forms_found.add(url)
            print(f"  {PREFIX}F{SUFFIX} {white}Form found       {reset}{url}", reset)

    # --- EMAILS from mailto + regex in body ---
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.startswith("mailto:"):
            email = href[7:].split("?")[0].strip()
            if email and email not in emails_found:
                emails_found.add(email)
                print(f"  {PREFIX}@{SUFFIX} {white}Email found      {reset}{green}{email}{reset}", reset)

    for email in EMAIL_RE.findall(html):
        if email not in emails_found:
            emails_found.add(email)
            print(f"  {PREFIX}@{SUFFIX} {white}Email found      {reset}{green}{email}{reset}", reset)

    # --- PHONES from tel: links ---
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.startswith("tel:"):
            phone = href[4:].strip()
            if phone and phone not in phones_found:
                phones_found.add(phone)
                print(f"  {PREFIX}#{SUFFIX} {white}Phone found      {reset}{green}{phone}{reset}", reset)

    # --- LINKS ---
    next_crawl = []
    for link in soup.find_all("a", href=True):
        href = link["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        full_url = urljoin(url, href)
        parsed   = parse_url(full_url)
        if not parsed:
            continue

        link_domain = parsed.netloc.split(":")[0]

        # Subdomain detection
        if link_domain and link_domain != base_domain and base_domain in link_domain:
            if link_domain not in subdomains_found:
                subdomains_found.add(link_domain)
                print(f"  {PREFIX}S{SUFFIX} {white}Subdomain found  {reset}{green}{link_domain}{reset}", reset)

        # Same-origin only for crawling
        if base_domain not in link_domain:
            continue

        # Dynamic URL
        if "?" in full_url:
            if full_url not in dynamic_found:
                dynamic_found.add(full_url)
                urls_found.add(full_url)
                print(f"  {PREFIX}D{SUFFIX} {white}Dynamic URL      {reset}{green}{full_url}{reset}", reset)
        else:
            if full_url not in urls_found:
                urls_found.add(full_url)
                print(f"  {PREFIX}+{SUFFIX} {white}URL found        {reset}{full_url}", reset)

        if full_url not in visited:
            next_crawl.append(full_url)

    # Recurse
    for next_url in next_crawl:
        crawl(next_url, base_domain, cookie=cookie, depth=depth + 1, max_depth=max_depth)

def save_results(domain):
    base = os.path.join(OUTPUT_DIR, domain)
    os.makedirs(base, exist_ok=True)

    def write(filename, data):
        path = os.path.join(base, filename)
        with open(path, "w", encoding="utf-8") as f:
            for line in sorted(data):
                f.write(line + "\n")
        return path

    paths = {}
    paths["urls"]       = write("urls.txt",       urls_found)
    paths["dynamic"]    = write("dynamic.txt",    dynamic_found)
    paths["subdomains"] = write("subdomains.txt", subdomains_found)
    paths["emails"]     = write("emails.txt",     emails_found)
    paths["phones"]     = write("phones.txt",     phones_found)
    paths["forms"]      = write("forms.txt",      forms_found)
    return base, paths

def print_summary(domain, elapsed, base, paths):
    print(f"\n  {green}{'═' * 70}{reset}", reset)
    print(f"  {SUCCESS} Scan complete for {green}{domain}{reset} in {green}{elapsed:.2f}s{reset}", reset)
    print(f"  {green}{'─' * 70}{reset}", reset)
    print(f"  {PREFIX}+{SUFFIX} URLs found       : {green}{len(urls_found)}{reset}", reset)
    print(f"  {PREFIX}D{SUFFIX} Dynamic URLs     : {green}{len(dynamic_found)}{reset}", reset)
    print(f"  {PREFIX}S{SUFFIX} Subdomains       : {green}{len(subdomains_found)}{reset}", reset)
    print(f"  {PREFIX}@{SUFFIX} Emails           : {green}{len(emails_found)}{reset}", reset)
    print(f"  {PREFIX}#{SUFFIX} Phones           : {green}{len(phones_found)}{reset}", reset)
    print(f"  {PREFIX}F{SUFFIX} Forms            : {green}{len(forms_found)}{reset}", reset)
    print(f"  {green}{'─' * 70}{reset}", reset)
    print(f"  {INFO} Output saved to  : {green}{base}{reset}", reset)
    print(f"  {green}{'═' * 70}{reset}\n", reset)

try:
    target_url = input(f"{INPUT} Target URL (ex: https://example.com) {green}->{reset} ").strip()

    if not target_url:
        ErrorInput()
    else:
        if not target_url.startswith("http"):
            target_url = "https://" + target_url

        parsed_target = urlparse(target_url)
        base_domain   = parsed_target.netloc.split(":")[0]

        if not base_domain:
            ErrorUrl()
        else:
            depth_input = input(f"{INPUT} Crawl depth (default: 3) {green}->{reset} ").strip()
            max_depth   = int(depth_input) if depth_input.isdigit() else 3

            cookie_input = input(f"{INPUT} Cookie (leave empty to skip) {green}->{reset} ").strip()

            print(f"\n{LOADING} Starting BlackWidow on {green}{target_url}{reset} — depth {green}{max_depth}{reset}", reset)

            start_time = time.monotonic()

            crawl(target_url, base_domain, cookie=cookie_input, depth=0, max_depth=max_depth)

            elapsed          = time.monotonic() - start_time
            base, paths      = save_results(base_domain)

            print_summary(base_domain, elapsed, base, paths)

    Continue()
    Reset()

except KeyboardInterrupt:
    Reset()
except Exception as e:
    Error(e)
