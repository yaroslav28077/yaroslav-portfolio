"""UI-аудит зібраного сайту за Web Interface Guidelines (машинна частина): семантика, доступність, зображення, фокус, viewport.

  python3 tools/app_ui_audit.py [шлях/до/dist]

Перевіряє те, що можна виміряти в браузері (1440 px з WebGL і 390 px). Огляд тексту, візуальних деталей і копірайтингу — окремо, вручну.
"""
import functools, http.server, os, socketserver, sys, threading
DIST = sys.argv[1] if len(sys.argv) > 1 else "/home/user/work/app/dist"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
from pwutil import ensure_images_loaded
results = []
def check(n, ok, info=""): results.append(bool(ok)); print(("PASS " if ok else "FAIL ") + n + (f"  [{info}]" if info else ""))
h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DIST); h.func.log_message = lambda *a, **k: None
class S(socketserver.TCPServer): allow_reuse_address = True
threading.Thread(target=S(("127.0.0.1", 4191), h).serve_forever, daemon=True).start()
URL = "http://127.0.0.1:4191/index.html"

AUDIT = """()=>{
 const q=s=>[...document.querySelectorAll(s)], name=e=>(e.getAttribute('aria-label')||e.getAttribute('aria-labelledby')&&document.getElementById(e.getAttribute('aria-labelledby'))?.textContent||e.textContent||e.getAttribute('title')||'').trim();
 const hs=q('h1,h2,h3,h4,h5,h6').map(e=>+e.tagName[1]); let jumps=[]; hs.forEach((v,i)=>{ if(i&&v>hs[i-1]+1) jumps.push([hs[i-1],v]) });
 const vp=document.querySelector('meta[name=viewport]')?.content||'';
 return {
  lang:document.documentElement.lang, h1:q('h1').length, jumps, main:q('main').length, header:q('header').length, footer:q('footer').length,
  vpOk:!/user-scalable\\s*=\\s*(no|0)|maximum-scale\\s*=\\s*1(\\.0)?\\b/.test(vp), vp,
  noName:[...q('a'),...q('button')].filter(e=>!name(e)).map(e=>e.outerHTML.slice(0,90)),
  imgNoAlt:q('img').filter(e=>!e.hasAttribute('alt')).length, imgNoDim:q('img').filter(e=>!(e.getAttribute('width')&&e.getAttribute('height'))).map(e=>e.src.split('/').pop()),
  blankNoRel:q('a[target=_blank]').filter(e=>!/noopener/.test(e.rel)).length,
  divClick:q('div[onclick],span[onclick]').length,
  inputs:q('input,select,textarea').length, dupIds:(()=>{const s={},d=[];q('[id]').forEach(e=>{ if(s[e.id]) d.push(e.id); s[e.id]=1});return d})(),
  anchorsBroken:q('a[href^="#"]').filter(a=>a.getAttribute('href').length>1&&!document.getElementById(a.getAttribute('href').slice(1))).map(a=>a.getAttribute('href')),
  badEllipsis:q('main *').filter(e=>e.children.length===0&&/\\.\\.\\./.test(e.textContent)).length,
  themeColor:document.querySelector('meta[name=theme-color]')?.content,
 }}"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    for label, vp in (("1440", {"width": 1440, "height": 900}), ("390", {"width": 390, "height": 844})):
        ctx = b.new_context(viewport=vp, locale="uk-UA", has_touch=label == "390", is_mobile=label == "390"); pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:120])); pg.on("console", lambda m: errs.append(m.text[:120]) if m.type == "error" else None)
        pg.goto(URL); pg.wait_for_selector("h1"); ensure_images_loaded(pg, rendered_only=True)
        a = pg.evaluate(AUDIT)
        check(f"[{label}] html lang=uk", a["lang"] == "uk")
        check(f"[{label}] один h1, без пропусків рівнів заголовків", a["h1"] == 1 and not a["jumps"], str(a["jumps"]))
        check(f"[{label}] лендмарки header/main/footer", a["main"] == 1 and a["header"] >= 1 and a["footer"] >= 1)
        check(f"[{label}] viewport не блокує масштабування", a["vpOk"], a["vp"])
        check(f"[{label}] кожне посилання/кнопка має доступне ім'я", not a["noName"], str(a["noName"]))
        check(f"[{label}] зображення: alt + width/height", a["imgNoAlt"] == 0 and not a["imgNoDim"], str(a["imgNoDim"]))
        check(f"[{label}] target=_blank має rel=noopener", a["blankNoRel"] == 0)
        check(f"[{label}] немає div/span з onclick; немає форм без міток", a["divClick"] == 0 and a["inputs"] == 0)
        check(f"[{label}] немає дубльованих id і битих якорів", not a["dupIds"] and not a["anchorsBroken"], f"{a['dupIds']} {a['anchorsBroken']}")
        check(f"[{label}] «...» замість «…» немає", a["badEllipsis"] == 0)
        # клавіатура: skip-link першим, видимий при фокусі; у всіх фокусованих елементів видимий контур
        pg.evaluate("document.activeElement.blur(); window.scrollTo(0,0)")
        pg.keyboard.press("Tab")
        sk = pg.evaluate("(()=>{const e=document.activeElement;const r=e.getBoundingClientRect();const cs=getComputedStyle(e);return {txt:e.textContent.trim(),w:r.width,h:r.height,inView:r.top>=0&&r.left>=0&&r.bottom<=innerHeight,cls:e.className}})()")
        check(f"[{label}] перший Tab → skip-link, видимий і в межах екрана", "Перейти" in sk["txt"] and sk["w"] > 60 and sk["h"] > 20 and sk["inView"], str(sk))
        pg.evaluate("document.activeElement.blur()"); pg.evaluate("window.scrollTo(0,0)")
        bad = []; seen = 0
        for _ in range(40):
            pg.keyboard.press("Tab"); pg.wait_for_timeout(30)
            r = pg.evaluate("""()=>{const e=document.activeElement; if(!e||e===document.body) return null; const cs=getComputedStyle(e); const bs=cs.boxShadow;
               return {t:(e.getAttribute('aria-label')||e.textContent).trim().slice(0,28), ol:cs.outlineStyle!=='none'&&parseFloat(cs.outlineWidth)>=2, shadow:bs&&bs!=='none', vis:cs.visibility!=='hidden'}}""")
            if r is None: break
            seen += 1
            if not (r["ol"] or r["shadow"]): bad.append(r["t"])
        check(f"[{label}] видимий індикатор фокуса на {seen} фокусованих елементах", seen > 8 and not bad, str(bad))
        check(f"[{label}] без помилок консолі", not errs, str(errs))
        ctx.close()
    b.close()
print(f"\nПідсумок: {sum(results)}/{len(results)} PASS"); sys.exit(0 if all(results) else 1)
