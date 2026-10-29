(() => {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const main = $("#main");
  if (!window.VI) {
    main.innerHTML = '<div class="page-h"><h1>Data not found</h1><p class="sub">The <code>data/</code> folder is missing. Extract the whole archive, not just index.html.</p></div>';
    return;
  }
  const nav = $("#nav");
  const results = $("#results");
  const input = $("#q");
  const brandBySlug = Object.fromEntries((window.VI.b || []).map(b => [b.s, b]));
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const href = (...parts) => "#/" + parts.map(encodeURIComponent).join("/");
  const modelData = {};
  let searchIndex = null;
  let routeId = 0;
  let activeHash = location.hash || "#/";
  let pendingRestore = 0;
  const scrollPositions = new Map();
  if ("scrollRestoration" in history) history.scrollRestoration = "manual";

  /* ---------- data ---------- */
  function loadModel(brand, model) {
    const key = brand + "/" + model;
    if (modelData[key]) return Promise.resolve(modelData[key]);
    return new Promise((resolve, reject) => {
      const sc = document.createElement("script");
      sc.src = "data/" + brand + "/" + model + ".js";
      sc.onload = () => {
        const d = window.VD && window.VD[key];
        if (!d) return reject(new Error("empty"));
        modelData[key] = d;
        resolve(d);
      };
      sc.onerror = () => reject(new Error("load"));
      document.head.appendChild(sc);
    });
  }
  function loadTutorials() {
    if (window.VD && window.VD.tutorials) return Promise.resolve(window.VD.tutorials);
    return new Promise((resolve, reject) => {
      const sc = document.createElement("script");
      sc.src = "data/tutorials.js";
      sc.onload = () => resolve((window.VD && window.VD.tutorials) || {});
      sc.onerror = () => reject(new Error("load"));
      document.head.appendChild(sc);
    });
  }

  /* ---------- nav ---------- */
  function renderNav() {
    let h = `<a class="nav-home" href="#/">Home</a>`;
    for (const b of window.VI.b) {
      const total = b.m.reduce((n, m) => n + m.p.length, 0);
      h += `<details class="brand-group" data-brand="${esc(b.s)}"><summary>${esc(b.n)} <span style="color:var(--mut-2);font-weight:400">${total}</span></summary><div class="brand-models">`;
      for (const m of b.m) h += `<a href="${href(b.s, m.s)}" data-brand="${esc(b.s)}" data-model="${esc(m.s)}">${esc(m.n)}</a>`;
      h += `</div></details>`;
    }
    h += `<a class="nav-tut" href="#/tutorials">Tutorials &amp; info</a>`;
    nav.innerHTML = h;
    nav.addEventListener("click", e => {
      if (e.target.closest("a")) closeNav();
    });
  }
  function markNav(brandSlug, modelSlug) {
    nav.querySelectorAll("a.on").forEach(a => a.classList.remove("on"));
    nav.querySelectorAll(".brand-group").forEach(d => {
      const on = d.dataset.brand === brandSlug;
      if (modelSlug && on) d.open = true;
    });
    if (modelSlug) {
      const a = nav.querySelector(`a[data-brand="${CSS.escape(brandSlug)}"][data-model="${CSS.escape(modelSlug)}"]`);
      if (a) { a.classList.add("on"); a.closest("details").open = true; }
    }
  }
  function closeNav() {
    document.body.classList.remove("nav-open");
    $("#menuBtn").setAttribute("aria-expanded", "false");
  }
  function toggleNav() {
    const open = document.body.classList.toggle("nav-open");
    $("#menuBtn").setAttribute("aria-expanded", String(open));
  }
  $("#menuBtn").addEventListener("click", toggleNav);
  document.addEventListener("click", e => {
    if (document.body.classList.contains("nav-open") && !e.target.closest("#side,#menuBtn")) closeNav();
  });

  /* ---------- helpers ---------- */
  function setPage(title, html) {
    document.title = title ? title + " — VAG Coding" : "VAG Coding — VCDS & OBDeleven reference";
    main.innerHTML = html;
    main.querySelectorAll("img").forEach(img => {
      img.addEventListener("error", () => {
        const f = img.closest("figure");
        (f || img).style.display = "none";
      }, { once: true });
    });
    const y = pendingRestore;
    pendingRestore = 0;
    window.scrollTo(0, y);
    closeNav();
    hideResults();
  }
  function crumbs(items) {
    return `<nav class="crumbs" aria-label="Breadcrumb">` + items.map((it, i) =>
      (i ? `<span>/</span>` : "") + (it.href ? `<a href="${it.href}">${esc(it.t)}</a>` : `<span>${esc(it.t)}</span>`)
    ).join("") + `</nav>`;
  }
  function sourceUrl(brand, model, slug) {
    return `https://www.vag-coding.net/${brand}/${model}/${slug}/`;
  }
  function findPage(b, m, slug) {
    return m.p.find(p => p[0] === slug);
  }

  /* ---------- views ---------- */
  function viewHome() {
    const models = window.VI.b.reduce((n, b) => n + b.m.length, 0);
    const cards = window.VI.b.map(b => {
      const pages = b.m.reduce((n, m) => n + m.p.length, 0);
      return `<a class="card" href="${href(b.s)}"><span class="n">${pages} codings</span><h3>${esc(b.n)}</h3><p>${b.m.length} models</p></a>`;
    }).join("");
    setPage("", `
      <section class="hero">
        <h1>Coding, without the clutter.</h1>
        <p>A dark, fast reference for VCDS and OBDeleven coding on VAG vehicles. Search a procedure, follow the steps, get out.</p>
        <div class="stats">
          <div class="stat"><b>${window.VI.n.toLocaleString("en")}</b><span>procedures</span></div>
          <div class="stat"><b>${models}</b><span>models</span></div>
          <div class="stat"><b>4</b><span>brands</span></div>
        </div>
      </section>
      <div class="section-h"><h2>Browse by brand</h2></div>
      <div class="cards">${cards}</div>
      <div class="section-h"><h2>Guides</h2><a href="#/tutorials">All tutorials →</a></div>
      <p style="color:var(--mut);max-width:640px">VCDS vs OBDeleven, SFD protection, backups, service resets and other background reading.</p>
    `);
    markNav();
  }

  function viewBrand(b) {
    const pages = b.m.reduce((n, m) => n + m.p.length, 0);
    const list = b.m.map(m => `<a href="${href(b.s, m.s)}"><span>${esc(m.n)}</span><span class="arrow">${m.p.length} codings →</span></a>`).join("");
    setPage(b.n, `
      ${crumbs([{ t: "Home", href: "#/" }, { t: b.n }])}
      <div class="page-h"><h1>${esc(b.n)}</h1><p class="sub">${b.m.length} models · ${pages} coding procedures</p></div>
      <div class="model-list">${list}</div>
    `);
    markNav();
  }

  function viewModel(b, m) {
    const list = m.p.map(p => `<a href="${href(b.s, m.s, p[0])}"><span>${esc(p[1])}</span><span class="arrow">→</span></a>`).join("");
    const banner = m.i ? `<figure class="model-banner"><img src="${esc(m.i)}" alt="${esc(m.n)}" loading="lazy"></figure>` : "";
    setPage(m.n, `
      ${crumbs([{ t: "Home", href: "#/" }, { t: b.n, href: href(b.s) }, { t: m.n }])}
      <div class="page-h"><h1>${esc(m.n)}</h1>${m.d ? `<p class="sub">${esc(m.d)}</p>` : ""}</div>
      ${banner}
      <div class="section-h"><h2>${m.p.length} coding procedures</h2></div>
      <div class="model-list">${list}</div>
    `);
    markNav(b.s, m.s);
  }

  function viewCoding(b, m, slug) {
    const page = findPage(b, m, slug);
    if (!page) return viewNotFound();
    const rid = routeId;
    loadModel(b.s, m.s).then(data => {
      if (rid !== routeId) return;
      const html = data[slug];
      if (!html) return viewNotFound();
      const idx = m.p.findIndex(p => p[0] === slug);
      const prev = idx > 0 ? m.p[idx - 1] : null;
      const next = idx < m.p.length - 1 ? m.p[idx + 1] : null;
      const pager = `<div class="pager">
        ${prev ? `<a href="${href(b.s, m.s, prev[0])}"><span class="lab">PREVIOUS</span>${esc(prev[1])}</a>` : "<span></span>"}
        ${next ? `<a class="r" href="${href(b.s, m.s, next[0])}"><span class="lab">NEXT</span>${esc(next[1])}</a>` : "<span></span>"}
      </div>`;
      setPage(page[1], `
        ${crumbs([{ t: "Home", href: "#/" }, { t: b.n, href: href(b.s) }, { t: m.n, href: href(b.s, m.s) }, { t: page[1] }])}
        <div class="page-h"><h1>${esc(page[1])}</h1></div>
        <article class="doc">${html}</article>
        ${pager}
        <div class="page-foot"><span>Source: <a href="${sourceUrl(b.s, m.s, slug)}" target="_blank" rel="noopener">vag-coding.net</a></span><span>${esc(b.n)} · ${esc(m.n)}</span></div>
      `);
      markNav(b.s, m.s);
    }).catch(() => { if (rid === routeId) viewLoadError(); });
    main.innerHTML = `<p style="color:var(--mut);padding:40px 0">Loading…</p>`;
  }

  function viewTutorials() {
    const t = window.VI.t || [];
    const list = t.map(p => `<a href="${href("t", p[0])}"><span>${esc(p[1])}</span><span class="arrow">→</span></a>`).join("");
    setPage("Tutorials", `
      ${crumbs([{ t: "Home", href: "#/" }, { t: "Tutorials" }])}
      <div class="page-h"><h1>Tutorials &amp; information</h1><p class="sub">${t.length} guides on tools, backups and diagnostics</p></div>
      <div class="model-list">${list}</div>
    `);
    markNav();
  }

  function viewTutorial(slug) {
    const page = (window.VI.t || []).find(p => p[0] === slug);
    if (!page) return viewNotFound();
    const rid = routeId;
    loadTutorials().then(data => {
      if (rid !== routeId) return;
      const html = data[slug];
      if (!html) return viewNotFound();
      const src = "https://www.vag-coding.net/" + (page[2] || ("tutorials-information/" + slug)) + "/";
      setPage(page[1], `
        ${crumbs([{ t: "Home", href: "#/" }, { t: "Tutorials", href: "#/tutorials" }, { t: page[1] }])}
        <div class="page-h"><h1>${esc(page[1])}</h1></div>
        <article class="doc">${html}</article>
        <div class="page-foot"><span>Source: <a href="${src}" target="_blank" rel="noopener">vag-coding.net</a></span></div>
      `);
      markNav();
    }).catch(() => { if (rid === routeId) viewLoadError(); });
    main.innerHTML = `<p style="color:var(--mut);padding:40px 0">Loading…</p>`;
  }

  function viewAbout() {
    const download = location.protocol === "file:" ? "" :
      `<a class="btn" href="VAG-Coding-offline.zip" download>Download offline copy <span>.zip</span></a>`;
    setPage("About", `
      ${crumbs([{ t: "Home", href: "#/" }, { t: "About" }])}
      <div class="page-h"><h1>About</h1></div>
      <div class="doc about">
        <p>A faster, cleaner front end for the coding reference published at <a href="https://www.vag-coding.net/" target="_blank" rel="noopener">vag-coding.net</a>, published with permission. Data captured 2026-10-29.</p>
        <h2>Offline</h2>
        <p>Prefer a local copy? The ZIP runs entirely from your hard drive — no server or internet connection needed. Extract it and open <code>index.html</code>.</p>
        ${download}
        <h2>Coding is risky</h2>
        <p>Always make a backup before changing anything. Incorrect coding can brick modules, and some procedures differ between model years and equipment levels.</p>
      </div>
    `);
    markNav();
  }

  function viewNotFound() {
    setPage("Not found", `
      <div class="page-h"><h1>Not found</h1><p class="sub">That page is not in this copy.</p></div>
      <p><a href="#/">Back to home</a></p>
    `);
    markNav();
  }
  function viewLoadError() {
    setPage("Error", `<div class="page-h"><h1>Could not load data</h1><p class="sub">The data file is missing or blocked. If you opened this from a file manager, make sure the whole folder was extracted.</p></div>`);
  }

  /* ---------- router ---------- */
  function route() {
    const nextHash = location.hash || "#/";
    if (activeHash !== nextHash) {
      scrollPositions.set(activeHash, window.scrollY);
      activeHash = nextHash;
      pendingRestore = scrollPositions.get(nextHash) || 0;
    }
    routeId++;
    hideResults();
    const parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean).map(decodeURIComponent);
    if (!parts.length) return viewHome();
    if (parts[0] === "tutorials") return viewTutorials();
    if (parts[0] === "about") return viewAbout();
    if (parts[0] === "t") return viewTutorial(parts[1] || "");
    const b = brandBySlug[parts[0]];
    if (!b) return viewNotFound();
    if (parts.length === 1) return viewBrand(b);
    const m = b.m.find(x => x.s === parts[1]);
    if (!m) return viewNotFound();
    if (parts.length === 2) return viewModel(b, m);
    return viewCoding(b, m, parts[2]);
  }
  window.addEventListener("hashchange", route);

  /* ---------- search ---------- */
  function buildSearchIndex() {
    if (searchIndex) return searchIndex;
    const out = [];
    for (const b of window.VI.b) {
      out.push({ s: b.s, t: b.n, b: b.s, bn: b.n, m: "", mn: "", full: b.n + " brand", kind: "brand" });
      for (const m of b.m) {
        out.push({ s: m.s, t: m.n, b: b.s, bn: b.n, m: m.s, mn: m.n, full: m.n + " " + b.n + " model", kind: "model" });
        for (const p of m.p) {
          out.push({ s: p[0], t: p[1], b: b.s, bn: b.n, m: m.s, mn: m.n, full: p[1] + " " + m.n + " " + b.n });
        }
      }
    }
    for (const p of window.VI.t || []) out.push({ s: p[0], t: p[1], b: "t", bn: "Tutorials", m: "", mn: "", full: p[1] + " tutorial" });
    searchIndex = out;
    return out;
  }
  function highlight(text, q) {
    const i = text.toLowerCase().indexOf(q);
    if (i < 0) return esc(text);
    return esc(text.slice(0, i)) + "<b>" + esc(text.slice(i, i + q.length)) + "</b>" + esc(text.slice(i + q.length));
  }
  function search(q) {
    q = q.trim().toLowerCase();
    if (!q) return [];
    const hits = [];
    for (const it of buildSearchIndex()) {
      const t = it.t.toLowerCase(), f = it.full.toLowerCase();
      let score = -1;
      if (t === q) score = 0;
      else if (t.startsWith(q)) score = 1;
      else if (t.split(/[\s–-]+/).some(w => w.startsWith(q))) score = 2;
      else if (t.includes(q)) score = 3;
      else if (f.includes(q)) score = 4;
      if (score >= 0) hits.push([score, it]);
    }
    hits.sort((a, b) => a[0] - b[0] || a[1].t.length - b[1].t.length);
    return hits.slice(0, 40).map(h => h[1]);
  }
  let activeIdx = -1;
  function hideResults() {
    results.hidden = true;
    input.closest(".search-wrap").classList.remove("open");
    results.innerHTML = "";
    activeIdx = -1;
  }
  function showResults(q) {
    const hits = search(q);
    activeIdx = -1;
    if (!hits.length) {
      results.innerHTML = `<div class="result-empty">No match for “${esc(q)}”.</div>`;
    } else {
      results.innerHTML = hits.map((it, i) => {
        let url, path;
        if (it.kind === "brand") { url = href(it.b); path = "Brand"; }
        else if (it.kind === "model") { url = href(it.b, it.m); path = `${esc(it.bn)} · Model`; }
        else {
          url = it.b === "t" ? href("t", it.s) : href(it.b, it.m, it.s);
          path = it.b === "t" ? "Tutorials" : `${esc(it.bn)} · ${esc(it.mn)}`;
        }
        return `<a class="result" role="option" data-i="${i}" href="${url}">${highlight(it.t, q.toLowerCase())}<span class="r-path">${path}</span></a>`;
      }).join("");
    }
    results.hidden = false;
    input.closest(".search-wrap").classList.add("open");
  }
  input.addEventListener("input", () => {
    const q = input.value.trim();
    if (q.length < 2) return hideResults();
    showResults(q);
  });
  input.addEventListener("focus", () => { if (input.value.trim().length >= 2) showResults(input.value.trim()); });
  input.addEventListener("keydown", e => {
    const opts = results.querySelectorAll(".result");
    if (e.key === "Escape") { hideResults(); input.blur(); return; }
    if (!opts.length) return;
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      activeIdx = e.key === "ArrowDown" ? Math.min(activeIdx + 1, opts.length - 1) : Math.max(activeIdx - 1, 0);
      opts.forEach((o, i) => o.classList.toggle("active", i === activeIdx));
      opts[activeIdx].scrollIntoView({ block: "nearest" });
    } else if (e.key === "Enter" && opts.length) {
      const o = opts[activeIdx >= 0 ? activeIdx : 0];
      location.hash = o.getAttribute("href");
      hideResults();
      input.blur();
    }
  });
  results.addEventListener("click", () => { hideResults(); input.blur(); });
  document.addEventListener("click", e => { if (!e.target.closest(".search-wrap")) hideResults(); });
  document.addEventListener("keydown", e => {
    if (e.key === "/" && document.activeElement !== input && !/input|textarea|select/i.test(document.activeElement.tagName)) {
      e.preventDefault(); input.focus();
    }
  });

  /* ---------- lightbox ---------- */
  const box = $("#lightbox");
  main.addEventListener("click", e => {
    const img = e.target.closest(".doc img");
    if (img) {
      e.preventDefault();
      box.querySelector("img").src = img.src;
      box.querySelector("img").alt = img.alt || "";
      box.hidden = false;
    }
  });
  box.addEventListener("click", () => { box.hidden = true; box.querySelector("img").src = ""; });
  document.addEventListener("keydown", e => { if (e.key === "Escape" && !box.hidden) box.hidden = true; });

  /* ---------- boot ---------- */
  $(".skip").addEventListener("click", e => { e.preventDefault(); main.focus(); main.scrollIntoView(); });
  input.placeholder = "Search " + window.VI.n.toLocaleString("en") + " procedures…";
  renderNav();
  route();
})();
