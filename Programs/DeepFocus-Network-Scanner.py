# Copyright (c) 2025-2026 v4lkyr0 — SINIX
# Deep Focus integration — Network Scanner (Page 9)

import os
import sys
import subprocess

# Inject sinix_tools root into sys.path so Core imports resolve correctly
# regardless of the cwd set by StartProgram (which sets cwd=Programs/)
_prog_dir = os.path.dirname(os.path.abspath(__file__))   # .../Programs
_root_dir = os.path.dirname(_prog_dir)                   # .../sinix_tools
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

try:
    from Programs.Core.Utils import *
    from Programs.Core.Config import *
except Exception as e:
    print(f"[!] Import error: {e}")
    sys.exit(1)


def run():
    Title("Deep Focus - Network Scanner")
    Clear()

    deep_focus_dir = os.path.join(tool_path, "Programs", "DeepFocus")
    entry_point    = os.path.join(deep_focus_dir, "deep_focus.py")

    if not os.path.exists(entry_point):
        print(f"\n  [!] Deep Focus not found at: {entry_point}")
        input("\n  Press Enter to return...")
        return

    print(f"\n  Launching Deep Focus...\n")

    original_dir = os.getcwd()
    try:
        os.chdir(deep_focus_dir)
        subprocess.run([sys.executable, "deep_focus.py"], check=False)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n  [!] Error: {e}")
        input("\n  Press Enter to return...")
    finally:
        os.chdir(original_dir)

run()
