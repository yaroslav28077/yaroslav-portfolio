"""Перевірка R3F-віяла, fallback-ів і перемикання режимів (Chromium, програмний WebGL SwiftShader).

  python3 tools/app_webgl.py

ВАЖЛИВО: у середовищі WebGL малює програмний рендерер (SwiftShader, CPU). Такі перевірки підтверджують
коректність і поведінку, але НЕ підтверджують продуктивність/FPS на реальному (слабкому) пристрої.
Скриншоти цей скрипт зберігає в /home/user/work/shots (webgl-*, fallback-*, mobile-*).
"""
import functools, http.server, math, os, socketserver, sys, threading
sys.path.insert(0, os.path.dirname(__file__))
from playwright.sync_api import sync_playwright
from pwutil import ensure_images_loaded

DIST = "/home/user/work/app/dist"; PORT = 4173; BASE = f"http://127.0.0.1:{PORT}/index.html"
SHOTS = "/home/user/work/shots"; os.makedirs(SHOTS, exist_ok=True)
results = []

def check(name, ok, info=""):
    results.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name + (f"  [{info}]" if info else ""))

try:
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DIST); h.func.log_message = lambda *a, **k: None
    class S(socketserver.TCPServer): allow_reuse_address = True
    threading.Thread(target=S(("127.0.0.1", PORT), h).serve_forever, daemon=True).start()
except OSError:
    pass

TITLES = ["Українська класична гімназія", "Гімназія «Просвіт»", "ЦПРПП м. Лубни", "Тренажер з історії України"]
ANG = [-18, -6, 6, 18]

def scene(pg): return pg.get_attribute("[data-scene]", "data-scene")
def sel(pg): return int(pg.get_attribute("[data-scene]", "data-selected"))
def cap(pg): return pg.inner_text('[class*="captionName"]').strip()
def layer(pg): return pg.evaluate("(()=>{const l=document.querySelector('[data-scene-layer]'); return l? {...l.dataset}:null})()")
def wait_state(pg, want, timeout=20000):
    pg.wait_for_function(f"['{want}'].includes(document.querySelector('[data-scene]').dataset.scene)", timeout=timeout)
def tilt(pg):
    s = layer(pg)["state"]; t = s.split(";")[0].split("=")[1].split(","); return float(t[0]), float(t[1])
def lifts(pg): return [float(v) for v in layer(pg)["state"].split(";")[1].split("=")[1].split(",")]

def new_page(b, w=1440, h=900, **kw):
    ctx = b.new_context(viewport={"width": w, "height": h}, locale="uk-UA", **kw); pg = ctx.new_page()
    pg.errors, pg.warnings, pg.reqs, pg.failed = [], [], [], []
    pg.on("console", lambda m: (pg.errors if m.type == "error" else pg.warnings).append(m.text[:160]) if m.type in ("error", "warning") else None)
    pg.on("pageerror", lambda e: pg.errors.append("pageerror: " + str(e)[:160]))
    pg.on("request", lambda r: pg.reqs.append(r.url.split("/")[-1].split("?")[0]))
    pg.on("requestfailed", lambda r: pg.failed.append(r.url.split("/")[-1]))
    return ctx, pg

def rect(pg, css):
    return pg.evaluate("s=>{const e=document.querySelector(s); if(!e) return null; const r=e.getBoundingClientRect(); return [Math.round(r.left*10)/10,Math.round(r.top*10)/10,Math.round(r.width*10)/10,Math.round(r.height*10)/10]}", css)

def click_point(pg, i):
    """Точка у лівій смузі картки i (під час 3D вона видима): від верхнього центру картки вліво й униз у її системі координат."""
    a = pg.evaluate(f"(()=>{{const r=document.querySelector('[data-index=\"{i}\"] [class*=anchor]').getBoundingClientRect(); return [r.left,r.top]}})()")
    th = math.radians(ANG[i]); ex = (math.cos(th), math.sin(th)); ey = (-math.sin(th), math.cos(th))
    dx, dy = -(75 if i < 3 else 20), 40
    return a[0] + dx * ex[0] + dy * ey[0], a[1] + dx * ex[1] + dy * ey[1]

