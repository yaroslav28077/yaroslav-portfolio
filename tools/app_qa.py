"""Перевірка зібраного React-застосунку (dist) у Chromium.

  cd /home/user/work/app && npm run build
  python3 /home/user/yaroslav-portfolio/tools/app_qa.py [dist_dir]

Перевіряє ширини 360, 390, 768, 1024, 1440: overflow, вихід тексту за межі, touch targets, контраст,
помилки консолі, завантаження ВСІХ зображень, взаємодії (віяло, підпис, меню, стрічка).
Скриншоти: /home/user/work/shots/<width>-{hero,full}.png, потім WebP у previews-app/.
Увага: цей скрипт НЕ замінює візуальний огляд. Він перевіряє DOM і поведінку.
"""
import functools, http.server, json, os, socketserver, sys, threading
sys.path.insert(0, os.path.dirname(__file__))
from playwright.sync_api import sync_playwright
from pwutil import ensure_images_loaded, lazy_state

DIST = "/home/user/work/app/dist"
QUERY = sys.argv[1] if len(sys.argv) > 1 else ""   # напр. "?scene=off" (CSS-віяло) або "" (на 1440 увімкнеться WebGL)
TAG = "css" if "scene=off" in QUERY else "auto"
PORT = 4173
SHOTS = "/home/user/work/shots"
os.makedirs(SHOTS, exist_ok=True)

