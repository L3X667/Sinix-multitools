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
    import datetime
except Exception as e:
    MissingModule(e)


def SafeGet(session, url, timeout, method="get", payload=None):
    try:
        if method == "post":
            r = session.post(url, json=payload, timeout=timeout)
        else:
            r = session.get(url, timeout=timeout)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None


def NormalizeTimestamp(raw):
    if raw is None:
        return None
    try:
        if isinstance(raw, datetime.datetime):
            return raw
        if isinstance(raw, (int, float)):
            return datetime.datetime.fromtimestamp(int(raw))
        if isinstance(raw, str):
            return datetime.datetime.fromisoformat(raw.replace("Z", ""))
    except Exception:
        return None
    return None


def FetchEvm(address, session, timeout, api_url, chain):
    out = []
    data = SafeGet(session, f"{api_url}/api?module=account&action=txlist&address={address}&sort=desc", timeout)
    if not isinstance(data, dict):
        return out
    result = data.get("result")
    if not isinstance(result, list):
        return out
    for tx in result[:30]:
        if not isinstance(tx, dict):
            continue
        out.append({
            "chain"          : chain,
            "transaction_id" : tx.get("hash"),
            "value"          : int(tx.get("value", 0)) / 1e18,
            "date"           : NormalizeTimestamp(tx.get("timeStamp")),
        })
    return out


def FetchBtc(address, session, timeout):
    out = []
    data = SafeGet(session, f"https://mempool.space/api/address/{address}/txs", timeout)
    if not isinstance(data, list):
        return out
    for tx in data:
        if not isinstance(tx, dict):
            continue
        value = 0
        for v in tx.get("vout", []):
            if isinstance(v, dict) and v.get("scriptpubkey_address") == address:
                value += v.get("value", 0)
        status = tx.get("status", {})
        out.append({
            "chain"          : "BTC",
            "transaction_id" : tx.get("txid"),
            "value"          : value / 1e8,
            "date"           : NormalizeTimestamp(status.get("block_time") if isinstance(status, dict) else None),
        })
    return out


def FetchSol(address, session, timeout):
    out  = []
    url  = "https://api.mainnet-beta.solana.com"
    sigs = SafeGet(session, url, timeout, "post", {"jsonrpc": "2.0", "id": 1, "method": "getSignaturesForAddress", "params": [address]})
    if not sigs or "result" not in sigs:
        return out
    for s in sigs["result"]:
        sig   = s.get("signature")
        tx    = SafeGet(session, url, timeout, "post", {"jsonrpc": "2.0", "id": 1, "method": "getTransaction", "params": [sig, "jsonParsed"]})
        value = None
        try:
            if tx and tx.get("result"):
                meta = tx["result"].get("meta", {})
                pre  = meta.get("preBalances", [])
                post = meta.get("postBalances", [])
                if pre and post:
                    value = abs(sum(post) - sum(pre)) / 1e9
        except Exception:
            value = None
        out.append({"chain": "SOL", "transaction_id": sig, "value": value, "date": NormalizeTimestamp(s.get("blockTime"))})
    return out


def FetchTron(address, session, timeout):
    out  = []
    data = SafeGet(session, f"https://apilist.tronscanapi.com/api/transaction?address={address}&limit=999999", timeout)
    if not isinstance(data, dict):
        return out
    items = data.get("data")
    if not isinstance(items, list):
        return out
    for tx in items:
        if not isinstance(tx, dict):
            continue
        ts = tx.get("timestamp")
        out.append({
            "chain"          : "TRX",
            "transaction_id" : tx.get("hash"),
            "value"          : float(tx.get("amount", 0) or 0) / 1e6,
            "date"           : NormalizeTimestamp(int(ts) / 1000 if ts else None),
        })
    return out


