#!/usr/bin/env python3
"""Download every content image once, downscale it, and store WebP copies."""
import glob
import hashlib
import io
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import requests
from PIL import Image

BUILD = "/home/walktheearth/VAGCoder/build"
DIST = "/home/walktheearth/VAGCoder/docs"
IMG_DIR = os.path.join(DIST, "img")
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def collect():
    urls = set()
    for f in glob.glob(os.path.join(BUILD, "pages", "*.json")):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for u in d.get("i", []):
            if not u.startswith("http"):
                continue
            if "wp-content/plugins" in u or "wp-content/themes" in u:
                continue
            if re.search(r"\.svg(\?|$)", u, re.I):
                continue
            urls.add(u)
    return sorted(urls)


def fname(url):
    base = os.path.basename(urlparse(url).path)
    ext = ".gif" if re.search(r"\.gif$", base, re.I) else ".webp"
    base = re.sub(r"\.[a-zA-Z0-9]+$", "", base)
    base = re.sub(r"[^a-zA-Z0-9_-]+", "-", base).strip("-")[:50] or "img"
    return base + "-" + hashlib.md5(url.encode()).hexdigest()[:8] + ext


def one(url):
    path = os.path.join(IMG_DIR, fname(url))
    rel = "img/" + os.path.basename(path)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return url, rel, os.path.getsize(path), "cached"
    for attempt in range(2):
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=40)
            if r.status_code != 200:
                raise ValueError("HTTP %s" % r.status_code)
            if path.endswith(".gif"):
                with open(path, "wb") as fh:
                    fh.write(r.content)
                return url, rel, len(r.content), "ok"
            im = Image.open(io.BytesIO(r.content))
            im.seek(0)
            if im.mode in ("P", "LA") or (im.mode == "RGBA" and im.getextrema()[3][0] < 255):
                im = im.convert("RGBA")
            else:
                im = im.convert("RGB")
            im.thumbnail((1200, 2400), Image.LANCZOS)
            im.save(path, "WEBP", quality=74, method=6)
            return url, rel, os.path.getsize(path), "ok"
        except Exception as e:  # noqa: BLE001
            err = type(e).__name__
            time.sleep(0.8)
    return url, None, 0, err


def main():
    os.makedirs(IMG_DIR, exist_ok=True)
    urls = collect()
    print("images", len(urls), flush=True)
    mapping = {}
    total = 0
    done = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = [ex.submit(one, u) for u in urls]
        for fut in as_completed(futs):
            url, rel, size, st = fut.result()
            done += 1
            if rel:
                mapping[url] = rel
                total += size
            else:
                print("FAIL", st, url, flush=True)
            if done % 200 == 0:
                print(done, len(urls), round(total / 1048576, 1), "MB",
                      f"{done / (time.time() - t0):.1f}/s", flush=True)
    with open(os.path.join(BUILD, "imgmap.json"), "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=0)
    print("mapped", len(mapping), "total", round(total / 1048576, 1), "MB")


if __name__ == "__main__":
    main()
