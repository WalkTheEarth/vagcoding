#!/usr/bin/env python3
"""Turn scraped page extracts into the static site data files."""
import glob
import html
import json
import os
import re
from urllib.parse import urlparse

import bs4

BUILD = "/home/walktheearth/VAGCoder/build"
DIST = "/home/walktheearth/VAGCoder/dist"
BRANDS = [("audi", "Audi"), ("vw", "VW"), ("seat-cupra", "SEAT / Cupra"), ("skoda", "Skoda")]
BRAND_NAMES = dict(BRANDS)
SKIP = {"privacy-policy-and-legal-notice", "favourites", "partners"}


def load():
    pages = {}
    for f in glob.glob(os.path.join(BUILD, "pages", "*.json")):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if d.get("u") and d.get("c") is not None:
            pages[d["u"]] = d
    return pages


def slug_of(url):
    p = urlparse(url).path.strip("/")
    return p.split("/") if p else []


def drop_first_banner(soup, banner):
    if not banner:
        return
    for fig in soup.find_all(["figure", "p", "img"], limit=6):
        img = fig if fig.name == "img" else fig.find("img")
        if img and img.get("src") == banner:
            (fig if fig.name in ("figure", "p") else fig.parent).decompose()
            return


def clean_content(d, banner=None, model_image_map=None):
    soup = bs4.BeautifulSoup(d["c"], "lxml")
    root = soup.select_one("div.entry-content") or soup.body or soup
    for c in root.find_all(string=lambda t: isinstance(t, bs4.Comment)):
        c.extract()
    drop_first_banner(root, banner)
    if model_image_map is not None:
        for img in root.find_all("img"):
            src = img.get("src", "")
            if src in model_image_map:
                img["src"] = model_image_map[src]
    for a in root.find_all("a"):
        h = a.get("href", "")
        if h.startswith("https://www.vag-coding.net/") or h.startswith("http://www.vag-coding.net/"):
            parts = slug_of(h)
            if len(parts) == 1 and parts[0] in BRAND_NAMES:
                a["href"] = "#/" + parts[0]
            elif len(parts) == 2 and parts[0] in BRAND_NAMES:
                a["href"] = "#/" + "/".join(parts)
            elif len(parts) == 3 and parts[0] in BRAND_NAMES:
                a["href"] = "#/" + "/".join(parts)
            elif len(parts) == 2 and parts[0] == "tutorials-information":
                a["href"] = "#/t/" + parts[1]
            elif len(parts) == 3 and parts[0] == "tutorials-information":
                a["href"] = "#/t/" + parts[2]
            elif len(parts) == 1 and parts[0] == "tutorials-information":
                a["href"] = "#/tutorials"
        elif h.startswith("http"):
            a["target"] = "_blank"
            a["rel"] = "noopener"
    for img in root.find_all("img"):
        img["loading"] = "lazy"
        img["decoding"] = "async"
        img.attrs.pop("width", None)
        img.attrs.pop("height", None)
    for div in root.find_all("div"):
        div.unwrap()
    for el in root.find_all("p"):
        if not el.get_text(strip=True) and not el.find("img"):
            el.decompose()
    out = "".join(str(x) for x in root.contents)
    out = re.sub(r"\s*\n\s*", "\n", out)
    if not bs4.BeautifulSoup(out, "lxml").get_text(strip=True) and not bs4.BeautifulSoup(out, "lxml").find("img"):
        return '<p class="empty">No procedure text was published on the source page.</p>'
    return out.strip()


def short_title(title, model_name):
    if model_name and title.lower().startswith(model_name.lower()):
        tail = title[len(model_name):].lstrip(" –—-:")
        if tail:
            return tail
    return title