def FetchLtc(address, session, timeout):
    out  = []
    data = SafeGet(session, f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}", timeout)
    if not isinstance(data, dict):
        return out
    txs = data.get("txrefs", [])
    if not isinstance(txs, list):
        return out
    for tx in txs:
        if not isinstance(tx, dict):
            continue
        val = tx.get("value", 0)
        if not isinstance(val, (int, float)):
            val = 0
        out.append({
            "chain"          : "LTC",
            "transaction_id" : tx.get("tx_hash"),
            "value"          : val / 1e8,
            "date"           : NormalizeTimestamp(tx.get("confirmed")),
        })
    return out


def FetchXrp(address, session, timeout):
    out  = []
    data = SafeGet(session, "https://s1.ripple.com:51234/", timeout, "post",
                   {"method": "account_tx", "params": [{"account": address, "ledger_index_min": -1, "ledger_index_max": -1, "binary": False}]})
    if not isinstance(data, dict):
        return out
    txs = data.get("result", {}).get("transactions", [])
    for item in txs:
        tx     = item.get("tx", {})
        amount = tx.get("Amount")
        value  = 0
        if isinstance(amount, dict):
            try:
                value = float(amount.get("value", 0))
            except Exception:
                value = 0
        elif isinstance(amount, str):
            try:
                value = int(amount) / 1e6
            except Exception:
                value = 0
        raw_date = tx.get("date")
        date     = None
        if isinstance(raw_date, (int, float)):
            date = datetime.datetime.fromtimestamp(raw_date + 946684800)
        out.append({"chain": "XRP", "transaction_id": tx.get("hash"), "value": value, "date": date})
    return out


Title("Wallet Tracker")

Scroll(GradientBanner(osint_banner))

try:
    address = input(f"{INPUT} Wallet address {green}->{reset} ").strip()

    if not address:
        ErrorInput()

    print(f"{LOADING} Scanning chains (ETH, POLYGON, FTM, AVAX, BSC, BTC, SOL, TRX, LTC, XRP)..", reset)

    session = requests.Session()
    session.headers.update({"User-Agent": RandomUserAgents()})
    timeout = 15

    txs = []
    txs += FetchEvm(address, session, timeout, "https://eth.blockscout.com",       "ETH")
    txs += FetchEvm(address, session, timeout, "https://polygon.blockscout.com",   "POLYGON")
    txs += FetchEvm(address, session, timeout, "https://ftm.blockscout.com",       "FTM")
    txs += FetchEvm(address, session, timeout, "https://snowtrace.blockscout.com", "AVAX")
    txs += FetchEvm(address, session, timeout, "https://bsc.blockscout.com",       "BSC")
    txs += FetchBtc(address, session, timeout)
    txs += FetchSol(address, session, timeout)
    txs += FetchTron(address, session, timeout)
    txs += FetchLtc(address, session, timeout)
    txs += FetchXrp(address, session, timeout)

    if not txs:
        print(f"{ERROR} No transactions found for this address!", reset)
        Continue()
        Reset()

    w_chain = max((len(t.get("chain", "") or "") for t in txs), default=5) + 2
    w_tx    = max((len(t.get("transaction_id", "") or "") for t in txs), default=16) + 2
    w_val   = 14

    print(f"\n{green}{'':14} {'Chain':<{w_chain}} {'Transaction ID':<{w_tx}} {'Value':<{w_val}} {'Date'}{reset}")

    for tx in txs:
        chain  = str(tx.get("chain") or "Unknown")
        txid   = str(tx.get("transaction_id") or "Unknown")
        val    = tx.get("value")
        valstr = f"{float(val):.6f}" if val is not None else "Unknown"
        date   = str(tx.get("date")) if tx.get("date") else "Unknown"
        print(f" {SUCCESS} {chain:<{w_chain}} {txid:<{w_tx}} {valstr:<{w_val}} {date}", reset)

    print(f"\n{INFO} Total transactions:{green} {len(txs)}", reset)

    Continue()
    Reset()

except Exception as e:
    Error(e)