def css_click(pg, i):
    """Клік по видимій частині CSS-картки i (підбір точки через elementFromPoint, бо сусідні картки перекриваються)."""
    pt = pg.evaluate("""(i) => { const c = document.querySelector('[data-index="'+i+'"]'); const r = c.getBoundingClientRect();
      for (let fy = .06; fy < .95; fy += .05) for (let fx = .04; fx < .98; fx += .04) { const x = r.left + r.width*fx, y = r.top + r.height*fy;
        const el = document.elementFromPoint(x, y); const h = el && el.closest('[data-index]'); if (h && h.dataset.index == String(i)) return [x, y]; } return null; }""", i)
    pg.mouse.click(*pt); pg.wait_for_timeout(300)

def focusables(pg):
    return pg.evaluate("[...document.querySelector('[data-scene]').querySelectorAll('a[href],button,[tabindex],canvas')].filter(e=>{const r=e.getBoundingClientRect(); const cs=getComputedStyle(e); return r.width>0&&cs.visibility!=='hidden'&&(e.tagName!=='CANVAS'||e.tabIndex>=0)&&e.tabIndex>=0}).map(e=>e.tagName).join(',')")

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)

    # ================= A. НОРМАЛЬНИЙ WEBGL (1440, точний вказівник) =================
    print("\n=== A. normal WebGL ===")
    # еталон розкладки: CSS-віяло (?scene=off)
    ctx, css = new_page(b); css.goto(BASE + "?scene=off", wait_until="load"); css.wait_for_timeout(800)
    base = {k: rect(css, s) for k, s in {"hero": "section", "caption": '[class*="_caption_"]', "c0": '[data-index="0"]', "c3": '[data-index="3"]', "h1": "h1"}.items()}
    base_focus = focusables(css); check("еталон: CSS-режим, canvas немає", scene(css) == "css" and css.locator("canvas").count() == 0)
    ctx.close()

    ctx, pg = new_page(b, device_scale_factor=2)   # DPR 2 → ліміт має спрацювати
    pg.goto(BASE + "?scene-debug", wait_until="load")
    t0 = pg.evaluate("performance.now()")
    pre = {k: rect(pg, s) for k, s in {"hero": "section"}.items()}
    wait_state(pg, "webgl"); pg.wait_for_timeout(600)
    check("сцена перейшла в стан webgl", scene(pg) == "webgl", scene(pg))
    d = layer(pg)
    check("canvas існує й має розмір шару", pg.locator("[data-scene-layer] canvas").count() == 1 and rect(pg, "[data-scene-layer] canvas")[2] > 500, str(rect(pg, "[data-scene-layer] canvas")))
    check("НОРМАЛЬНА сцена справді відрендерилась: кадрів > 0, draw calls > 0, трикутників > 0", int(d["frames"]) > 0 and int(d["calls"]) > 0 and int(d["triangles"]) > 0, f"frames={d['frames']} calls={d['calls']} triangles={d['triangles']} textures={d['textures']} geometries={d['geometries']}")
    check("використано програмний рендерер (для звіту)", "SwiftShader" in d["gpu"], d["gpu"])
    check("DPR обмежено ≤ 1.5 (контекст DPR 2)", float(d["dprCap"]) <= 1.5, d["dprCap"])
    cw = pg.evaluate("(()=>{const c=document.querySelector('[data-scene-layer] canvas'); return [c.width, c.clientWidth]})()")
    check("розмір буфера canvas = clientWidth × ≤1.5", cw[0] <= cw[1] * 1.5 + 1, str(cw))
    # chunk не блокує початковий текст і CTA
    timing = pg.evaluate("""() => { const nav = performance.getEntriesByType('navigation')[0]; const fcp = (performance.getEntriesByName('first-contentful-paint')[0]||{}).startTime;
       const r = performance.getEntriesByType('resource').find(e => e.name.includes('FanScene')); return {fcp, domInteractive: nav.domInteractive, chunkStart: r && r.startTime, chunkEnd: r && r.responseEnd} }""")
    check("3D chunk вантажиться після першого малювання (не блокує текст і CTA)", timing["chunkStart"] is not None and timing["fcp"] is not None and timing["chunkStart"] > timing["fcp"], str({k: round(v) if v else v for k, v in timing.items()}))
    check("chunk запитано рівно один раз", sum(1 for r in pg.reqs if r.startswith("FanScene")) == 1, str([r for r in pg.reqs if r.startswith("FanScene")]))
    # піксельна перевірка (діагностика рендера, не огляд): області карток містять картки від canvas
    pg.screenshot(path=f"{SHOTS}/webgl-1440-hero.png", scale="css")
    from PIL import Image
    import numpy as np
    im = np.asarray(Image.open(f"{SHOTS}/webgl-1440-hero.png").convert("RGB")).astype(int)
    boxes = pg.evaluate("[...document.querySelectorAll('[data-index] > span:first-child')].map(s=>{const r=s.getBoundingClientRect();return [r.left,r.top,r.right,r.bottom]})")
    hidden_css = pg.evaluate("[...document.querySelectorAll('[data-index] > span:first-child')].map(s=>getComputedStyle(s).visibility)")
    ok_px = []
    for (l, t, r, bt) in boxes:
        cx, cy = int((l + r) / 2), int((t + bt) / 2); reg = im[cy - 20:cy + 20, cx - 20:cx + 20].reshape(-1, 3)
        ok_px.append(bool((reg.sum(1) > 700).any()) and bool((np.abs(reg - np.array([216, 235, 181])).sum(1) > 60).mean() > .5))
    check("CSS-картки приховано (visibility), а на їхніх місцях малює canvas (світла смуга в зоні кожної картки)", all(v == "hidden" for v in hidden_css) and all(ok_px), f"css={hidden_css} px={ok_px}")
    # розкладка не змінилась
    post = {k: rect(pg, s) for k, s in {"hero": "section", "caption": '[class*="_caption_"]', "c0": '[data-index="0"]', "c3": '[data-index="3"]', "h1": "h1"}.items()}
    # c0 має активний підйом як у CSS-режимі (однаковий стан selected=0)
    check("висота hero не змінилась після появи сцени", pre["hero"][3] == post["hero"][3] == base["hero"][3], f"{pre['hero'][3]} → {post['hero'][3]} (еталон {base['hero'][3]})")
    check("розкладка hero/підпису/кнопок ідентична CSS-режиму (без стрибка)", all(post[k] == base[k] for k in base), str({k: (base[k], post[k]) for k in base if post[k] != base[k]}))
    check("фокусованих елементів стільки ж, canvas не фокусований", focusables(pg) == base_focus, f"{base_focus} → {focusables(pg)}")
    # вибір усіх чотирьох карток кліком по canvas
    for i in range(4):
        x, y = click_point(pg, i); pg.mouse.click(x, y); pg.wait_for_timeout(900)
        a = pg.evaluate(f"(()=>{{const r=document.querySelector('[data-index=\"{i}\"] [class*=anchor]').getBoundingClientRect(); return [r.left+r.width/2, r.top]}})()")
        lead = pg.evaluate("(()=>{const l=document.querySelector('[class*=leader]').getBoundingClientRect(); return [l.left+l.width/2, l.bottom]})()")
        ls = lifts(pg)
        check(f"WebGL: клік по картці {i+1} → підпис «{TITLES[i]}», посилання, aria-pressed", sel(pg) == i and cap(pg) == TITLES[i] and pg.evaluate("[...document.querySelectorAll('[data-index]')].map(b=>b.getAttribute('aria-pressed'))") == ["true" if k == i else "false" for k in range(4)], f"selected={sel(pg)} cap={cap(pg)}")
        check(f"WebGL: картка {i+1} піднята (≈26 px), решта на місці; виносна лінія біля картки", abs(ls[i] - 26) < 1 and all(abs(v) < 1 for k, v in enumerate(ls) if k != i) and abs(lead[0] - a[0]) < 6 and abs(lead[1] - a[1]) < 8, f"lifts={ls} dx={lead[0]-a[0]:.1f} dy={lead[1]-a[1]:.1f}")
    # посилання підпису відповідає вибраній картці
    check("посилання підпису = посилання вибраної роботи", pg.get_attribute('[class*="captionLink"]', "href") == "https://history-ostapenko.netlify.app")
    # hover: курсор і підйом
    x, y = click_point(pg, 1); pg.mouse.move(x, y); pg.wait_for_timeout(900)
    check("hover по картці: курсор-«рука» й підйом ≈20 px", pg.evaluate("document.body.style.cursor") == "pointer" and abs(lifts(pg)[1] - 20) < 1.5, f"cursor={pg.evaluate('document.body.style.cursor')} lifts={lifts(pg)}")
    pg.mouse.move(40, 600); pg.wait_for_timeout(900)
    check("курсор пішов: підйом hover знято, курсор звичайний", pg.evaluate("document.body.style.cursor") in ("", "auto") and abs(lifts(pg)[1]) < 1.5, f"lifts={lifts(pg)}")
    # нахил за курсором і повернення
    pg.mouse.move(700, 600); pg.mouse.move(1300, 760, steps=6); pg.wait_for_timeout(1200)
    tx, ty = tilt(pg); check("м'який нахил за курсором (≤ 3°), ненульовий", 0.003 < abs(ty) <= 0.0501 and abs(tx) <= 0.0351, f"tiltX={tx:.4f} tiltY={ty:.4f} рад")
    pg.mouse.move(40, 120); pg.wait_for_timeout(2500)
    tx, ty = tilt(pg); check("плавне повернення нахилу до нуля після взаємодії", abs(tx) < 0.001 and abs(ty) < 0.001, f"{tx:.5f},{ty:.5f}")
    f1 = int(layer(pg)["frames"]); pg.wait_for_timeout(1500); f2 = int(layer(pg)["frames"])
    check("рендер на вимогу: у спокої нові кадри не малюються", f2 == f1, f"{f1} → {f2}")
    # клавіатура через DOM
    pg.focus('[data-index="0"]'); pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(250)
    check("клавіатура (DOM): ArrowRight переносить фокус на картку 2", pg.evaluate("document.activeElement.dataset.index") == "1")
    pg.wait_for_timeout(700); ls = lifts(pg)
    check("сфокусована картка підіймається у 3D (≈20 px) і має видимий фокус-контур", abs(ls[1] - 20) < 1.5 and pg.evaluate("getComputedStyle(document.activeElement).outlineStyle") == "solid", f"lifts={ls}")
    pg.keyboard.press("Enter"); pg.wait_for_timeout(900)
    check("клавіатура: Enter обирає картку 2 → підпис «Просвіт», підйом 26", sel(pg) == 1 and cap(pg) == TITLES[1] and abs(lifts(pg)[1] - 26) < 1)
    for key, want in (("End", 3), ("Home", 0)):
        pg.keyboard.press(key); pg.keyboard.press("Enter"); pg.wait_for_timeout(700)
        check(f"клавіатура: {key}+Enter → картка {want+1}", sel(pg) == want and cap(pg) == TITLES[want])
    # вибір усіх чотирьох з клавіатури (WebGL активний)
    ok = True
    for i in range(4):
        pg.focus(f'[data-index="{i}"]'); pg.keyboard.press("Enter"); pg.wait_for_timeout(300); ok &= (sel(pg) == i and cap(pg) == TITLES[i])
    check("усі чотири роботи обираються з клавіатури через DOM у WebGL-режимі", ok)
    # поза viewport сцена не малює
    pg.evaluate("window.scrollTo(0, 2600)"); pg.wait_for_timeout(700)
    f1 = int(layer(pg)["frames"]); pg.evaluate("document.querySelector('[data-index=\"2\"]').click()"); pg.wait_for_timeout(700); f2 = int(layer(pg)["frames"])
    check("поза viewport (frameloop=never) кадри не малюються", f1 == f2, f"{f1} → {f2}")
    pg.evaluate("window.scrollTo(0, 0)"); pg.wait_for_timeout(1200)
    check("після повернення у viewport сцена доганяє стан (картка 3 піднята)", abs(lifts(pg)[2] - 26) < 1.5, str(lifts(pg)))
    # Звичайні посилання/CTA поруч доступні
    check("CTA «Переглянути роботи» та «Обговорити проєкт» присутні й видимі", pg.locator("section >> text=Переглянути роботи").is_visible() and pg.locator("section >> text=Обговорити проєкт").is_visible())
    ensure_images_loaded(pg); pg.wait_for_timeout(500)
    pg.screenshot(path=f"{SHOTS}/webgl-1440-full.png", full_page=True)
    pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(500)
    check("overflow сторінки відсутній (WebGL)", not pg.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth"))
    check("помилок консолі немає (WebGL-режим)", not pg.errors, str(pg.errors))
    print("   (попередження, не помилки):", sorted(set(w[:90] for w in pg.warnings)))

    # ================= C. ПЕРЕМИКАННЯ RESPONSIVE (той самий документ) =================
    print("\n=== C. responsive-перемикання ===")
    n_chunk = sum(1 for r in pg.reqs if r.startswith("FanScene"))
    h_wide = rect(pg, "section")[3]
    pg.set_viewport_size({"width": 1024, "height": 800}); pg.wait_for_timeout(1500)
    check("1024: сцену знято, CSS-стрічка, canvas видалено", scene(pg) == "css" and pg.locator("canvas").count() == 0, scene(pg))
    st = pg.evaluate("(()=>{const s=document.querySelector('[role=group]'); return [getComputedStyle(s).overflowX, getComputedStyle(s).scrollSnapType, s.scrollWidth>s.clientWidth]})()")
    check("1024: нативна стрічка scroll-snap без змін", st[0] == "auto" and "mandatory" in st[1] and st[2], str(st))
    check("1024: overflow сторінки відсутній", not pg.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth"))
    check("1024: CSS-картки видимі (не приховані)", pg.evaluate("getComputedStyle(document.querySelector('[data-index=\"0\"] > span:first-child')).visibility") == "visible")
    pg.set_viewport_size({"width": 1440, "height": 900}); wait_state(pg, "webgl", 15000); pg.wait_for_timeout(600)
    check("повернення на 1440: сцена знову webgl без перезавантаження", scene(pg) == "webgl")
    check("модуль сцени не вантажився вдруге", sum(1 for r in pg.reqs if r.startswith("FanScene")) == n_chunk)
    check("висота hero після перемикань та сама", rect(pg, "section")[3] == h_wide, f"{h_wide} → {rect(pg, 'section')[3]}")
    check("після перемикань помилок консолі немає", not pg.errors, str(pg.errors))
    ctx.close()

    # ================= D. FALLBACK-СЦЕНАРІЇ =================
    print("\n=== D. fallback ===")
    # reduced motion
    ctx, pg = new_page(b, reduced_motion="reduce"); pg.goto(BASE + "?scene-debug", wait_until="load"); pg.wait_for_timeout(2500)
    check("reduced motion: CSS-віяло, 3D-модуль НЕ вантажиться, canvas немає", scene(pg) == "css" and not any(r.startswith("FanScene") for r in pg.reqs) and pg.locator("canvas").count() == 0, str([r for r in pg.reqs if 'Fan' in r]))
    check("reduced motion: CSS-картки видимі й клікабельні", pg.evaluate("getComputedStyle(document.querySelector('[data-index=\"0\"] > span:first-child')).visibility") == "visible")
    pg.screenshot(path=f"{SHOTS}/fallback-reduced-1440-hero.png"); ctx.close()
    # немає WebGL (getContext повертає null)
    ctx, pg = new_page(b)
    pg.add_init_script("const o=HTMLCanvasElement.prototype.getContext; HTMLCanvasElement.prototype.getContext=function(t,...a){ if(/webgl/i.test(String(t))) return null; return o.call(this,t,...a) }")
    pg.goto(BASE + "?scene-debug", wait_until="load"); wait_state(pg, "failed", 15000); pg.wait_for_timeout(800)
    check("WebGL недоступний (getContext=null): стан failed, CSS-віяло, canvas прибрано", scene(pg) == "failed" and pg.locator("canvas").count() == 0)
    hh = rect(pg, "section")[3]; check("WebGL недоступний: висота hero як в еталоні", hh == base["hero"][3], f"{hh} vs {base['hero'][3]}")
    check("WebGL недоступний: CSS-картки видимі", pg.evaluate("getComputedStyle(document.querySelector('[data-index=\"0\"] > span:first-child')).visibility") == "visible")
    css_click(pg, 2)
    check("WebGL недоступний: вибір картки працює (CSS)", sel(pg) == 2 and cap(pg) == TITLES[2], cap(pg))
    pg.screenshot(path=f"{SHOTS}/fallback-nowebgl-1440-hero.png")
    check("WebGL недоступний: без необроблених помилок (pageerror)", not [e for e in pg.errors if e.startswith("pageerror")], str(pg.errors[:2]))
    ctx.close()
    # немає WebGLRenderingContext взагалі
    ctx, pg = new_page(b); pg.add_init_script("delete window.WebGLRenderingContext; delete window.WebGL2RenderingContext;")
    pg.goto(BASE, wait_until="load"); pg.wait_for_timeout(2000)
    check("немає WebGLRenderingContext: модуль не вантажиться, CSS-віяло", scene(pg) == "css" and not any(r.startswith("FanScene") for r in pg.reqs))
    ctx.close()
    # помилка завантаження chunk
    ctx, pg = new_page(b); pg.route("**/FanScene-*.js", lambda r: r.abort())
    pg.goto(BASE, wait_until="load"); wait_state(pg, "failed", 15000); pg.wait_for_timeout(500)
    check("помилка завантаження 3D chunk: стан failed, CSS-віяло видиме, hero незмінний", scene(pg) == "failed" and rect(pg, "section")[3] == base["hero"][3] and pg.evaluate("getComputedStyle(document.querySelector('[data-index=\"0\"] > span:first-child')).visibility") == "visible")
    css_click(pg, 1)
    check("помилка chunk: сайт і вибір карток працюють", cap(pg) == TITLES[1])
    check("помилка chunk: немає необроблених помилок сторінки", not [e for e in pg.errors if e.startswith("pageerror")], str(pg.errors[:2]))
    ctx.close()
    # втрата контексту
    ctx, pg = new_page(b); pg.goto(BASE, wait_until="load"); wait_state(pg, "webgl", 20000); pg.wait_for_timeout(500)
    pg.evaluate("(()=>{const c=document.querySelector('[data-scene-layer] canvas'); const gl=c.getContext('webgl2'); gl.getExtension('WEBGL_lose_context').loseContext()})()")
    wait_state(pg, "failed", 8000); pg.wait_for_timeout(500)
    check("втрата WebGL-контексту: перехід на CSS-віяло (failed), canvas прибрано", scene(pg) == "failed" and pg.locator("canvas").count() == 0)
    check("втрата контексту: CSS-картки знову видимі, hero незмінний", pg.evaluate("getComputedStyle(document.querySelector('[data-index=\"0\"] > span:first-child')).visibility") == "visible" and rect(pg, "section")[3] == base["hero"][3])
    pg.screenshot(path=f"{SHOTS}/fallback-contextlost-1440-hero.png")
    check("втрата контексту: вибір карток працює", (css_click(pg, 3), cap(pg) == TITLES[3])[1])
    ctx.close()

    # ================= E. МОБІЛЬНИЙ І ПЛАНШЕТНИЙ РЕЖИМИ =================
    print("\n=== E. mobile/tablet ===")
    ctx, pg = new_page(b, 390, 844, device_scale_factor=2, is_mobile=True, has_touch=True)
    pg.goto(BASE, wait_until="load"); pg.wait_for_timeout(2500)
    check("mobile 390: 3D-модуль не вантажиться, canvas немає, стан css", scene(pg) == "css" and not any(r.startswith("FanScene") for r in pg.reqs) and pg.locator("canvas").count() == 0)
    st = pg.evaluate("(()=>{const s=document.querySelector('[role=group]'); return [getComputedStyle(s).overflowX, getComputedStyle(s).scrollSnapType, s.scrollWidth>s.clientWidth]})()")
    check("mobile 390: нативна горизонтальна стрічка scroll-snap", st[0] == "auto" and "mandatory" in st[1] and st[2], str(st))
    check("mobile 390: overflow сторінки відсутній", not pg.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth"))
    check("mobile 390: touch-scroll не перехоплено (touchmove-слухачів немає у сцені: canvas відсутній)", pg.evaluate("document.querySelectorAll('canvas').length") == 0)
    ensure_images_loaded(pg); pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(300)
    pg.screenshot(path=f"{SHOTS}/mobile-390-hero.png"); ctx.close()
    ctx, pg = new_page(b, 1024, 768)    # планшетна композиція з мишею: 3D лишається вимкненим
    pg.goto(BASE, wait_until="load"); pg.wait_for_timeout(2500)
    check("планшет 1024 (миша): 3D-модуль не вантажиться, CSS-стрічка", scene(pg) == "css" and not any(r.startswith("FanScene") for r in pg.reqs))
    ctx.close()
    ctx, pg = new_page(b, 1440, 900, has_touch=True, is_mobile=False)
    ctx.close()
    b.close()

print(f"\nПідсумок: {sum(results)}/{len(results)} PASS")
sys.exit(0 if all(results) else 1)
