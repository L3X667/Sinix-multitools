# Copyright (c) 2025-2026 v4lkyr0 — SINIX
# See the file 'LICENSE' for copying permission.

import subprocess
import os
import sys
import traceback

from Core.Utils import *

ANIMATIONS = [
    ("bnr",            "ascii.live/bnr"),
    ("knot",           "ascii.live/knot"),
    ("earth",          "ascii.live/earth"),
    ("batman",         "ascii.live/batman"),
    ("coin",           "ascii.live/coin"),
    ("donut",          "ascii.live/donut"),
    ("hes",            "ascii.live/hes"),
    ("spidyswing",     "ascii.live/spidyswing"),
    ("maxwell",        "ascii.live/maxwell"),
    ("kitty",          "ascii.live/kitty"),
    ("batman-running", "ascii.live/batman-running"),
    ("dvd",            "ascii.live/dvd"),
    ("nyan",           "ascii.live/nyan"),
    ("torus-knot",     "ascii.live/torus-knot"),
    ("purdue",         "ascii.live/purdue"),
    ("bomb",           "ascii.live/bomb"),
    ("india",          "ascii.live/india"),
    ("can-you-hear-me","ascii.live/can-you-hear-me"),
    ("clock",          "ascii.live/clock"),
    ("parrot",         "ascii.live/parrot"),
    ("playstation",    "ascii.live/playstation"),
    ("as",             "ascii.live/as"),
    ("forrest",        "ascii.live/forrest"),
    ("parrot.live",    "parrot.live"),
    ("rick",           "ascii.live/rick"),
]

COLS = 2
COL_W = 32

def display_menu():
    Clear()
    print(f"""
{green}╓──────────────────────────────────────────────────╖{reset}
{green}║{white}             ASCII Live Animations               {green}║{reset}
{green}╙──────────────────────────────────────────────────╜{reset}
""")
    for i, (name, url) in enumerate(ANIMATIONS, 1):
        num   = f"{PREFIX1}{str(i).zfill(2)}{SUFFIX1}"
        label = f"{white}{name}{reset}"
        line  = f"  {num} {label}"
        if i % COLS == 1:
            print(line, end="")
        else:
            # Pad left column to fixed width then print right column
            visible_left = len(line) - (len(str(i).zfill(2)) * 0 )  # approx
            print(f"{line}")
            # Simpler: just print each on its own line for clean display
    # Reprint cleanly one per line
    pass

def display_menu_clean():
    Clear()
    print(f"""
{green}╓──────────────────────────────────────────────────────╖{reset}
{green}║{white}               ASCII Live Animations                 {green}║{reset}
{green}╙──────────────────────────────────────────────────────╜{reset}
""")

    # Two-column layout
    total = len(ANIMATIONS)
    mid   = (total + 1) // 2

    left_items  = ANIMATIONS[:mid]
    right_items = ANIMATIONS[mid:]

    for i in range(mid):
        li = left_items[i]
        ln = i + 1
        left_str  = f"  {PREFIX1}{str(ln).zfill(2)}{SUFFIX1} {white}{li[0]:<20}{reset}"

        if i < len(right_items):
            ri  = right_items[i]
            rn  = mid + i + 1
            right_str = f"  {PREFIX1}{str(rn).zfill(2)}{SUFFIX1} {white}{ri[0]}{reset}"
        else:
            right_str = ""

        print(f"{left_str}   {right_str}")

    print(f"\n{green}{'─' * 56}{reset}")
    print(f"  {PREFIX}A{SUFFIX} Toutes (séquence)   {PREFIX}0{SUFFIX} Quitter\n")

def launch_animation(name, url):
    """
    Ouvre un nouveau terminal cmd et lance curl sur l'URL ascii.live.
    Le terminal reste ouvert jusqu'à Ctrl+C côté utilisateur.
    """
    # curl streams indefinitely — /k keeps the window open after Ctrl+C closes curl
    # title set to animation name for easy identification
    cmd = (
        f'start cmd /k "title SINIX :: {name} && '
        f'curl {url}"'
    )
    subprocess.Popen(cmd, shell=True)
    print(f"\n{SUCCESS} Terminal ouvert — animation {green}{name}{reset} en cours.")
    print(f"  {white}Ferme le terminal pour arrêter.{reset}\n")

def launch_all_sequence():
    """
    Lance toutes les animations en séquence dans le même terminal séparé,
    chacune pendant 8 secondes via timeout entre deux curls.
    """
    # Build a chained cmd sequence: curl url & timeout 8 & curl url2 ...
    parts = []
    for name, url in ANIMATIONS:
        parts.append(f"echo. && echo [{name}] && curl {url}")

    # Each animation streams forever — we use a background approach instead:
    # open one terminal per animation with a 5s timeout wrapping curl
    print(f"\n{LOADING} Lancement de {green}{len(ANIMATIONS)}{reset} animations en séquence...\n")
    for name, url in ANIMATIONS:
        cmd = (
            f'start cmd /k "title SINIX :: {name} && '
            f'curl {url}"'
        )
        subprocess.Popen(cmd, shell=True)
        print(f"  {PREFIX1}✓{SUFFIX1} {white}{name}{reset}")

    print(f"\n{SUCCESS} {green}{len(ANIMATIONS)}{reset} terminaux ouverts.\n")

def main():
    Title("ASCII Live Animations")

    while True:
        display_menu_clean()

        choice = input(f"{PREFIX}{os.environ.get('USERNAME', 'SINIX')}@SINIX{SUFFIX} {green}->{reset} ").strip().upper()

        if choice == "0":
            break

        if choice == "A":
            confirm = input(f"\n{INPUT} Ouvrir {green}{len(ANIMATIONS)}{reset} terminaux ? {YESORNO} {green}->{reset} ").strip().lower()
            if confirm in ["y", "yes", "o", "oui"]:
                launch_all_sequence()
                input(f"\n{INPUT} Entrée pour continuer {green}->{reset} ")
            else:
                print(f"{ERROR} Annulé.")
            continue

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(ANIMATIONS):
                name, url = ANIMATIONS[idx]
                launch_animation(name, url)
                input(f"{INPUT} Entrée pour continuer {green}->{reset} ")
            else:
                print(f"\n{ERROR} Numéro invalide. Entre {green}01{reset} et {green}{len(ANIMATIONS)}{reset}.\n")
                input(f"{INPUT} Entrée pour continuer {green}->{reset} ")
        else:
            print(f"\n{ERROR} Entrée invalide.\n")

try:
    main()
except Exception:
    err = traceback.format_exc()
    print(f"\n{ERROR} Erreur critique:\n{err}")
    input(f"\n{INPUT} Entrée pour quitter {green}->{reset} ")
