"""Перевірка SEO-збірки: набір сценаріїв середовища (локально, Netlify production/preview/branch, SITE_URL, noindex).

  python3 tools/app_seo.py

Кожен сценарій збирає сайт у тимчасову теку (vite build --outDir) з потрібними змінними середовища.
Адреси у сценаріях — тестові заглушки (example.com / *.test), вони не потрапляють у справжню збірку.
"""
import json, os, re, shutil, subprocess, sys, tempfile
from html.parser import HTMLParser

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")
if not os.path.isdir(os.path.join(APP, "node_modules")): APP = "/home/user/work/app"
results = []
def check(n, ok, info=""): results.append(bool(ok)); print(("PASS " if ok else "FAIL ") + n + (f"  [{info}]" if info else ""))

class P(HTMLParser):
    def __init__(s): super().__init__(); s.meta = []; s.links = []; s.ld = []; s.lang = None; s.title = ""; s._t = False; s._ld = False
    def handle_starttag(s, t, a):
        a = dict(a)
        if t == "html": s.lang = a.get("lang")
        if t == "meta": s.meta.append(a)
        if t == "link": s.links.append(a)
        if t == "title": s._t = True
        if t == "script" and a.get("type") == "application/ld+json": s._ld = True
    def handle_endtag(s, t):
        if t == "title": s._t = False
        if t == "script": s._ld = False
    def handle_data(s, d):
        if s._t: s.title += d
        if s._ld: s.ld.append(d)

def build(env_extra):
    out = tempfile.mkdtemp(prefix="seo-")
    env = {k: v for k, v in os.environ.items() if k not in ("CONTEXT", "URL", "DEPLOY_URL", "DEPLOY_PRIME_URL", "SITE_URL", "ROBOTS_NOINDEX")}
    env.update(env_extra)
    r = subprocess.run(["npx", "vite", "build", "--outDir", out, "--emptyOutDir"], cwd=APP, env=env, capture_output=True, text=True)
    return out, r

def inspect(out):
    h = open(os.path.join(out, "index.html"), encoding="utf-8").read(); p = P(); p.feed(h)
    m = lambda **k: [x for x in p.meta if all(x.get(a) == b for a, b in k.items())]
    def content(**k):
        r = m(**k); return r[0].get("content") if r else None
    canon = [l["href"] for l in p.links if l.get("rel") == "canonical"]
    return p, h, content, canon

def rd(out, f):
    fp = os.path.join(out, f); return open(fp, encoding="utf-8").read() if os.path.exists(fp) else None

