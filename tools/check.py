#!/usr/bin/env python3
"""Sanity checks on the generated site data."""
import json
import os
import re
import sys

DIST = "/home/walktheearth/VAGCoder/docs"


def load_js(path, var):
    s = open(path, encoding="utf-8").read()
    i = s.find(var)
    return json.loads(s[i + len(var):].rstrip().rstrip(";"))


def main():
    idx = load_js(os.path.join(DIST, "data", "index.js"), "window.VI=")
    problems = []
    total = 0
    remote = 0
    empty = 0
    for b in idx["b"]:
        for m in b["m"]:
            path = os.path.join(DIST, "data", b["s"], m["s"] + ".js")
            if not m["p"]:
                continue
            if not os.path.exists(path):
                problems.append("missing model file: " + b["s"] + "/" + m["s"])
                continue
            prefix = 'window.VD=window.VD||{};window.VD["%s/%s"]=' % (b["s"], m["s"])
            brand = load_js(path, prefix)
            for slug, title in m["p"]:
                total += 1
                key = slug
                if key not in brand:
                    problems.append("missing content: " + b["s"] + "/" + m["s"] + "/" + key)
                    continue
                html = brand[key]
                if "empty" in html and len(html) < 200:
                    empty += 1
                remote += len(re.findall(r'src="https?://', html))
                if "<script" in html.lower():
                    problems.append("script in content: " + key)
    tut = load_js(os.path.join(DIST, "data", "tutorials.js"),
                  "window.VD=window.VD||{};window.VD.tutorials=")
    tut_remote = sum(len(re.findall(r'src="https?://', v)) for v in tut.values())
    print("index pages:", idx["n"], "| brand pages checked:", total,
          "| tutorials:", len(tut))
    print("empty-procedure placeholders:", empty)
    print("remote image refs in codings:", remote, "| in tutorials:", tut_remote)
    banner_remote = sum(1 for b in idx["b"] for m in b["m"] if m["i"].startswith("http"))
    print("remote model banners:", banner_remote)
    print("problems:", len(problems))
    for p in problems[:10]:
        print(" ", p)
    imgdir = os.path.join(DIST, "img")
    n_img = len(os.listdir(imgdir))
    size = sum(os.path.getsize(os.path.join(imgdir, f)) for f in os.listdir(imgdir))
    print("local images:", n_img, round(size / 1048576, 1), "MB")
    total_size = 0
    for root, _, files in os.walk(DIST):
        for f in files:
            total_size += os.path.getsize(os.path.join(root, f))
    print("site total:", round(total_size / 1048576, 1), "MB")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
