# Copyright (c) 2025-2026 v4lkyr0 — SINIX
# See the file 'LICENSE' for copying permission.
# --------------------------------------------------------
# EN: Non-commercial use only. Do not sell, remove credits
#     or redistribute without prior written permission.
# FR: Usage non-commercial uniquement. Ne pas vendre, supprimer
#     les crédits ou redistribuer sans autorisation écrite.

from Core.Utils import *
from Core.Config import *

import webbrowser

Title("Osint Web")

SITES = {
    "01": ("Sherlock Osint",    "https://sherlockosint.com/"),
    "02": ("See Know",          "https://see-know.ru/"),
    "03": ("Oathnet",           "https://oathnet.org"),
    "04": ("Brixhub",           "https://brixhub.to"),
    "05": ("Zsearcher",         "https://zsearcher.net/"),
    "06": ("Intelbyte",         "https://www.intelbyte.cc/"),
    "07": ("Stryxx",            "https://stryxx.net"),
    "08": ("Eldia Studio",      "https://eldia-studio.eu/"),
    "09": ("Osintcat",          "https://www.osintcat.net/register"),
    "10": ("Osint Framework",   "https://osintframework.com"),
    "11": ("X-Ray Contact",     "https://x-ray.contact/"),
    "12": ("IntelX",            "https://intelx.io/"),
    "13": ("LeakCheck",         "https://leakcheck.io/"),
    "14": ("Osint Leak",        "https://osintleak.com/fr"),
    "15": ("Osint Catalog",     "https://osint-catalog.xyz/"),
    "16": ("Ghunt",             "https://ghunt.org/"),
    "17": ("Holehe",            "https://holehe.online/fr"),
    "18": ("Deadeye",           "https://deadeye.cc"),
    "19": ("Open Archive",      "https://openarchive.lol/"),
    "20": ("Kerbes",            "https://kerbes.org/signin?redirectTo=%2Fdashboard"),
    "21": ("Tracked",           "https://tracked.sh"),
    "22": ("SwattedW",          "https://swattedw.tf/#pricing"),
}

try:
    Clear()

    print(f"""
{green}╓──────────────────────────────────────────────────────────────────────────╖
                              Osint Web                                     
╙┬─────────────────────────────────────────────────────────────────────────╜{reset}""")

    keys = list(SITES.keys())
    half = (len(keys) + 1) // 2

    left  = keys[:half]
    right = keys[half:]

    for i in range(half):
        lk = left[i]
        ln, _ = SITES[lk]
        lprefix = "└─" if i == half - 1 and len(right) <= i else "├─"

        if i < len(right):
            rk = right[i]
            rn, _ = SITES[rk]
            rprefix = "└─" if i == len(right) - 1 else "├─"
            print(f" {lprefix} {PREFIX1}{lk}{SUFFIX1} {ln:<25}   {rprefix} {PREFIX1}{rk}{SUFFIX1} {rn}")
        else:
            print(f" {lprefix} {PREFIX1}{lk}{SUFFIX1} {ln}")

    print()
    choice = input(f"{PREFIX}{username_pc}@SINIX{SUFFIX} {green}->{reset} ").strip().zfill(2)

    if choice in SITES:
        name, url = SITES[choice]
        print(f"\n{INFO} Opening {green}{name}{reset}...")
        webbrowser.open(url)
        print(f"{SUCCESS} Opened {green}{url}{reset}")
    else:
        ErrorFeature()

    Continue()
    Reset()

except Exception as e:
    Error(e)
