#!/usr/bin/env python3
"""Fetch vag-coding.net pages and store a compact extract (no raw HTML kept)."""
import hashlib
import json
import os
import re
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

OUT = "/home/walktheearth/VAGCoder/build/pages"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
DROP = [".simplefavorite-button", ".ssba", ".ssbp-wrap", ".sharedaddy",
        ".wpml-ls-statics-post_translations", ".wp-block-buttons",
        ".ccchildpages", "script", "style", ".screen-reader-text"]
ALLOWED = {"p", "br", "strong", "b", "em", "i", "u", "ul", "ol", "li",
           "h2", "h3", "h4", "blockquote", "table", "thead", "tbody", "tr",
           "td", "th", "figure", "figcaption", "img", "a", "hr", "code", "pre"}

local = threading.local()


def sess():
    if not hasattr(local, "s"):
        local.s = requests.Session()
        local.s.headers.update({"User-Agent": UA, "Accept-Language": "en"})
    return local.s


def clean_html(node):
    for sel in DROP:
        for tag in node.select(sel):
            tag.decompose()
    for tag in list(node.find_all(True)):
        name = tag.name.lower()
        if name not in ALLOWED:
            tag.unwrap()
            continue
        attrs = {}
        if name == "img":
            src = tag.get("src") or tag.get("data-src") or ""
            if not src:
                tag.decompose()
                continue
            attrs["src"] = src
            if tag.get("alt"):
                attrs["alt"] = tag["alt"].strip()[:300]
            tag.attrs = attrs
        elif name == "a":
            href = tag.get("href") or ""
            if href.startswith(("http://", "https://")):
                attrs["href"] = href
            tag.attrs = attrs
        else:
            tag.attrs = {}
    return str(node)


def extract(url, html):
    soup = BeautifulSoup(html, "lxml")
    title_el = soup.select_one("h1.entry-title")
    title = title_el.get_text(" ", strip=True) if title_el else ""
    if not title:
        t = soup.find("title")
        title = re.sub(r"\s*-\s*VAG Coding\s*$", "", t.get_text(strip=True)) if t else url
    art = (soup.select_one("article") or soup)
    body = art.select_one("div.entry-content") or art.select_one("div.entry")
    content = clean_html(body) if body else ""
    # top-level text description (used for model pages)
    desc = ""
    if body:
        ps = [p.get_text(" ", strip=True) for p in body.find_all("p", recursive=True)]
        ps = [p for p in ps if len(p) > 40 and "Partager" not in p]
        desc = ps[0] if ps else ""
    imgs = [i["src"] for i in BeautifulSoup(content, "lxml").find_all("img")]
    return {"u": url, "t": title, "c": content, "d": desc[:1000], "i": imgs}


def fetch(url):
    os.makedirs(OUT, exist_ok=True)
    key = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join(OUT, key + ".json")
    if os.path.exists(path):
        return key, "cached"
    last = None
    for attempt in range(3):
        try:
            r = sess().get(url, timeout=45)
            if r.status_code == 200:
                data = extract(url, r.text)
                data["s"] = r.status_code
                with open(path + ".tmp", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
                os.replace(path + ".tmp", path)
                return key, "ok"
            last = f"HTTP {r.status_code}"
            if r.status_code in (404, 410):
                break
        except Exception as e:  # noqa: BLE001
            last = type(e).__name__
        time.sleep(1.5 * (attempt + 1))
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"u": url, "e": last}, f)
    return key, "err:" + str(last)


def main():
    os.makedirs(OUT, exist_ok=True)
    urls = json.load(open("/home/walktheearth/VAGCoder/build/urls.json"))
    done = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(fetch, u): u for u in urls}
        for fut in as_completed(futs):
            done += 1
            key, status = fut.result()
            if done % 100 == 0 or status.startswith("err"):
                rate = done / max(time.time() - t0, 1)
                print(f"{done}/{len(urls)} {rate:.1f}/s last={status} {futs[fut]}", flush=True)
    print("DONE", done, f"{time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
