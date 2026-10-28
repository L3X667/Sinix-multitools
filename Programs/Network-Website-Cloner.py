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
    import concurrent.futures
    import base64
    import re
    import urllib.parse
    import bs4
    import lxml.html
    import lxml.etree
    import warnings
except Exception as e:
    MissingModule(e)


def GetMimeType(url):
    p = urllib.parse.urlparse(url).path.lower()
    if p.endswith(".png"):              return "image/png"
    if p.endswith((".jpg", ".jpeg")):   return "image/jpeg"
    if p.endswith(".gif"):              return "image/gif"
    if p.endswith(".svg"):              return "image/svg+xml"
    if p.endswith(".webp"):             return "image/webp"
    if p.endswith(".woff"):             return "font/woff"
    if p.endswith(".woff2"):            return "font/woff2"
    if p.endswith(".ttf"):              return "font/ttf"
    if p.endswith(".otf"):              return "font/otf"
    if p.endswith(".css"):              return "text/css"
    if p.endswith(".js"):               return "application/javascript"
    return "application/octet-stream"


def SanitizeXml(text):
    if not text:
        return text
    return re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\uD7FF\uE000-\uFFFD]", "", text)


def FetchResource(session, url, timeout):
    for _ in range(3):
        try:
            r = session.get(url, timeout=timeout)
            if r.status_code == 200:
                return r.content
            if r.status_code == 403:
                return None
        except requests.exceptions.Timeout:
            continue
        except Exception:
            return None
    return None


def FetchAll(session, urls, timeout):
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(FetchResource, session, url, timeout): url for url in urls}
        for f in concurrent.futures.as_completed(futures):
            url     = futures[f]
            content = f.result()
            if content:
                results[url] = content
    return results


def InlineCss(base_url, css_content, resource_map):
    def Replace(m):
        raw_url  = m.group(1).strip("'\"")
        full_url = urllib.parse.urljoin(base_url, raw_url)
        if full_url in resource_map:
            mime    = GetMimeType(full_url)
            b64     = base64.b64encode(resource_map[full_url]).decode()
            return f"url(data:{mime};base64,{b64})"
        return m.group(0)
    return re.sub(r"url\((.*?)\)", Replace, css_content)


def ClonePageHtml(session, url, timeout):
    try:
        r = session.get(url, timeout=timeout)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"{ERROR} HTTP error:{green} {e}", reset)
        return None, None
    except requests.exceptions.RequestException as e:
        print(f"{ERROR} Request error:{green} {e}", reset)
        return None, None

    html       = SanitizeXml(r.content.decode("utf-8", "ignore"))
    title_m    = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    page_title = title_m.group(1).strip() if title_m else "page"
    print(f"{SUCCESS} HTML fetched:{green} {len(html)} bytes", reset)
    return html, page_title


def InlineResources(session, base_url, html, timeout):
    html    = SanitizeXml(html)
    parser  = lxml.html.HTMLParser(recover=True)
    tree    = lxml.html.fromstring(html, parser=parser)

    scripts   = tree.xpath("//script[@src]")
    css_links = tree.xpath("//link[@rel='stylesheet'][@href]")
    images    = tree.xpath("//img[@src]")
    media     = tree.xpath("//source[@src]|//video[@src]|//audio[@src]")

    all_urls = set()
    for el in scripts  : all_urls.add(urllib.parse.urljoin(base_url, el.attrib["src"]))
    for el in css_links: all_urls.add(urllib.parse.urljoin(base_url, el.attrib["href"]))
    for el in images   : all_urls.add(urllib.parse.urljoin(base_url, el.attrib["src"]))
    for el in media    : all_urls.add(urllib.parse.urljoin(base_url, el.attrib["src"]))

    fetched = FetchAll(session, list(all_urls), timeout)

    for el in scripts:
        full_url = urllib.parse.urljoin(base_url, el.attrib["src"])
        if full_url in fetched:
            el.attrib.pop("src", None)
            content = SanitizeXml(fetched[full_url].decode("utf-8", "ignore"))
            if content.strip():
                el.text = "\n" + content + "\n"
    print(f"{SUCCESS} JS inlined:{green} {len(scripts)}", reset)

    for el in css_links:
        full_url = urllib.parse.urljoin(base_url, el.attrib["href"])
        if full_url in fetched:
            css      = fetched[full_url].decode("utf-8", "ignore")
            css      = SanitizeXml(css)
            if not css.strip():
                continue
            sub_urls = [urllib.parse.urljoin(full_url, u.strip("'\"")) for u in re.findall(r"url\((.*?)\)", css)]
            extra    = FetchAll(session, sub_urls, timeout)
            css      = InlineCss(full_url, css, extra)
            style    = lxml.html.Element("style")
            style.text = "\n" + css + "\n"
            el.getparent().replace(el, style)
    print(f"{SUCCESS} CSS inlined:{green} {len(css_links)}", reset)

    for el in images:
        full_url = urllib.parse.urljoin(base_url, el.attrib["src"])
        if full_url in fetched:
            mime               = GetMimeType(full_url)
            b64                = base64.b64encode(fetched[full_url]).decode()
            el.attrib["src"]   = f"data:{mime};base64,{b64}"
    print(f"{SUCCESS} Images inlined:{green} {len(images)}", reset)

    for el in media:
        full_url = urllib.parse.urljoin(base_url, el.attrib["src"])
        if full_url in fetched:
            mime             = GetMimeType(full_url)
            b64              = base64.b64encode(fetched[full_url]).decode()
            el.attrib["src"] = f"data:{mime};base64,{b64}"
    print(f"{SUCCESS} Media inlined:{green} {len(media)}", reset)

    raw  = lxml.etree.tostring(tree, encoding="unicode", method="html")
    raw  = SanitizeXml(raw)
    warnings.filterwarnings("ignore", category=bs4.XMLParsedAsHTMLWarning)
    soup = bs4.BeautifulSoup(raw, "html.parser")
    return soup.prettify()


Title("Website Cloner")

Scroll(GradientBanner(network_banner))

try:
    target = input(f"{INPUT} Target URL {green}->{reset} ").strip()

    if not target:
        ErrorInput()

    if not target.startswith("http"):
        target = "https://" + target

    timeout_input = input(f"{INPUT} HTTP timeout in seconds (default: 60) {green}->{reset} ").strip()
    try:
        timeout = float(timeout_input) if timeout_input else 60.0
    except ValueError:
        timeout = 60.0

    print(f"{LOADING} Cloning {target}..", reset)

    session = requests.Session()
    session.headers.update({"User-Agent": RandomUserAgents()})

    html, page_title = ClonePageHtml(session, target, timeout)
    if not html:
        Continue()
        Reset()

    final_html = InlineResources(session, target, html, timeout)

    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in page_title).strip() or "page"
    output_dir = os.path.join(tool_path, "Programs", "Output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{safe_title}.html")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"{SUCCESS} Saved:{green} {output_path}", reset)

    Continue()
    Reset()

except Exception as e:
    Error(e)