def serve():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DIST)
    handler.func.log_message = lambda *a, **k: None
    class S(socketserver.TCPServer):
        allow_reuse_address = True
    srv = S(("127.0.0.1", PORT), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv

JS_LAYOUT = r"""
() => {
  const out = {}; const vw = document.documentElement.clientWidth;
  out.pageOverflow = document.documentElement.scrollWidth > vw + 1;
  const inScroller = e => { for (let n = e.parentElement; n && n !== document.body; n = n.parentElement) { const o = getComputedStyle(n).overflowX; if (o === 'auto' || o === 'scroll') return true; } return false; };
  const vis = e => { const r = e.getBoundingClientRect(), cs = getComputedStyle(e); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
  out.wide = [...document.querySelectorAll('body *')].filter(e => vis(e) && !inScroller(e) && e.getBoundingClientRect().right > vw + 2 && !e.closest('.visually-hidden, [class*=visually], .skip-link:not(:focus)'))
      .slice(0, 5).map(e => e.tagName + '.' + String(e.className).slice(0, 30) + ' ' + Math.round(e.getBoundingClientRect().right));
  // touch targets
  const inter = [...document.querySelectorAll('a[href], button, [role=button]')].filter(e => vis(e) && !e.closest('.visually-hidden, .skip-link:not(:focus)'));
  out.interactive = inter.length;
  out.small = inter.filter(e => { const r = e.getBoundingClientRect(); return r.height < 44 || r.width < 44; })
    .map(e => e.tagName + ':' + (e.innerText || e.getAttribute('aria-label') || '').trim().slice(0, 26) + ' ' + Math.round(e.getBoundingClientRect().width) + 'x' + Math.round(e.getBoundingClientRect().height));
  // текст, що виходить за свій блок
  const bad = [];
  document.querySelectorAll('h1,h2,h3,p,li,dd,dt,a,button').forEach(e => {
    if (!vis(e) || inScroller(e) && false) return;
    const tw = document.createTreeWalker(e, NodeFilter.SHOW_TEXT); let R = -1e9, L = 1e9;
    while (tw.nextNode()) { const n = tw.currentNode; if (!n.nodeValue.trim() || n.parentElement.closest('.visually-hidden, .skip-link:not(:focus)')) continue; const rg = document.createRange(); rg.selectNodeContents(n); const q = rg.getBoundingClientRect(); if (q.width) { R = Math.max(R, q.right); L = Math.min(L, q.left); } }
    const b = e.getBoundingClientRect();
    if (R > b.right + 2 && getComputedStyle(e).display !== 'inline') bad.push(e.tagName + ' "' + e.textContent.trim().slice(0, 24) + '" ' + Math.round(R) + '>' + Math.round(b.right));
    if (!inScroller(e) && (R > vw + 1 || L < -1)) bad.push('viewport: ' + e.tagName + ' "' + e.textContent.trim().slice(0, 24) + '"');
  });
  out.textOut = bad.slice(0, 6);
  // контраст (суцільні фони)
  const lum = c => { const a = c.map(v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }); return .2126 * a[0] + .7152 * a[1] + .0722 * a[2]; };
  const parse = s => { const m = s.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(',').map(parseFloat); return { rgb: p.slice(0, 3), a: p.length > 3 ? p[3] : 1 }; };
  const bgOf = e => { for (let n = e; n; n = n.parentElement) { const c = parse(getComputedStyle(n).backgroundColor); if (c && c.a > .5) return c.rgb; } return [255, 255, 255]; };
  const low = [], seen = new Set(); const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (w.nextNode()) { const n = w.currentNode; const e = n.parentElement; if (!n.nodeValue.trim() || !e || seen.has(e) || !vis(e) || e.closest('.visually-hidden, .skip-link:not(:focus)')) continue; seen.add(e);
    const cs = getComputedStyle(e), fg = parse(cs.color); if (!fg) continue; const L1 = lum(fg.rgb), L2 = lum(bgOf(e)); const cr = (Math.max(L1, L2) + .05) / (Math.min(L1, L2) + .05);
    const fs = parseFloat(cs.fontSize), bold = parseInt(cs.fontWeight) >= 700; const need = (fs >= 24 || (fs >= 18.66 && bold)) ? 3 : 4.5;
    if (cr < need) low.push(e.tagName + ':' + e.textContent.trim().slice(0, 22) + ' ' + cr.toFixed(2) + '<' + need); }
  out.lowContrast = low.slice(0, 8);
  const cta = [...document.querySelectorAll('a')].filter(e => /Переглянути роботи|Обговорити проєкт/.test(e.innerText) && vis(e) && e.closest('section'));
  out.ctaFirstScreen = cta.filter(e => e.getBoundingClientRect().bottom <= innerHeight).map(e => e.innerText.trim());
  out.heroBottom = Math.round(document.querySelector('section').getBoundingClientRect().bottom + scrollY);
  out.minFont = Math.min(...[...seen].map(e => parseFloat(getComputedStyle(e).fontSize)));
  return out;
}
"""

def sel(name):  # CSS Modules хешують імена: шукаємо за фрагментом
    return f'[class*="{name}"]'

def run():
    serve()
    report = {}
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        for w, h in ((360, 740), (390, 844), (768, 1024), (1024, 768), (1440, 900)):
            mobile = w < 768
            ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2 if mobile else 1,
                                is_mobile=mobile, has_touch=mobile, locale="uk-UA")
            pg = ctx.new_page(); errs, fails = [], []
            warns = []
            pg.on("console", lambda m, e=errs, w=warns: e.append(m.text) if m.type == "error" else (w.append(m.text[:100]) if m.type == "warning" else None))
            pg.on("pageerror", lambda x, e=errs: e.append(str(x)))
            pg.on("requestfailed", lambda r, f=fails: f.append(r.url))
            pg.goto(f"http://127.0.0.1:{PORT}/index.html{QUERY}", wait_until="load"); pg.wait_for_timeout(1500)
            pg.evaluate("document.fonts.ready")
            r = pg.evaluate(JS_LAYOUT)
            r["unloadedBeforeScroll"] = lazy_state(pg)
            r["consoleErrors"] = errs; r["failedRequests"] = fails; r["consoleWarnings"] = sorted(set(warns))
            r["fonts"] = pg.evaluate("[...new Set([...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family))]")
            if w in (390, 1440, 768):
                pg.screenshot(path=f"{SHOTS}/{TAG}-{w}-hero.png")
            imgs = ensure_images_loaded(pg); r["images"] = imgs
            if w in (390, 1440, 768):
                pg.screenshot(path=f"{SHOTS}/{TAG}-{w}-full.png", full_page=True)
            r["overflowAfterScroll"] = pg.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
            report[w] = r
            ctx.close()
        b.close()
    json.dump(report, open(f"{SHOTS}/layout-report-{TAG}.json", "w"), ensure_ascii=False, indent=1)
    bad = 0
    for w, r in report.items():
        issues = []
        if r["pageOverflow"] or r["overflowAfterScroll"]: issues.append("PAGE OVERFLOW")
        if r["wide"]: issues.append(f"wide={r['wide']}")
        if r["small"]: issues.append(f"small={r['small']}")
        if r["textOut"]: issues.append(f"textOut={r['textOut']}")
        if r["lowContrast"]: issues.append(f"lowContrast={r['lowContrast']}")
        if r["consoleErrors"] or r["failedRequests"]: issues.append(f"errors={r['consoleErrors']} {r['failedRequests']}")
        bad += bool(issues)
        print(f"[{w}] interactive={r['interactive']} minFont={r['minFont']} ctaFirstScreen={r['ctaFirstScreen']} heroBottom={r['heroBottom']} "
              f"images={r['images']['total']} (lazy {r['images']['lazy']}) unloadedBeforeScroll={r['unloadedBeforeScroll']} fonts={r['fonts']}")
        print("     ", issues or "OK")
    print("widths with issues:", bad)

if __name__ == "__main__":
    run()
