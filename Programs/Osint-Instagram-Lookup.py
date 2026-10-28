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
    import instaloader
    import logging
except Exception as e:
    MissingModule(e)

Title("Instagram Profile Lookup")

Scroll(GradientBanner(osint_banner))

try:
    username  = input(f"{INPUT} Username {green}->{reset} ").strip()
    sessionid = input(f"{INPUT} Session ID (Instagram cookie) {green}->{reset} ").strip()

    if not username:
        ErrorInput()

    if not sessionid:
        print(f"{ERROR} Session ID requigreen (log in to Instagram, copy sessionid cookie)!", reset)
        Continue()
        Reset()

    print(f"{LOADING} Fetching profile..", reset)

    logging.getLogger("instaloader").setLevel(logging.CRITICAL)
    loader                     = instaloader.Instaloader(download_pictures=False, download_videos=False, save_metadata=False, quiet=True)
    loader.context.log         = lambda *a, **kw: None
    loader.context.error       = lambda *a, **kw: None
    loader.context._session.cookies.set("sessionid", sessionid, domain=".instagram.com")
    loader.context._session.headers.update({"User-Agent": RandomUserAgents()})

    try:
        profile = instaloader.Profile.from_username(loader.context, username)
    except Exception as e:
        print(f"{ERROR} Could not fetch profile:{green} {e}", reset)
        Continue()
        Reset()

    bio_tags     = " / ".join(profile.biography_hashtags) if profile.biography_hashtags else None
    bio_mentions = " / ".join(profile.biography_mentions) if profile.biography_mentions else None

    results = {
        "Username"              : profile.username,
        "Full name"             : profile.full_name,
        "User ID"               : profile.userid,
        "Biography"             : profile.biography,
        "Bio hashtags"          : bio_tags,
        "Bio mentions"          : bio_mentions,
        "External URL"          : profile.external_url,
        "Followers"             : profile.followers,
        "Followees"             : profile.followees,
        "Posts"                 : profile.mediacount,
        "Reels"                 : profile.igtvcount,
        "Private"               : profile.is_private,
        "Verified"              : profile.is_verified,
        "Business account"      : profile.is_business_account,
        "Business category"     : profile.business_category_name,
        "Has public story"      : profile.has_public_story,
        "Has viewable story"    : profile.has_viewable_story,
        "Has highlight reels"   : profile.has_highlight_reels,
        "Blocked by viewer"     : profile.blocked_by_viewer,
        "Has blocked viewer"    : profile.has_blocked_viewer,
        "Followed by viewer"    : profile.followed_by_viewer,
        "Follows viewer"        : profile.follows_viewer,
        "Profile URL"           : f"https://www.instagram.com/{profile.username}",
        "Profile picture URL"   : profile.profile_pic_url,
    }

    output_lines = []
    for key, val in results.items():
        if val is not None and val != "" and val != False:
            output_lines.append(f" {SUCCESS} {key:<24}:{green} {val}{white}")

    Scroll("\n" + "\n".join(output_lines) + "\n")

    Continue()
    Reset()

except Exception as e:
    Error(e)