def main():
    pages = load()
    print("loaded", len(pages))
    by_slug = {}
    for u, d in pages.items():
        by_slug[tuple(slug_of(u))] = d

    # brand -> models
    tree = []
    tutorial_list = []
    imgmap = {}
    imgmap_path = os.path.join(BUILD, "imgmap.json")
    if os.path.exists(imgmap_path):
        imgmap = json.load(open(imgmap_path))
    save_images = bool(imgmap)

    total_codings = 0
    for bslug, bname in BRANDS:
        models = []
        model_keys = sorted({k[1] for k in by_slug if len(k) in (2, 3) and k[0] == bslug})
        for mslug in model_keys:
            md = by_slug.get((bslug, mslug))
            raw = []
            for k, d in by_slug.items():
                if len(k) == 3 and k[0] == bslug and k[1] == mslug:
                    raw.append((k[2], re.sub(r"\s+", " ", d["t"]).strip(), d))
            raw.sort(key=lambda x: x[1].lower())
            if md and md.get("t", "").strip():
                mname = md["t"].strip()
            elif raw:
                mname = re.split(r"\s+[–—-]\s+", raw[0][1])[0].strip()
            else:
                continue
            banner = md["i"][0] if md and md.get("i") else (raw[0][2]["i"][0] if raw and raw[0][2].get("i") else "")
            raw_banner = banner
            if save_images and banner in imgmap:
                banner = imgmap[banner]
            codings = [(slug, short_title(title, mname), d) for slug, title, d in raw]
            if not codings and not md:
                continue
            entries = []
            content_map = {}
            for cslug, st, d in codings:
                c = clean_content(d, banner=raw_banner or None,
                                  model_image_map=imgmap or None)
                entries.append([cslug, st])
                content_map[cslug] = c
            desc = re.sub(r"\s+", " ", (md.get("d") or "")).strip() if md else ""
            models.append({
                "s": mslug, "n": mname, "d": desc[:400], "i": banner,
                "p": entries, "_content": content_map,
            })
            total_codings += len(entries)
        models.sort(key=lambda m: m["n"].lower())
        tree.append({"s": bslug, "n": bname, "m": models})

    # tutorials
    tut_content = {}
    for k, d in by_slug.items():
        if len(k) in (2, 3) and k[0] == "tutorials-information":
            b = k[-1]
            title = re.sub(r"\s+", " ", d["t"]).strip()
            tutorial_list.append((b, title, "/".join(k)))
            tut_content[b] = clean_content(d, model_image_map=imgmap or None)
    tutorial_list.sort(key=lambda x: x[1].lower())

    if not imgmap:
        # keep remote images so this build is still viewable
        pass

    if os.path.isdir(os.path.join(DIST, "data")):
        import shutil
        shutil.rmtree(os.path.join(DIST, "data"))
    os.makedirs(os.path.join(DIST, "data"), exist_ok=True)
    os.makedirs(os.path.join(DIST, "img"), exist_ok=True)

    index = {
        "b": [{"s": b["s"], "n": b["n"], "m": [
            {"s": m["s"], "n": m["n"], "d": m["d"], "i": m["i"], "p": m["p"]} for m in b["m"]
        ]} for b in tree],
        "t": tutorial_list,
        "n": total_codings,
    }
    with open(os.path.join(DIST, "data", "index.js"), "w", encoding="utf-8") as f:
        f.write("window.VI=" + json.dumps(index, ensure_ascii=False, separators=(",", ":")) + ";\n")

    for b in tree:
        os.makedirs(os.path.join(DIST, "data", b["s"]), exist_ok=True)
        for m in b["m"]:
            content = m.pop("_content")
            if not content:
                continue
            with open(os.path.join(DIST, "data", b["s"], m["s"] + ".js"), "w", encoding="utf-8") as f:
                f.write('window.VD=window.VD||{};window.VD["' + b["s"] + "/" + m["s"] + '"]=' +
                        json.dumps(content, ensure_ascii=False, separators=(",", ":")) + ";\n")
    with open(os.path.join(DIST, "data", "tutorials.js"), "w", encoding="utf-8") as f:
        f.write("window.VD=window.VD||{};window.VD.tutorials=" +
                json.dumps(tut_content, ensure_ascii=False, separators=(",", ":")) + ";\n")

    # drop downloaded images that the generated data never references
    if imgmap:
        used = set()
        for root, _, fs in os.walk(os.path.join(DIST, "data")):
            for fn in fs:
                used.update(re.findall(r'img/[A-Za-z0-9_.-]+\.(?:webp|gif)',
                                       open(os.path.join(root, fn), encoding="utf-8").read()))
        removed = 0
        for fn in os.listdir(os.path.join(DIST, "img")):
            if "img/" + fn not in used:
                os.remove(os.path.join(DIST, "img", fn))
                removed += 1
        print("  unused images removed", removed)

    print("models", sum(len(b["m"]) for b in tree), "codings", total_codings, "tutorials", len(tutorial_list))
    for b in tree:
        print(" ", b["n"], len(b["m"]), "models", sum(len(m["p"]) for m in b["m"]), "codings")
    dsize = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(os.path.join(DIST, "data")) for f in fs)
    print("  data dir", round(dsize / 1048576, 1), "MB")


if __name__ == "__main__":
    main()
