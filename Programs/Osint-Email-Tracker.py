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
    import requests
    import threading
except Exception as e:
    MissingModule(e)


def CheckTwitter(email, session, timeout):
    try:
        r = session.get("https://api.twitter.com/i/users/email_available.json", params={"email": email}, timeout=timeout)
        if r.status_code == 200:
            return r.json().get("taken", False)
        return False
    except Exception:
        return False

def CheckSpotify(email, session, timeout):
    try:
        r = session.get(
            "https://spclient.wg.spotify.com/signup/public/v1/account",
            headers={"Accept": "application/json, text/plain, */*", "DNT": "1"},
            params={"validate": "1", "email": email},
            timeout=timeout
        )
        if r.status_code == 200:
            return r.json().get("status") == 20
        return False
    except Exception:
        return False

def CheckDeezer(email, session, timeout):
    try:
        r = session.post(
            "https://www.deezer.com/ajax/gw-light.php?method=deezer.getUserData&input=3&api_version=1.0&api_token=&cid=",
            timeout=timeout
        )
        token = r.json()["results"]["checkForm"]
        r2 = session.post(
            "https://www.deezer.com/ajax/gw-light.php",
            params={"method": "deezer.emailCheck", "input": 3, "api_version": 1.0, "api_token": token},
            data=f'{{\"EMAIL\":\"{email}\"}}',
            timeout=timeout
        )
        return r2.json()["results"]["availability"] == False
    except Exception:
        return False

def CheckChess(email, session, timeout):
    try:
        r = session.post(f"https://www.chess.com/callback/email/available?email={email}", timeout=timeout)
        return r.json().get("isEmailAvailable") == False
    except Exception:
        return False

def CheckDuolingo(email, session, timeout):
    try:
        r = session.get("https://www.duolingo.com/2017-06-30/users", params={"email": email}, timeout=timeout)
        return '{"users":[]}' not in r.text
    except Exception:
        return False

def CheckFirefox(email, session, timeout):
    try:
        r = session.post("https://api.accounts.firefox.com/v1/account/status", data={"email": email}, timeout=timeout)
        if r.status_code == 200:
            return "false" not in r.text
        return False
    except Exception:
        return False

def CheckAdobe(email, session, timeout):
    try:
        r = session.post(
            "https://auth.services.adobe.com/signin/v2/users/accounts",
            headers={"x-ims-clientid": "homepage_milo", "content-type": "application/json"},
            json={"username": email, "usernameType": "EMAIL"},
            timeout=timeout
        )
        data = r.json()
        if data and data[0].get("authenticationMethods"):
            return True
        return False
    except Exception:
        return False

def CheckArchive(email, session, timeout):
    try:
        boundary = "---------------------------"
        data = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"input_name\"\r\n\r\nusername\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"input_value\"\r\n\r\n{email}\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"input_validator\"\r\n\r\ntrue\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"submit_by_js\"\r\n\r\ntrue\r\n"
            f"--{boundary}--\r\n"
        )
        r = session.post(
            "https://archive.org/account/signup",
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "Referer": "https://archive.org/account/signup"},
            data=data,
            timeout=timeout
        )
        return r.status_code == 200 and "is already taken" in r.text
    except Exception:
        return False

def CheckPatreon(email, session, timeout):
    try:
        r = session.post(
            "https://www.plurk.com/Users/isEmailFound",
            headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest"},
            data={"email": email},
            timeout=timeout
        )
        return r.status_code == 200 and "True" in r.text
    except Exception:
        return False


PLATFORMS = {
    "X (Twitter)"       : CheckTwitter,
    "Spotify"           : CheckSpotify,
    "Deezer"            : CheckDeezer,
    "Chess"             : CheckChess,
    "Duolingo"          : CheckDuolingo,
    "Firefox (Mozilla)" : CheckFirefox,
    "Adobe"             : CheckAdobe,
    "Archive.org"       : CheckArchive,
    "Patreon/Plurk"     : CheckPatreon,
}


Title("Email Tracker")

Scroll(GradientBanner(osint_banner))

try:
    email = input(f"{INPUT} Email {green}->{reset} ").strip()

    if not email or "@" not in email:
        print(f"{ERROR} Invalid email!", reset)
        Continue()
        Reset()

    timeout = 10
    print(f"{LOADING} Scanning {len(PLATFORMS)} platforms..", reset)

    session = requests.Session()
    session.headers.update({"User-Agent": RandomUserAgents()})

    found    = []
    lock     = threading.Lock()
    sem      = threading.Semaphore(5)

    def CheckPlatform(name, func):
        with sem:
            result = func(email, session, timeout)
            with lock:
                if result:
                    found.append(name)
                    print(f"{SUCCESS} {name:<22}:{green} registegreen{white}", reset)
                else:
                    print(f"{ERROR} {name:<22}:{green} not found{white}", reset)

    threads = [threading.Thread(target=CheckPlatform, args=(n, f), daemon=True) for n, f in PLATFORMS.items()]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"\n{INFO} Found on:{green} {len(found)}/{len(PLATFORMS)} platforms", reset)
    if found:
        for p in found:
            print(f" {SUCCESS} {p}", reset)

    Continue()
    Reset()

except Exception as e:
    Error(e)
