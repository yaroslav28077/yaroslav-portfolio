"""Скриншоти для перевірки бічного обрізання (звичайний viewport, без зміни стилів сторінки).

  python3 tools/app_edge_shots.py

Зберігає в /home/user/work/shots/edge-*.png. Для кожного кадру «-bounds» додатково малює
пунктирний контур меж canvas-шару (тільки в знімку, на сайті нічого не змінюється).
"""
import functools, http.server, os, socketserver, threading
import sys
sys.path.insert(0, os.path.dirname(__file__))
from playwright.sync_api import sync_playwright
from pwutil import ensure_images_loaded

DIST = "/home/user/work/app/dist"; PORT = 4178; SHOTS = "/home/user/work/shots"
h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DIST); h.func.log_message = lambda *a, **k: None
class S(socketserver.TCPServer): allow_reuse_address = True
threading.Thread(target=S(("127.0.0.1", PORT), h).serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{PORT}/index.html"
OUTLINE = """(on)=>{let o=document.getElementById('__bounds'); if(!on){o&&o.remove();return}
  const l=document.querySelector('[data-scene-layer]').getBoundingClientRect(); o=document.createElement('div'); o.id='__bounds';
  o.style.cssText=`position:fixed;left:${l.left}px;top:${l.top}px;width:${l.width}px;height:${l.height}px;outline:2px dashed #d00;pointer-events:none;z-index:99999`; document.body.appendChild(o)}"""

def fan_pt(pg, where):
    r = pg.evaluate("(()=>{const b=document.querySelector('[role=group]').getBoundingClientRect(); return [b.left,b.top,b.right,b.bottom]})()")
    l, t, rr, b = r
    return {"center": ((l + rr) / 2, (t + b) / 2), "left-bottom": (l + 1, b - 2), "right-bottom": (rr - 2, b - 2)}[where]

with sync_playwright() as p:
    br = p.chromium.launch(headless=True)
    def page(w, scene=True):
        ctx = br.new_context(viewport={"width": w, "height": 900}, locale="uk-UA"); pg = ctx.new_page()
        pg.goto(BASE + ("?scene-debug" if scene else "?scene=off"))
        if scene: pg.wait_for_function("document.querySelector('[data-scene]')?.dataset.scene==='webgl'", timeout=40000)
        else: pg.wait_for_selector("[data-index='0']")
        ensure_images_loaded(pg, rendered_only=True); pg.wait_for_timeout(900)
        return ctx, pg
    def snap(pg, name, select=None, where=None):
        if select is not None: pg.evaluate(f"document.querySelector('[data-index=\"{select}\"]').click()")
        if where: pg.mouse.move(*fan_pt(pg, where), steps=8)
        pg.wait_for_timeout(1200)
        pg.screenshot(path=f"{SHOTS}/edge-{name}.png")
        if pg.query_selector("[data-scene-layer]"):
            pg.evaluate(OUTLINE, True); pg.screenshot(path=f"{SHOTS}/edge-{name}-bounds.png"); pg.evaluate(OUTLINE, False)
    # 1440: CSS і WebGL
    ctx, pg = page(1440, scene=False); snap(pg, "1440-css-first", 0); snap(pg, "1440-css-last", 3); ctx.close()
    ctx, pg = page(1440); snap(pg, "1440-webgl-first", 0, "center"); snap(pg, "1440-webgl-last", 3, "center")
    snap(pg, "1440-webgl-first-tilt-left", 0, "left-bottom"); snap(pg, "1440-webgl-last-tilt-right", 3, "right-bottom"); snap(pg, "1440-webgl-last-tilt-left", 3, "left-bottom"); ctx.close()
    for w in (1181, 1280, 1920):
        ctx, pg = page(w); snap(pg, f"{w}-webgl-first", 0, "center"); snap(pg, f"{w}-webgl-last", 3, "center"); ctx.close()
    ctx, pg = page(1181, scene=False); snap(pg, "1181-css-last", 3); ctx.close()
    br.close()
print("ok")
