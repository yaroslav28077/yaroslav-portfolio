"""Перевірка взаємодій React-застосунку (dist). Сервер має бути запущений app_qa.py або окремо на :4173.
  python3 tools/app_interactions.py
Кожна перевірка друкує PASS/FAIL.
"""
import functools, http.server, os, socketserver, sys, threading
sys.path.insert(0, os.path.dirname(__file__))
from playwright.sync_api import sync_playwright

DIST = "/home/user/work/app/dist"; PORT = 4173
URL = f"http://127.0.0.1:{PORT}/index.html?scene=off"   # CSS-віяло: регресійні тести
results = []

def check(name, ok, info=""):
    results.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name + (f"  [{info}]" if info else ""))

try:
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DIST); h.func.log_message = lambda *a, **k: None
    class S(socketserver.TCPServer): allow_reuse_address = True
    threading.Thread(target=S(("127.0.0.1", PORT), h).serve_forever, daemon=True).start()
except OSError:
    pass

def rect(pg, css):
    return pg.evaluate("s=>{const e=document.querySelector(s); if(!e) return null; const r=e.getBoundingClientRect(); return [r.left,r.top,r.right,r.bottom]}", css)


def visible_point(pg, i):
    """Точка, де курсор справді потрапляє на картку i (перевірка elementFromPoint по сітці її bbox)."""
    return pg.evaluate("""(i) => { const c = document.querySelector('[data-index="'+i+'"]'); const r = c.getBoundingClientRect();
      for (let fy = .06; fy < .95; fy += .05) for (let fx = .04; fx < .98; fx += .04) {
        const x = r.left + r.width * fx, y = r.top + r.height * fy;
        const el = document.elementFromPoint(x, y); const h = el && el.closest('[data-index]');
        if (h && h.dataset.index == String(i) && y < innerHeight) return [x, y]; }
      return null; }""", i)

def click_card(pg, i):
    pt = visible_point(pg, i)
    check(f"картка {i+1}: є видима клікабельна область", pt is not None, str(pt and [round(v) for v in pt]))
    pg.mouse.click(*pt)

