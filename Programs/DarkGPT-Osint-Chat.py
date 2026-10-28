# Copyright (c) 2025-2026 v4lkyr0 — SINIX
# See the file 'LICENSE' for copying permission.

from Core.Utils import *
from Core.Config import *

try:
    import os
    import json
    import requests
    requests.packages.urllib3.disable_warnings()
except Exception as e:
    MissingModule(e)

Title("DarkGPT — OSINT AI Chat")

darkgpt_banner = f"""{green}
    ██████╗  █████╗ ██████╗ ██╗  ██╗ ██████╗ ██████╗ ████████╗
    ██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝██╔════╝ ██╔══██╗╚══██╔══╝
    ██║  ██║███████║██████╔╝█████╔╝ ██║  ███╗██████╔╝   ██║
    ██║  ██║██╔══██║██╔══██╗██╔═██╗ ██║   ██║██╔═══╝    ██║
    ██████╔╝██║  ██║██║  ██║██║  ██╗╚██████╔╝██║        ██║
    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝        ╚═╝
              {white}OSINT AI — Powered by luijait/DarkGPT{green}
{reset}"""

Scroll(Gradient(darkgpt_banner))

DARKGPT_DIR  = os.path.join(tool_path, "Programs", "DarkGPT")
HISTORY_PATH = os.path.join(DARKGPT_DIR, "history.json")
CONFIG_PATH  = os.path.join(DARKGPT_DIR, "config.json")
os.makedirs(DARKGPT_DIR, exist_ok=True)

SYSTEM_PROMPT = (
    "You are DarkGPT, an advanced OSINT (Open Source Intelligence) assistant. "
    "Help security researchers gather, correlate, and interpret publicly available "
    "information. You excel at analyzing usernames, emails, IPs, domains, and digital "
    "footprints; explaining OSINT tools (Sherlock, theHarvester, SpiderFoot, Recon-ng, "
    "Maltego); interpreting WHOIS, DNS, Shodan, Censys results; identifying patterns "
    "in open-source data; advising on OPSEC and defensive measures. "
    "Respond clearly, technically, and concisely."
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"api_key": ""}

def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
    except Exception:
        pass

# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------
def load_history():
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Filtre les anciens historiques qui avaient le system prompt en role "user"
            return [m for m in data if m.get("role") in ("user", "assistant")
                    and m.get("content") != SYSTEM_PROMPT]
        except Exception:
            pass
    return []

def save_history(history):
    try:
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

def reset_history():
    save_history([])
    return []

# ---------------------------------------------------------------------------
# Send via Anthropic API (claude-haiku — fast, cheap)
# ---------------------------------------------------------------------------
def send_anthropic(history, api_key):
    # Convert history to Anthropic format
    messages = []
    system   = SYSTEM_PROMPT
    for msg in history:
        role    = msg["role"]
        content = msg["content"]
        if role == "system":
            system = content
            continue
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": content})

    if not messages:
        return None

    headers = {
        "Content-Type":      "application/json",
        "x-api-key":         api_key,
        "anthropic-version": "2023-06-01",
    }
    payload = {
        "model":      "claude-haiku-4-5-20251001",
        "max_tokens": 1024,
        "system":     system,
        "messages":   messages,
    }
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers = headers,
        json    = payload,
        timeout = 30,
        verify  = True,
    )
    if r.status_code == 200:
        return r.json()["content"][0]["text"]
    else:
        return f"[HTTP {r.status_code}] {r.text[:200]}"

# ---------------------------------------------------------------------------
# Send via Groq (free tier — no card needed for 30 req/min)
# ---------------------------------------------------------------------------
def send_groq(history, api_key):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += [m for m in history if m["role"] in ("user", "assistant")]
    headers  = {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model":    "llama-3.1-8b-instant",
        "messages": messages,
    }
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers = headers,
        json    = payload,
        timeout = 30,
    )
    if r.status_code == 200:
        return r.json()["choices"][0]["message"]["content"]
    return f"[HTTP {r.status_code}] {r.text[:200]}"

# ---------------------------------------------------------------------------
# Send dispatcher
# ---------------------------------------------------------------------------
def send(history, cfg):
    provider = cfg.get("provider", "")
    api_key  = cfg.get("api_key", "")

    if not api_key:
        return "[Error] No API key configured. Type /config to set one."

    if provider == "groq":
        return send_groq(history, api_key)
    else:
        return send_anthropic(history, api_key)

