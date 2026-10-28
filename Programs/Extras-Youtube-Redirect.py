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

Title("Youtube Redirect")

try:
    url = "https://www.youtube.com/watch?v=iik25wqIuFo"

    print(f"{INFO} Opening YouTube...")
    webbrowser.open(url)
    print(f"{SUCCESS} Opened {green}{url}{reset}")

    Continue()
    Reset()

except Exception as e:
    Error(e)