def cap_title(pg): return pg.inner_text('[class*="captionName"]')
def pressed(pg): return pg.evaluate("[...document.querySelectorAll('[data-index]')].map(b=>b.getAttribute('aria-pressed'))")

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)

    # ---------- ДЕСКТОП 1440 ----------
    ctx = b.new_context(viewport={"width": 1440, "height": 900}); pg = ctx.new_page()
    errs = []; pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None); pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="load"); pg.wait_for_timeout(800)
    check("H1 = «Ваш сайт — від ідеї до запуску»", pg.inner_text("h1").strip() == "Ваш сайт — від ідеї до запуску", pg.inner_text("h1"))
    check("початково вибрана перша робота", cap_title(pg) == "Українська класична гімназія" and pressed(pg)[0] == "true")
    lead = pg.inner_text('[class*="lead"]')
    check("опис hero — скорочений, за ТЗ", lead.strip() == "Я Ярослав. Створюю сайти під ключ — від дизайну до публікації та підтримки.", lead)
    body = pg.inner_text("body")
    for bad in ["підтверджений", "Авторство", "а не межа", "не межа", "Хостинг безкоштовний або платний, залежно"]:
        if bad == "Хостинг безкоштовний або платний, залежно":
            check("хостинг пояснено один раз (у послугах)", body.count("Хостинг безкоштовний або платний") == 1 and pg.inner_text("#services").count("Хостинг безкоштовний або платний") == 1, str(body.count("Хостинг")))
        else:
            check(f"немає службової фрази «{bad}»", bad not in body)
    check("«договірна» згадується один раз (у послугах)", body.count("договірна") == 1 and "договірна" in pg.inner_text("#services"), str(body.count("договірна")))
    check("у hero немає ціни/хостингу/досвіду", all(w not in pg.inner_text("section").split("Роботи, які")[0] for w in ["договірна", "Хостинг", "досвід"]))
    check("вступ до робіт — за ТЗ", "Сайти навчальних закладів і установ та навчальний PWA-застосунок. У кожному проєкті я відповідав за дизайн, розробку й публікацію" in pg.inner_text("#works"), pg.inner_text("#works")[:160])
    check("в кейсах коротка роль «Дизайн, розробка та запуск»", pg.locator("#works dd", has_text="Дизайн, розробка та запуск").count() == 4)
    check("PWA без вигаданих замовника/стеку", "Технологія" not in pg.locator("#works article").nth(3).inner_text() and "Замовник" not in pg.locator("#works article").nth(3).inner_text() and "Тренажер" in pg.locator("#works article").nth(3).inner_text())
    about = pg.inner_text("#about")
    check("«Про мене»: працюю особисто, створюю й оновлюю сайти, публікація й супровід", all(w in about for w in ["Працюю особисто", "створюю та оновлюю сайти", "публікацією й подальшим супроводом"]))
    check("оновлення старих сайтів лишилось у послугах", "Оновлення застарілого сайту" in pg.inner_text("#services"))
    for i, name in enumerate(["Українська класична гімназія", "Гімназія «Просвіт»", "ЦПРПП м. Лубни", "Тренажер з історії України"]):
        click_card(pg, i); pg.wait_for_timeout(700)
        cap = rect(pg, '[class*="caption_"], [class*="captionName"]')
        pg.wait_for_timeout(100)
        lx = pg.evaluate("(()=>{const l=document.querySelector('[class*=leader]'); const r=l.getBoundingClientRect(); return [r.left+r.width/2, r.top, r.bottom]})()")
        anc = pg.evaluate(f"(()=>{{const a=document.querySelector('[data-index=\"{i}\"] [class*=anchor]').getBoundingClientRect(); return [a.left+a.width/2, a.top]}})()")
        link = pg.get_attribute('[class*="captionLink"]', "href")
        check(f"картка {i+1}: підпис оновився, aria-pressed", cap_title(pg) == name and pressed(pg)[i] == "true" and pressed(pg).count("true") == 1, f"{cap_title(pg)} → {link}")
        check(f"картка {i+1}: виносна лінія торкається картки", abs(lx[0] - anc[0]) < 6 and abs(lx[2] - anc[1]) < 6 and lx[2] - lx[1] > 0, f"dx={lx[0]-anc[0]:.1f}, dy={lx[2]-anc[1]:.1f}, довжина={lx[2]-lx[1]:.0f}")

    # назви на картках не закриті сусідніми картками (перевірка elementFromPoint по рядках тексту)
    for width in (1440, 1300, 1200):
        pg.set_viewport_size({"width": width, "height": 900}); pg.wait_for_timeout(500)
        hidden = pg.evaluate("""() => { const res = [];
          document.querySelectorAll('[data-index]').forEach(card => { const i = card.dataset.index; const label = card.querySelector('[class*=cardTop]');
            const rg = document.createRange(); rg.selectNodeContents(label);
            for (const r of rg.getClientRects()) { for (const fx of [.02, .5, .98]) { const x = r.left + r.width * fx, y = r.top + r.height / 2;
              const el = document.elementFromPoint(x, y); const h = el && el.closest('[data-index]'); if (!h || h.dataset.index !== i) { res.push(card.innerText.trim().slice(0, 18) + ' @' + Math.round(x) + ',' + Math.round(y)); break; } } } });
          return res; }""")
        check(f"{width}px: назви на картках видно повністю (не під сусідніми)", not hidden, str(hidden))
    pg.set_viewport_size({"width": 1440, "height": 900}); pg.wait_for_timeout(300)
    # підпис не перекриває картки й текст
    cap = rect(pg, '[class*="captionName"]')
    check("підпис не перекриває заголовок/CTA ліворуч", rect(pg, "h1")[2] <= rect(pg, '[class*="captionLabel"]')[0] and True)
    # клавіатура
    pg.focus('[data-index="3"]'); pg.keyboard.press("ArrowRight")
    check("ArrowRight з останньої картки → перша", pg.evaluate("document.activeElement.dataset.index") == "0")
    pg.keyboard.press("End"); check("End → остання", pg.evaluate("document.activeElement.dataset.index") == "3")
    pg.keyboard.press("Enter"); pg.wait_for_timeout(300)
    check("Enter вибирає сфокусовану картку", cap_title(pg) == "Тренажер з історії України")
    # hover піднімає картку
    t0 = pg.evaluate("getComputedStyle(document.querySelector('[data-index=\"1\"]')).transform")
    pg.mouse.move(*visible_point(pg, 1)); pg.wait_for_timeout(450)
    t1 = pg.evaluate("getComputedStyle(document.querySelector('[data-index=\"1\"]')).transform")
    check("hover змінює положення картки (підйом)", t0 != t1)
    # CTA-якорі
    pg.click("text=Переглянути роботи"); pg.wait_for_timeout(900)
    check("«Переглянути роботи» веде до #works", pg.evaluate("location.hash") == "#works" and abs(rect(pg, "#works")[1]) < 40, pg.evaluate("location.hash"))
    pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(300)
    pg.click('section >> text=Обговорити проєкт'); pg.wait_for_timeout(900)
    check("«Обговорити проєкт» веде до #contacts", pg.evaluate("location.hash") == "#contacts")
    # контакти
    check("Telegram і email правильні", pg.get_attribute('a[href="https://t.me/prosto0728"]', "href") == "https://t.me/prosto0728" and pg.locator('a[href="mailto:yaroslav28077@gmail.com"]').count() >= 1)
    # зовнішні посилання безпечні
    ext = pg.evaluate("[...document.querySelectorAll('a[target=_blank]')].map(a=>a.rel)")
    check("усі зовнішні посилання з rel=noopener", all("noopener" in r for r in ext), f"{len(ext)} посилань")
    # усі 4 проєкти мають повні прев'ю у секції робіт
    cases = pg.evaluate("[...document.querySelectorAll('#works article')].map(a=>({t:a.querySelector('h3').innerText, imgs:[...a.querySelectorAll('img')].map(i=>[i.naturalWidth,i.complete]), btn:!!a.querySelector('a[href^=http]')}))")
    check("в секції робіт 4 кейси з двома зображеннями й кнопкою", len(cases) == 4 and all(len(c["imgs"]) == 2 and c["btn"] for c in cases), str([c["t"] for c in cases]))
    check("жодних помилок консолі (desktop)", not errs, str(errs))
    ctx.close()

    # ---------- ТЕЛЕФОН 390 ----------
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True); pg = ctx.new_page()
    errs = []; pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None); pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="load"); pg.wait_for_timeout(800)
    strip = pg.evaluate("(()=>{const s=document.querySelector('[role=group]'); return {sw:s.scrollWidth, cw:s.clientWidth, ov:getComputedStyle(s).overflowX, snap:getComputedStyle(s).scrollSnapType}})()")
    check("стрічка карток нативно прокручується (overflow-x + scroll-snap)", strip["sw"] > strip["cw"] and strip["ov"] in ("auto", "scroll") and "mandatory" in strip["snap"], str(strip))
    check("сторінка не має горизонтального overflow", not pg.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth"))
    hint = pg.evaluate("(()=>{const e=document.querySelector('[class*=hint]'); const r=e.getBoundingClientRect(); return [e.innerText, r.width>0, r.bottom<=innerHeight+400]})()")
    check("підказка про гортання видима", hint[1], hint[0])
    cards = pg.evaluate("[...document.querySelectorAll('[data-index]')].map(c=>{const r=c.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.right)]})")
    check("друга картка визирає з-за краю (видно, що є ще)", cards[1][0] < 390 < cards[1][1], str(cards[:2]))
    dots0 = pg.evaluate("[...document.querySelectorAll('[class*=dot]')].map(d=>getComputedStyle(d).backgroundColor)")
    # прокрутка стрічки до кінця
    pg.evaluate("document.querySelector('[role=group]').scrollTo({left: 10000, behavior:'instant'})"); pg.wait_for_timeout(500)
    dots1 = pg.evaluate("[...document.querySelectorAll('[class*=dot]')].map(d=>getComputedStyle(d).backgroundColor)")
    check("індикатор точок змінюється при прокрутці", dots0 != dots1)
    last = pg.evaluate("(()=>{const c=document.querySelector('[data-index=\"3\"]').getBoundingClientRect(); return [c.left, c.right]})()")
    check("остання картка доступна в межах екрана після прокрутки", last[1] <= 392 and last[0] >= 0, str(last))
    pg.tap('[data-index="3"]'); pg.wait_for_timeout(400)
    check("тап по картці оновлює підпис (без hover)", cap_title(pg) == "Тренажер з історії" and pressed(pg)[3] == "true", cap_title(pg))
    pg.evaluate("document.querySelector('[role=group]').scrollTo({left: 0, behavior:'instant'})"); pg.wait_for_timeout(300)
    pg.tap('[data-index="1"]'); pg.wait_for_timeout(400)
    check("тап по другій картці → «Просвіт»", cap_title(pg) == "Гімназія «Просвіт»")
    cap = pg.evaluate("(()=>{const c=document.querySelector('[class*=_caption_]').getBoundingClientRect(); const l=document.querySelector('[class*=captionLink]').getBoundingClientRect(); return {ch:c.height, lw:l.width, lh:l.height, cw:c.width}})()")
    check("мобільний підпис компактний: висота ≤ 64, посилання ≤ 45% ширини, ціль ≥ 44", cap["ch"] <= 64 and cap["lw"] <= cap["cw"] * .45 and cap["lh"] >= 44, str(cap))
    check("мобільний підпис: лише коротка назва й «Відкрити»", pg.inner_text('[class*=captionLink]').strip() == "Відкрити" and pg.is_hidden('[class*=captionMeta]'))
    first_card_top = pg.evaluate("document.querySelector('[data-index=\"0\"]').getBoundingClientRect().top")
    check("картки з'являються раніше: верх карток у першому екрані з запасом (≥ 300 px видно)", first_card_top <= 844 - 300, str(round(first_card_top)))
    h1s = pg.evaluate("[parseFloat(getComputedStyle(document.querySelector('h1')).fontSize), parseFloat(getComputedStyle(document.querySelector('[class*=lead]')).fontSize)]")
    check("шрифти mobile hero не зменшені (h1 ≥ 30, опис ≥ 18)", h1s[0] >= 30 and h1s[1] >= 18, str(h1s))
    cap = rect(pg, '[class*="caption_"]') or rect(pg, '[class*=captionLabel]')
    # меню
    check("меню закрите спочатку", not pg.is_visible("#mobile-menu"))
    pg.tap('button:has-text("Меню")'); pg.wait_for_timeout(200)
    check("меню відкривається, aria-expanded=true", pg.is_visible("#mobile-menu") and pg.get_attribute('button[aria-controls="mobile-menu"]', "aria-expanded") == "true")
    pg.keyboard.press("Escape"); pg.wait_for_timeout(200)
    check("Escape закриває меню", not pg.is_visible("#mobile-menu"))
    pg.tap('button:has-text("Меню")'); pg.wait_for_timeout(150)
    pg.tap('#mobile-menu >> text=Послуги'); pg.wait_for_timeout(900)
    check("пункт меню веде до секції й закриває меню", pg.evaluate("location.hash") == "#services" and not pg.is_visible("#mobile-menu"))
    check("жодних помилок консолі (mobile)", not errs, str(errs))
    ctx.close()

    # ---------- reduced motion ----------
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce"); pg = ctx.new_page()
    pg.goto(URL, wait_until="load"); pg.wait_for_timeout(600)
    dur = pg.evaluate("getComputedStyle(document.querySelector('[data-index=\"1\"]')).transitionDuration")
    check("reduced motion: переходи вимкнено", dur.startswith("1e-05") or dur.startswith("0.00001") or dur == "0s", dur)
    check("reduced motion: немає активних анімацій", pg.evaluate("document.getAnimations().filter(a=>a.playState==='running').length") == 0)
    ctx.close()
    b.close()

print(f"\nПідсумок: {sum(results)}/{len(results)} PASS")
sys.exit(0 if all(results) else 1)
