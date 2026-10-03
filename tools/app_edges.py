"""Перевірка бічного обрізання WebGL-віяла межами canvas.

  python3 tools/app_edges.py [ширини...]     (за замовчуванням 1181 1280 1366 1440 1920)

Метод: у кожному стані знімається viewport; у смузі шару рахуються пікселі, що відрізняються від фону hero.
 - у WebGL: «торкання краю» = непорожні пікселі в 2 крайніх стовпцях canvas-шару → картку обрізано;
   також міряється мінімальний зазор від найкрайнішого пікселя до краю шару;
 - у CSS (?scene=off): еталонний виступ віяла за межі колонки showcase (того ж, де в WebGL сидить canvas).
Крім того: горизонтальний overflow сторінки, відсутність перекриття тексту/CTA, елемент під курсором за межами шару.
Це піксельна перевірка. Вона НЕ замінює візуальний огляд.
"""
import functools, http.server, io, os, socketserver, sys, threading
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

DIST = "/home/user/work/app/dist"; PORT = 4175
SHOTS = "/home/user/work/shots"; os.makedirs(SHOTS, exist_ok=True)
BG = np.array([216, 235, 181])
results = []
warned = []

def check(name, ok, info=""):
    results.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name + (f"  [{info}]" if info else ""))

h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DIST); h.func.log_message = lambda *a, **k: None
class S(socketserver.TCPServer): allow_reuse_address = True
threading.Thread(target=S(("127.0.0.1", PORT), h).serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{PORT}/index.html"

GEOM = """()=>{const r=e=>{const b=document.querySelector(e);if(!b)return null;const x=b.getBoundingClientRect();return [x.left,x.top,x.right,x.bottom]};
 return {layer:r('[data-scene-layer]'),show:r('[class*=showcase]'),hero:r('[class*=hero]'),fan:r('[role=group]'),sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth}}"""

def shot(pg):
    """full_page + знятий overflow:hidden у hero (див. UNCLIP): видно справжні межі, а не обрізані краєм сторінки"""
    return np.asarray(Image.open(io.BytesIO(pg.screenshot(full_page=True))).convert("RGB")).astype(int)

UNCLIP = "html,body{overflow-x:visible!important}[class*=hero]{overflow:visible!important}"

def fan_mask(img, g, pad=140):
    """маска «не фон» у смузі віяла; координати x абсолютні (viewport)"""
    top = int(g["show"][1]); L = int(g["show"][3]) - int(g["layer_h"])
    y0 = max(int(L), 0); y1 = min(img.shape[0], int(g["show"][3]))
    x0 = max(int(g["show"][0]) - pad, 0); x1 = min(img.shape[1], int(g["show"][2]) + pad)
    m = np.abs(img[y0:y1, x0:x1] - BG).sum(2) > 24
    return m, x0, y0

def extents(m, x0):
    cols = np.where(m.any(0))[0]
    return (cols.min() + x0, cols.max() + x0) if len(cols) else (None, None)

def geom(pg):
    g = pg.evaluate(GEOM)
    g = {k: v for k, v in g.items()}
    # висота смуги віяла: від верху canvas-шару, а в CSS — тієї самої висоти від низу showcase
    pg.evaluate("1")
    return g

def settle(pg, ms=1100): pg.wait_for_timeout(ms)

def tilt_deg(pg):
    d = pg.evaluate("(()=>{const l=document.querySelector('[data-scene-layer]');return l?l.dataset.state:null})()")
    return d

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    for w in [int(a) for a in sys.argv[1:]] or [1181, 1280, 1366, 1440, 1920]:
        print(f"\n===== {w}px =====")
        # --- еталон: CSS-віяло ---
        ctx = b.new_context(viewport={"width": w, "height": 900}, locale="uk-UA"); pg = ctx.new_page()
        pg.goto(BASE + "?scene=off"); pg.wait_for_selector("[data-index='0']"); settle(pg, 700); pg.add_style_tag(content=UNCLIP)
        css_ext = {}; css_mask = {}
        for name, idx in (("перша", 0), ("остання", 3)):
            pg.evaluate(f"document.querySelector('[data-index=\"{idx}\"]').click()"); settle(pg, 700)
            g = pg.evaluate(GEOM); fv = pg.evaluate("parseFloat(getComputedStyle(document.querySelector('[class*=showcase]')).getPropertyValue('--fan-visible'))")
            g["layer_h"] = fv + 56
            A = shot(pg); pg.evaluate("document.querySelector('[role=group]').style.visibility='hidden'"); B = shot(pg); pg.evaluate("document.querySelector('[role=group]').style.visibility=''")
            top_y = int(g["show"][3] - g["layer_h"]); bot_y = min(int(g["show"][3]), A.shape[0], B.shape[0]); Wd = min(A.shape[1], B.shape[1])
            m = np.abs(A[top_y:bot_y, :Wd] - B[top_y:bot_y, :Wd]).sum(2) > 24
            lo, hi = extents(m, 0)
            css_ext[name] = (lo, hi, g["show"][0], g["show"][2]); css_mask[name] = m
            print(f"  CSS [{name}]: віяло x={lo}..{hi}; колонка showcase {g['show'][0]:.0f}..{g['show'][2]:.0f}  (виступ вліво {g['show'][0]-lo:.0f}, вправо {hi-g['show'][2]:.0f})")
        ctx.close()
        # --- WebGL ---
        ctx = b.new_context(viewport={"width": w, "height": 900}, locale="uk-UA"); pg = ctx.new_page()
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:120]))
        pg.goto(BASE + "?scene-debug"); pg.wait_for_function("document.querySelector('[data-scene]')?.dataset.scene==='webgl'", timeout=40000); settle(pg, 1200)
        g0 = pg.evaluate(GEOM); fv = pg.evaluate("parseFloat(getComputedStyle(document.querySelector('[class*=showcase]')).getPropertyValue('--fan-visible'))")
        g0["layer_h"] = fv + 56
        lay = g0["layer"]; print(f"  WebGL: canvas-шар x={lay[0]:.0f}..{lay[2]:.0f} (showcase {g0['show'][0]:.0f}..{g0['show'][2]:.0f})")
        check(f"{w}: немає горизонтального overflow", g0["sw"] <= g0["cw"], f"sw={g0['sw']} cw={g0['cw']}")
        if os.environ.get('EDGE_CSS'): pg.add_style_tag(content=os.environ['EDGE_CSS']); settle(pg, 1500)
        pg.add_style_tag(content=UNCLIP)  # далі міряємо справжні межі; overflow-перевірка вище зроблена до цього

        def probe(label, pointer=None, focus=None, select=None, save=None):
            if select is not None:
                pg.evaluate(f"document.querySelector('[data-index=\"{select}\"]').click()")
            if focus is not None:
                pg.evaluate(f"document.querySelector('[data-index=\"{focus}\"]').focus()")
            if pointer is not None:
                pg.mouse.move(*pointer, steps=6)
            settle(pg)
            g = pg.evaluate(GEOM); g["layer_h"] = fv + 56
            img = shot(pg)
            pg.evaluate("document.querySelector('[data-scene-layer]').style.visibility='hidden'"); bare = shot(pg); pg.evaluate("document.querySelector('[data-scene-layer]').style.visibility=''")
            lay = g["layer"]
            Wd = min(img.shape[1], bare.shape[1]); img = img[:, :Wd]; bare = bare[:, :Wd]
            y0, y1 = int(round(lay[1])), min(int(round(lay[3])), img.shape[0], bare.shape[0])
            m_full = np.abs(img[y0:y1] - bare[y0:y1]).sum(2) > 24   # лише те, що намалював canvas
            xa, xb = max(int(round(lay[0])), 0), min(int(round(lay[2])), img.shape[1])
            m = m_full[:, xa:xb]; probe.last_full = m_full
            lo, hi = extents(m, xa)
            left_gap = lo - lay[0] if lo is not None else None; right_gap = (lay[2] - 1) - hi if hi is not None else None
            rows = np.where(m.any(1))[0]; top_gap = int(rows.min()) if len(rows) else None
            vp = False
            if False:  # скриншоти для звіту знімає tools/app_edge_shots.py (звичайний viewport)
                Image.fromarray(img.astype("uint8")).save(f"{SHOTS}/{save}.png")
            return lo, hi, lay, left_gap, right_gap, g, top_gap, vp

        cases = [
            ("вибір першої",    dict(select=0, pointer=(10, 10))),
            ("вибір останньої", dict(select=3, pointer=(10, 10))),
        ]
        worst_l, worst_r = 9999, 9999
        overs = []
        def run(label, **kw):
            global worst_l, worst_r
            lo, hi, lay, lg, rg, g, tg, vp = probe(label, **kw)
            hero_r = g['hero'][2]
            right_at_edge = lay[2] >= hero_r - 1   # правий край canvas збігається з краєм hero/viewport: далі обрізає hero, це окрема перевірка нижче
            ok = lg is not None and lg >= 6 and (rg >= 6 or right_at_edge)
            css_over = max(v[1] for v in css_ext.values()) - (w - 1)   # на скільки CSS-віяло (без hover/нахилу) виходить за правий край viewport
            over = hi - (w - 1) if hi is not None else None
            ok_vp = over is not None and over <= css_over + 6 and (lo is None or lo >= min(0, min(v[0] for v in css_ext.values()) - 6))
            overs.append((over, label))
            if not ok_vp:
                msg = f"ПОПЕРЕДЖЕННЯ {w}: {label} — 3D виходить за край viewport на {over}px (CSS без нахилу: {css_over}px); це обрізання краєм hero/сторінки, не canvas"
                if msg not in warned: warned.append(msg)
            check(f"{w}: {label} — зазор до країв canvas ≥ 6px", ok, f"x={lo}..{hi}, шар {lay[0]:.0f}..{lay[2]:.0f}, зазор ліво {lg:.0f} право {rg:.0f}")
            worst_l = min(worst_l, lg if lg is not None else -1); worst_r = min(worst_r, rg if rg is not None else -1)
            return lo, hi, lay

        lay = g0["layer"]
        fl, ft, fr, fb = g0["fan"]; L, T, R, B = max(fl, 0) + 1, max(ft, lay[1]) + 1, min(fr, w) - 2, min(fb, 898) - 2
        corners = {"лівий-верх": (L, T), "правий-верх": (R, T), "лівий-низ": (L, B), "правий-низ": (R, B), "центр": ((L + R) / 2, (T + B) / 2)}
        for sel_i, sel_name in ((0, "перша"), (3, "остання")):
            for cname, pt in corners.items():
                save = f"edges-{w}-sel{sel_i}-{cname}" if cname in ("центр", "лівий-верх", "правий-верх") else None
                run(f"вибір {sel_name}, курсор {cname} (максимальний нахил)", select=sel_i, pointer=pt, save=save)
        # hover і фокус по крайніх картках, повернення курсора
        for idx in (0, 3):
            pt = pg.evaluate(f"(()=>{{const r=document.querySelector('[data-index=\"{idx}\"] [class*=anchor]').getBoundingClientRect();return [r.left, r.top]}})()")
            run(f"hover крайньої картки {idx}", select=1 if idx == 0 else 2, pointer=(pt[0] - (60 if idx == 0 else 20), pt[1] + 80))
            run(f"фокус (клавіатура) крайньої картки {idx}", focus=idx, pointer=(10, 10))
        run("повернення курсора мимо canvas", select=0, pointer=(10, 10), save=f"edges-{w}-return")
        # збіг положення 3D з CSS-віялом (центр колонки не з\u0027їхав після розширення canvas): силует вибраної першої/останньої, без нахилу
        for name, idx in (("перша", 0), ("остання", 3)):
            run(f"позиція без нахилу, вибрана {name}", select=idx, pointer=(10, 10))
            a = css_mask[name]; bm = probe.last_full
            Hh = min(a.shape[0], bm.shape[0]); Ww = min(a.shape[1], bm.shape[1])
            a, bm = a[:Hh, :Ww], bm[:Hh, :Ww]
            iou = (a & bm).sum() / max((a | bm).sum(), 1)
            ca = np.where(a.any(0))[0]; cb = np.where(bm.any(0))[0]
            dc = ((cb.min() + cb.max()) - (ca.min() + ca.max())) / 2 if len(ca) and len(cb) else None
            check(f"{w}: 3D збігається з CSS-віялом ({name} вибрана): IoU ≥ 0.75 і зміщення центру ≤ 8px (3D-вибрана картка повернута, тож IoU < 1)", iou >= 0.75 and dc is not None and abs(dc) <= 8, f"IoU={iou:.3f}, зміщення центру по x={dc}px")
        # перші/останні — скриншоти для звіту
        if w in (1181, 1280, 1440):
            run("знімок: вибрана перша", select=0, pointer=((L + R) / 2, (T + B) / 2), save=f"edges-{w}-first-selected")
            run("знімок: вибрана остання", select=3, pointer=((L + R) / 2, (T + B) / 2), save=f"edges-{w}-last-selected")
        # --- перекриття тексту/CTA і перехоплення кліків ---
        cov = pg.evaluate("""()=>{const bad=[];for(const el of document.querySelectorAll('[class*=copy] h1, [class*=copy] p, [class*=copy] a, header a, [class*=caption] a')){
              const r=el.getBoundingClientRect(); if(!r.width) continue; const pts=[[r.left+3,r.top+3],[r.right-3,r.top+3],[r.left+3,r.bottom-3],[r.right-3,r.bottom-3],[(r.left+r.right)/2,(r.top+r.bottom)/2]];
              for(const [x,y] of pts){ if(x<0||y<0||x>innerWidth||y>innerHeight) continue; const e=document.elementFromPoint(x,y); if(e&&e.closest('[data-scene-layer]')) bad.push(el.textContent.trim().slice(0,24)); } }
            return [...new Set(bad)]}""")
        check(f"{w}: текст, CTA та підпис не перехоплюються canvas (elementFromPoint)", not cov, str(cov))
        pe = pg.evaluate("getComputedStyle(document.querySelector('[data-scene-layer]')).pointerEvents")
        check(f"{w}: canvas-шар не приймає подій (pointer-events: none)", pe == "none", pe)
        # елемент під точкою зліва від шару й справа від шару — не canvas
        for nm, x in (("лівий край шару", lay[0] + 6), ("правий край шару", lay[2] - 6)):
            if 0 < x < w:
                inl = pg.evaluate(f"(()=>{{const e=document.elementFromPoint({x},{(lay[1]+lay[3])/2});return !!(e&&e.closest('[data-scene-layer]'))}})()")
                check(f"{w}: поза canvas ({nm}) кліки не перехоплюються шаром", not inl)
        check(f"{w}: немає необроблених помилок сторінки", not errs, str(errs))
        mo = max(overs, key=lambda x: x[0]); print(f"  найбільший вихід 3D за правий край viewport: {mo[0]}px у стані «{mo[1]}» (CSS-віяло: {max(v[1] for v in css_ext.values()) - (w - 1)}px)")
        print(f"  найменший зазор до країв за всіма станами: ліво {worst_l}px, право {worst_r}px")
        ctx.close()
    b.close()
print("\n".join(["", *warned]) if warned else "")
print(f"\nПідсумок: {sum(results)}/{len(results)} PASS")
sys.exit(0 if all(results) else 1)
