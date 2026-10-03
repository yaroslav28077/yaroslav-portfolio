"""Перевірка заголовків із dist/_headers (джерело — app/netlify-headers.txt) на реальній збірці: локальний сервер віддає dist із заголовками з [[headers]]
(правила _headers із dist: «*» — будь-який суфікс, значення зливаються), у Chromium завантажується сайт зі справжнім WebGL.

  python3 tools/app_headers.py [шлях/до/dist]

Це перевірка КОНФІГУРАЦІЇ та сумісності заголовків із сайтом. Те, що Netlify справді віддає ці заголовки, треба перевірити
після першої публікації (див. README, «Перевірки після першої публікації»).
"""
import fnmatch, functools, http.server, mimetypes, os, re, socketserver, sys, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = sys.argv[1] if len(sys.argv) > 1 else "/home/user/work/app/dist"
def parse_headers(text):
    """формат Netlify _headers: рядок із шляхом, далі відступні «Назва: значення»; # — коментар"""
    rules = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"): continue
        if line[0] not in " \t": rules.append({"for": line.strip(), "values": {}})
        else:
            k, _, v = line.strip().partition(":"); rules[-1]["values"][k.strip()] = v.strip()
    return rules
RULES = parse_headers(open(os.path.join(DIST, "_headers"), encoding="utf-8").read())
results = []
def check(n, ok, info=""): results.append(bool(ok)); print(("PASS " if ok else "FAIL ") + n + (f"  [{info}]" if info else ""))

def headers_for(path):
    out = {}
    for r in RULES:
        if fnmatch.fnmatchcase(path, r["for"]): out.update({k.lower(): v for k, v in r["values"].items()})
    return out

class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def end_headers(self):
        p = self.path.split("?")[0]; p = "/index.html" if p == "/" else p
        for k, v in headers_for(p).items(): self.send_header(k, v)
        super().end_headers()
class S(socketserver.ThreadingTCPServer): allow_reuse_address = True; daemon_threads = True
srv = S(("127.0.0.1", 4190), functools.partial(H, directory=DIST)); threading.Thread(target=srv.serve_forever, daemon=True).start()

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True); ctx = b.new_context(viewport={"width": 1440, "height": 900}, locale="uk-UA"); pg = ctx.new_page()
    resp = []; errs = []
    pg.on("response", lambda r: resp.append(r)); pg.on("pageerror", lambda e: errs.append(str(e)[:150]))
    pg.on("console", lambda m: errs.append(m.text[:150]) if m.type == "error" else None)
    pg.goto("http://127.0.0.1:4190/?scene-debug"); pg.wait_for_function("document.querySelector('[data-scene]')?.dataset.scene==='webgl'", timeout=40000); pg.wait_for_timeout(1000)
    check("з усіма заголовками сайт запускає WebGL-віяло", pg.get_attribute("[data-scene]", "data-scene") == "webgl")
    pg.evaluate("window.scrollTo(0, document.body.scrollHeight)"); pg.wait_for_timeout(1200)
    check("без помилок у консолі та pageerror", not errs, str(errs))
    bad = [(r.url, r.status) for r in resp if r.status >= 400]; check("усі запити 200/304", not bad, str(bad))
    doc = next(r for r in resp if r.url.split("?")[0].endswith("/"))
    h = doc.headers
    check("документ: X-Content-Type-Options, Referrer-Policy, X-Frame-Options, Permissions-Policy",
          h.get("x-content-type-options") == "nosniff" and h.get("referrer-policy") == "strict-origin-when-cross-origin" and h.get("x-frame-options") == "DENY" and "camera=()" in h.get("permissions-policy", ""))
    check("документ (/): Cache-Control «max-age=0, must-revalidate»", "max-age=0" in h.get("cache-control", "") and "must-revalidate" in h.get("cache-control", ""), h.get("cache-control", "—"))
    check("CSP відсутня (свідомо)", "content-security-policy" not in h)
    check("X-Robots-Tag є лише у неіндексованих збірках (тут: " + ("noindex-збірка" if "x-robots-tag" in h else "індексована збірка") + ")", ("x-robots-tag" in h) == ("X-Robots-Tag" in "".join(l for l in open(os.path.join(DIST, "_headers")) if not l.lstrip().startswith("#"))))
    assets = [r for r in resp if "/assets/" in r.url]
    check("є хешовані ресурси в /assets/ (js, css, шрифти, зображення)", len(assets) >= 8, f"{len(assets)} шт.")
    check("усі /assets/* із Cache-Control immutable на рік", all("max-age=31536000" in r.headers.get("cache-control", "") and "immutable" in r.headers.get("cache-control", "") for r in assets))
    check("кожен ресурс /assets/ має хеш в імені", all(re.search(r"-[A-Za-z0-9_-]{8}\.[a-z0-9]+$", r.url) for r in assets), str([r.url.split('/')[-1] for r in assets if not re.search(r"-[A-Za-z0-9_-]{8}\.[a-z0-9]+$", r.url)]))
    b.close()
# покриття: кожен файл dist, що не лежить в assets/, не має «вічного» кешу, а hash-файли мають
files = [os.path.relpath(os.path.join(d, f), DIST) for d, _, fs in os.walk(DIST) for f in fs]
immut = [f for f in files if "immutable" in headers_for("/" + f).get("cache-control", "")]
check("immutable застосовано лише до файлів у assets/", all(f.startswith("assets/") for f in immut) and any(f.startswith("assets/") for f in immut))
check("усі файли assets/ мають хеш (безпечно кешувати вічно)", all(re.search(r"-[A-Za-z0-9_-]{8}\.[a-z0-9]+$", f) for f in files if f.startswith("assets/")))
for f in ("favicon.svg", "favicon.ico", "apple-touch-icon.png", "og-image.png"):
    check(f"{f}: кеш не «вічний»", "immutable" not in headers_for("/" + f).get("cache-control", "") and "max-age=86400" in headers_for("/" + f).get("cache-control", ""))
print(f"\nПідсумок: {sum(results)}/{len(results)} PASS"); sys.exit(0 if all(results) else 1)