# ---------------------------------------------------------------------------
# Config setup
# ---------------------------------------------------------------------------
def configure(cfg):
    print(f"\n  {INFO} {white}Choose provider:{reset}\n", reset)
    print(f"  {PREFIX}1{SUFFIX} {green}Anthropic{reset}  (claude-haiku — needs Anthropic API key)")
    print(f"  {PREFIX}2{SUFFIX} {green}Groq{reset}       (llama-3.1-8b — FREE tier, no card needed)")
    print()
    print(f"  {INFO} Groq free tier: {green}console.groq.com{reset} → sign up → API Keys → Create")
    print(f"  {INFO} Anthropic:      {green}console.anthropic.com{reset} → API Keys\n")

    choice = input(f"  {INPUT} Provider {green}->{reset} ").strip()
    if choice == "1":
        cfg["provider"] = "anthropic"
    elif choice == "2":
        cfg["provider"] = "groq"
    else:
        print(f"\n  {ERROR} Invalid choice. Type 1 or 2.\n")
        return cfg

    key = input(f"  {INPUT} API Key {green}->{reset} ").strip()
    if not key:
        print(f"\n  {ERROR} No key entered. Provider saved, key unchanged.\n")
        save_config(cfg)
        return cfg

    cfg["api_key"] = key
    save_config(cfg)
    pname = "Anthropic" if cfg["provider"] == "anthropic" else "Groq"
    print(f"\n  {SUCCESS} {pname} configured.\n")
    return cfg

# ---------------------------------------------------------------------------
# Format reply
# ---------------------------------------------------------------------------
def format_reply(text):
    lines   = text.split("\n")
    output  = []
    in_code = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            output.append(f"  {green}{'─' * 54}{reset}")
            continue
        output.append(f"  {white if in_code else ''}{line}{reset if in_code else ''}")
    return "\n".join(output)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run():
    cfg     = load_config()
    history = load_history()

    api_key  = cfg.get("api_key", "")
    provider = cfg.get("provider", "anthropic")
    pname    = "Groq / llama-3.1-8b" if provider == "groq" else "Anthropic / claude-haiku"

    print(f"  {yellow}30 requêtes/minute gratuites sur Llama-3.1-8b — assez pour discuter en continu.{reset}", reset)
    print(f"  {yellow}Groq est GRATUIT — inscris-toi sur console.groq.com puis tape /config{reset}", reset)
    print()

    if not api_key:
        print(f"  {ERROR} Aucune clé API configurée.", reset)
        print(f"  {INFO} Tape {green}/config{reset} pour en ajouter une.\n", reset)
    else:
        print(f"  {INFO} Provider : {green}{pname}{reset}", reset)

    print(f"  {INFO} /help for commands. /exit to quit.\n", reset)

    while True:
        try:
            user_input = input(f"\n  {PREFIX}You{SUFFIX} {green}->{reset} ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd in ["/exit", "/quit", "exit", "quit"]:
            break
        elif cmd == "/help":
            print(f"\n  {INFO} {white}Commands:{reset}", reset)
            cmds = {
                "/config":  "Set provider + API key",
                "/clear":   "Reset conversation",
                "/history": "Print conversation",
                "/exit":    "Exit",
            }
            for c, d in cmds.items():
                print(f"    {green}{c:<12}{reset} {d}", reset)
            print()
            continue
        elif cmd == "/config":
            cfg = configure(cfg)
            api_key  = cfg.get("api_key", "")
            provider = cfg.get("provider", "anthropic")
            pname    = "Groq / llama-3.1-8b" if provider == "groq" else "Anthropic / claude-haiku"
            continue
        elif cmd == "/clear":
            history = reset_history()
            print(f"\n  {SUCCESS} Conversation cleared.\n", reset)
            continue
        elif cmd == "/history":
            for msg in history:
                if msg["role"] == "system":
                    continue
                col  = green if msg["role"] == "user" else white
                role = "You" if msg["role"] == "user" else "DarkGPT"
                print(f"\n  {col}{role}:{reset} {msg['content']}", reset)
            print()
            continue

        history.append({"role": "user", "content": user_input})
        save_history(history)

        print(f"\n  {LOADING} Thinking..", end="\r")
        reply = send(history, cfg)
        print(" " * 40, end="\r")

        if not reply or reply.startswith("[Error]"):
            print(f"\n  {ERROR} {reply or 'No response.'}", reset)
            if not api_key:
                print(f"  {INFO} Type {green}/config{reset} to set a key.\n", reset)
            history.pop()
        else:
            history.append({"role": "assistant", "content": reply})
            save_history(history)
            pname = "Groq / llama-3.1-8b" if cfg.get("provider") == "groq" else "Anthropic / claude-haiku"
            print(f"\n  {PREFIX}DarkGPT{SUFFIX} {white}via {pname}{reset}\n", reset)
            print(format_reply(reply), reset)
            print()

try:
    run()
    Continue()
    Reset()
except KeyboardInterrupt:
    Reset()
except Exception as e:
    Error(e)
