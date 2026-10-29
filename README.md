# VAG Coding — dark offline reference

A clean, dark, flat front end for the VCDS / OBDeleven coding procedures published at
[vag-coding.net](https://www.vag-coding.net/). Single static site, no build step, no
dependencies, no tracking.

Data was captured on 2026-10-29. All procedures and images belong to their original
authors; this is an unofficial reference copy. **The source site explicitly states
that reproduction of its content is prohibited.** Keep the offline copy private, or
get permission from vag-coding.net before hosting it publicly or monetising it with
ads.

## Use it

- **Online:** upload the contents of `dist/` to any static host (or run
  `python3 -m http.server` inside `dist/`).
- **Offline:** unzip `VAG-Coding-offline.zip` and double-click `index.html`.
  Everything — data, images, search — works from `file://`, no server needed.

## AdSense

One right-hand 160×600 wide skyscraper slot. Open `assets/config.js` and fill in:

```js
window.VAG_CONFIG = {
  adsenseClient: "ca-pub-XXXXXXXXXXXXXXXX",
  adsenseSlot: "1234567890"
};
```

Leave both empty to show a dashed placeholder (or no rail at all when opened from
`file://`). The AdSense loader is only injected when both values are set, so the
offline copy never calls Google.

To use the 300×600 half-page format instead, change the rail/ad widths in
`assets/app.css` (`.rail`, `.ad-slot`) and the `ins` size in `assets/app.js`.

## Layout

```
index.html          app shell
assets/app.css      styles
assets/app.js       router, search, UI
assets/config.js    AdSense IDs
data/index.js       brand/model tree + every page title (search index)
data/<brand>/<model>.js   full procedure text, one file per model
data/tutorials.js   guide text
img/                optimized screenshots (WebP)
```

## Rebuilding the data

Tools live in `tools/` (Python 3 with `requests`, `beautifulsoup4`, `lxml`, `Pillow`):

```bash
python3 tools/scrape.py     # fetch sitemap pages into build/pages/
python3 tools/images.py     # download + optimize images, writes build/imgmap.json
python3 tools/build.py      # write dist/data/*.js
```

`robots.txt` on the source site allows crawling. Be polite if you re-run it.

## Licence

Code in this folder: do what you like with it. Scraped text and screenshots remain
the property of vag-coding.net; keep the source attribution links intact.