SCEN = {
 "local, без SITE_URL": ({}, dict(index=False, url=None)),
 "local, SITE_URL задано": ({"SITE_URL": "https://example.com"}, dict(index=True, url="https://example.com")),
 "local, SITE_URL зі слешем і шляхом-слешем": ({"SITE_URL": "https://example.com/"}, dict(index=True, url="https://example.com")),
 "production, лише Netlify URL": ({"CONTEXT": "production", "URL": "https://portfolio-test.netlify.app"}, dict(index=True, url="https://portfolio-test.netlify.app")),
 "production, SITE_URL має пріоритет": ({"CONTEXT": "production", "URL": "https://portfolio-test.netlify.app", "SITE_URL": "https://example.com"}, dict(index=True, url="https://example.com")),
 "production + ROBOTS_NOINDEX=true": ({"CONTEXT": "production", "URL": "https://portfolio-test.netlify.app", "ROBOTS_NOINDEX": "true"}, dict(index=False, url="https://portfolio-test.netlify.app")),
 "production, ROBOTS_NOINDEX порожній": ({"CONTEXT": "production", "URL": "https://portfolio-test.netlify.app", "ROBOTS_NOINDEX": ""}, dict(index=True, url="https://portfolio-test.netlify.app")),
 "deploy-preview (SITE_URL ігнорується)": ({"CONTEXT": "deploy-preview", "DEPLOY_PRIME_URL": "https://deploy-preview-3--portfolio-test.netlify.app", "DEPLOY_URL": "https://abc123--portfolio-test.netlify.app", "URL": "https://portfolio-test.netlify.app", "SITE_URL": "https://example.com"}, dict(index=False, url="https://deploy-preview-3--portfolio-test.netlify.app")),
 "branch-deploy": ({"CONTEXT": "branch-deploy", "DEPLOY_PRIME_URL": "https://dev--portfolio-test.netlify.app", "URL": "https://portfolio-test.netlify.app"}, dict(index=False, url="https://dev--portfolio-test.netlify.app")),
 "production без жодної адреси": ({"CONTEXT": "production"}, dict(index=True, url=None)),
 "некоректний SITE_URL (local)": ({"SITE_URL": "not a url"}, dict(index=False, url=None)),
}
TITLE = None
for name, (env, exp) in SCEN.items():
    out, r = build(env)
    try:
        check(f"[{name}] збірка проходить", r.returncode == 0, (r.stderr or r.stdout)[-200:] if r.returncode else "")
        if r.returncode: continue
        p, h, content, canon = inspect(out); url = exp["url"]
        TITLE = TITLE or p.title.strip()
        check(f"[{name}] lang=uk, title, description", p.lang == "uk" and p.title.strip() == TITLE and len(content(name="description") or "") > 50)
        robots_meta = content(name="robots"); robots_txt = rd(out, "robots.txt"); sm = rd(out, "sitemap.xml"); hdr = rd(out, "_headers"); hdr = "\n".join(l for l in hdr.splitlines() if not l.lstrip().startswith("#")) if hdr else hdr
        if exp["index"]:
            check(f"[{name}] НЕМАЄ noindex (meta, robots.txt, X-Robots-Tag у _headers)", robots_meta is None and "Disallow: /\n" not in robots_txt and hdr is not None and "X-Robots-Tag" not in hdr, f"meta={robots_meta}")
            check(f"[{name}] robots.txt дозволяє індексацію", robots_txt.startswith("User-agent: *\nAllow: /"), robots_txt.replace("\n", " | "))
        else:
            check(f"[{name}] noindex у meta, robots.txt і _headers", robots_meta == "noindex, nofollow" and "Disallow: /" in robots_txt and hdr and "X-Robots-Tag: noindex, nofollow" in hdr)
            check(f"[{name}] без canonical і sitemap", not canon and sm is None)
        if url and exp["index"]:
            check(f"[{name}] canonical, og:url", canon == [url + "/"] and content(property="og:url") == url + "/", str(canon))
            check(f"[{name}] sitemap.xml і Sitemap у robots.txt", sm and f"<loc>{url}/</loc>" in sm and f"Sitemap: {url}/sitemap.xml" in robots_txt)
        if url:
            check(f"[{name}] абсолютні og:image / twitter:image", content(property="og:image") == url + "/og-image.png" and content(name="twitter:image") == url + "/og-image.png")
        else:
            check(f"[{name}] без адреси: немає canonical/og:url/og:image/sitemap", not canon and content(property="og:url") is None and content(property="og:image") is None and content(name="twitter:image") is None and sm is None)
            if exp["index"]: check(f"[{name}] без адреси robots.txt без рядка Sitemap", "Sitemap" not in robots_txt)
        check(f"[{name}] _headers містить безпекові й кеш-правила", hdr and all(x in hdr for x in ("X-Content-Type-Options: nosniff", "/assets/*", "immutable", "X-Frame-Options")))
        check(f"[{name}] OG/Twitter: title, description, type, locale, card", all([content(property="og:title") == p.title.strip(), content(property="og:description") == content(name="description"), content(property="og:type") == "website", content(property="og:locale") == "uk_UA", content(name="twitter:card") == "summary_large_image", content(name="twitter:title") == p.title.strip()]))
        try:
            ld = json.loads("".join(p.ld)); g = {x["@type"]: x for x in ld["@graph"]}
            ok_ld = g["Person"]["email"] == "yaroslav28077@gmail.com" and g["Person"]["sameAs"] == ["https://t.me/prosto0728"] and g["WebSite"]["inLanguage"] == "uk"
            ok_ld &= (g["WebSite"].get("url") == url + "/") if url else ("url" not in g["WebSite"] and "url" not in g["Person"])
            check(f"[{name}] JSON-LD валідний, лише підтверджені дані", ok_ld, json.dumps(ld, ensure_ascii=False)[:160])
        except Exception as e:
            check(f"[{name}] JSON-LD валідний", False, repr(e))
        local = [l["href"] for l in p.links if l.get("rel") in ("icon", "apple-touch-icon")]
        check(f"[{name}] favicon / apple-touch-icon існують у dist", len(local) == 3 and all(os.path.exists(os.path.join(out, l.lstrip("./"))) for l in local), str(local))
    finally:
        shutil.rmtree(out, ignore_errors=True)
# попередження про незавершені налаштування мають бути в логу
out, r = build({"CONTEXT": "production"}); log = r.stdout + r.stderr; shutil.rmtree(out, ignore_errors=True)
check("production без адреси: у логу є попередження про SITE_URL", "[seo]" in log and "SITE_URL" in log)
out, r = build({"SITE_URL": "not a url"}); log = r.stdout + r.stderr; shutil.rmtree(out, ignore_errors=True)
check("некоректний SITE_URL: у логу попередження, збірка не падає", r.returncode == 0 and "некоректна адреса" in log)
print(f"\nПідсумок: {sum(results)}/{len(results)} PASS"); sys.exit(0 if all(results) else 1)
