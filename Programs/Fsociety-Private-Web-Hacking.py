# Copyright (c) 2025-2026 v4lkyr0 — SINIX
# fsociety integration — Private Web Hacking

import os
import sys
import subprocess

_prog_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_prog_dir)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

try:
    from Programs.Core.Utils import *
    from Programs.Core.Config import *
except Exception as e:
    print(f"[!] Import error: {e}")
    sys.exit(1)

FSOCIETY_CHOICE = "7"

def run():
    Title("fsociety — Private Web Hacking")
    Clear()

    fsociety_dir  = os.path.join(tool_path, "Programs", "fsociety-master")
    fsociety_path = os.path.join(fsociety_dir, "fsociety.py")

    if not os.path.isfile(fsociety_path):
        print(f"\n  [!] fsociety not found at: {fsociety_path}")
        input("\n  Press Enter to return...")
        return

    print(f"\n  Launching fsociety — Private Web Hacking...\n")

    original_dir = os.getcwd()
    try:
        os.chdir(fsociety_dir)
        # stdin=None -> herite du vrai terminal, l utilisateur garde la main
        # --sinix-choice saute le premier menu automatiquement
        proc = subprocess.Popen(
            ["python3", "fsociety.py", "--sinix-choice", FSOCIETY_CHOICE],
            stdin=None,
            stdout=None,
            stderr=None,
        )
        proc.wait()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n  [!] Error: {e}")
        input("\n  Press Enter to return...")
    finally:
        os.chdir(original_dir)

run()
