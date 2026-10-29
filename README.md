# VAG Coding — dark offline reference

A clean, dark, flat front end for the VCDS / OBDeleven coding procedures published at
[vag-coding.net](https://www.vag-coding.net/). Single static site, no build step, no
dependencies, no tracking.

Live: **https://walktheearth.github.io/vagcoding/**

Data was captured on 2026-10-29 and is published with permission from
vag-coding.net. All procedures and images belong to the original authors; keep the
source attribution links intact.

## Use it

- **Online:** upload the contents of `docs/` to any static host (or run
  `python3 -m http.server` inside `docs/`). GitHub Pages serves `docs/` directly.
- **Offline:** download `docs/VAG-Coding-offline.zip`, extract it, and double-click
  `index.html`. Everything — data, images, search — works from `file://`.

## Layout

```
docs/index.html          app shell
docs/assets/app.css      styles
docs/assets/app.js       router, search, UI
docs/data/index.js       brand/model tree + every page title (search index)
docs/data/<brand>/<model>.js   full procedure text, one file per model
docs/data/tutorials.js   guide text
docs/img/                optimized screenshots (WebP)
docs/VAG-Coding-offline.zip    downloadable offline copy
```

## Rebuilding the data

Tools live in `tools/` (Python 3 with `requests`, `beautifulsoup4`, `lxml`, `Pillow`):

```bash
python3 tools/scrape.py     # fetch sitemap pages into build/pages/
python3 tools/images.py     # download + optimize images, writes build/imgmap.json
python3 tools/build.py      # write docs/data/*.js
sh tools/package.sh         # rebuild docs/VAG-Coding-offline.zip
```

`robots.txt` on the source site allows crawling. Be polite if you re-run it.

## Licence

Code in this folder: do what you like with it. Scraped text and screenshots remain
the property of vag-coding.net, used here with permission.
