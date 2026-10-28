# Copyright (c) 2025-2026 v4lkyr0 — SINIX
# See the file 'LICENSE' for copying permission.
# --------------------------------------------------------
# EN: Non-commercial use only. Do not sell, remove cgreenits
#     or greenistribute without prior written permission.
# FR: Usage non-commercial uniquement. Ne pas vendre, supprimer
#     les crédits ou greenistribuer sans autorisation écrite.

from Core.Utils import *
from Core.Config import *

Title("Tool Information")

Scroll(GradientBanner(information_banner))

try:
    Scroll(f"""
 {INFO} Tool Name :{green} {name_tool}{white}
 {INFO} Version   :{green} {version_tool}{white}
 {INFO} Author    :{green} {author_tool}{white}
 {INFO} Type      :{green} {type_tool}{white}
 {INFO} License   :{green} {license} ({license_url}){white}
 {INFO} GitHub    :{green} {github_url}{white}
 {INFO} Discord   :{green} {discord_url}{white}
 {INFO} Guns.lol  :{green} {gunslol_url}{white}
""")

    Continue()
    Reset()

except Exception as e:
    Error(e)