"""Lighthouse (mobile, стандартні налаштування) для production-подібної збірки на локальному сервері.

  python3 tools/app_lighthouse.py [кількість запусків=3]    # потрібен lighthouse (встановлюється поза проєктом)

Умови: збірка з CONTEXT=production і URL=http://127.0.0.1:4192 (canonical збігається з хостом), сервер віддає gzip та заголовки
з dist/_headers; Chromium headless з програмним WebGL (SwiftShader), стандартне мобільне емулювання Lighthouse (Moto G Power,
simulated slow 4G, CPU ×4). Це лабораторні дані на локальному loopback: не відображають реальну мережу, CDN Netlify (brotli, HTTP/2)
і реальні пристрої. Оцінки з реальних замірів ПІСЛЯ публікації можуть відрізнятися.
"""
import fnmatch, functools, gzip, http.server, json, mimetypes, os, shutil, socketserver, statistics, subprocess, sys, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); APP = os.path.join(ROOT, "app")
if not os.path.isdir(os.path.join(APP, "node_modules")): APP = "/home/user/work/app"
LH = os.environ.get("LIGHTHOUSE_BIN", "/home/user/work/lhtmp/node_modules/.bin/lighthouse")
CHROME = os.environ.get("CHROME_PATH", os.path.expanduser("~/.cache/ms-playwright/chromium-1169/chrome-linux/chrome"))
OUT = "/home/user/work/lh-dist"; PORT = 4192; N = int(sys.argv[1]) if len(sys.argv) > 1 else 3
env = {**os.environ, "CONTEXT": "production", "URL": f"http://127.0.0.1:{PORT}"}; env.pop("SITE_URL", None)
subprocess.run(["npx", "vite", "build", "--outDir", OUT, "--emptyOutDir"], cwd=APP, env=env, check=True, capture_output=True)
def _parse(text):
    rules = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"): continue
        if line[0] not in " \t": rules.append({"for": line.strip(), "values": {}})
        else:
            k, _, v = line.strip().partition(":"); rules[-1]["values"][k.strip()] = v.strip()
    return rules
RULES = _parse(open(os.path.join(OUT, "_headers"), encoding="utf-8").read())
TEXT = (".html", ".js", ".css", ".svg", ".txt", ".xml", ".json")
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        p = self.path.split("?")[0]; p = "/index.html" if p == "/" else p; fp = os.path.join(OUT, p.lstrip("/"))
        if not os.path.isfile(fp): self.send_error(404); return
        data = open(fp, "rb").read(); ct = mimetypes.guess_type(fp)[0] or "application/octet-stream"
        gz = p.endswith(TEXT) and "gzip" in self.headers.get("Accept-Encoding", "")
        if gz: data = gzip.compress(data, 6)
        self.send_response(200); self.send_header("Content-Type", ct + ("; charset=utf-8" if ct.startswith("text") or ct.endswith(("javascript", "svg+xml")) else ""))
        if gz: self.send_header("Content-Encoding", "gzip")
        for r in RULES:
            if fnmatch.fnmatchcase(p, r["for"]):
                for k, v in r["values"].items(): self.send_header(k, v)
        self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
class S(socketserver.ThreadingTCPServer): allow_reuse_address = True; daemon_threads = True
threading.Thread(target=S(("127.0.0.1", PORT), H).serve_forever, daemon=True).start()
runs = []
for i in range(N):
    out = f"/home/user/work/lighthouse-{i + 1}.json"
    r = subprocess.run([LH, f"http://127.0.0.1:{PORT}/", "--output=json", f"--output-path={out}", "--only-categories=performance,accessibility,best-practices,seo",
                        '--chrome-flags=--headless=new --no-sandbox --disable-dev-shm-usage', "--quiet"], env={**os.environ, "CHROME_PATH": CHROME}, capture_output=True, text=True)
    if r.returncode: print("lighthouse помилка:", r.stderr[-400:]); sys.exit(1)
    j = json.load(open(out)); c = j["categories"]; a = j["audits"]
    runs.append({"perf": c["performance"]["score"], "a11y": c["accessibility"]["score"], "bp": c["best-practices"]["score"], "seo": c["seo"]["score"],
                 "fcp": a["first-contentful-paint"]["numericValue"], "lcp": a["largest-contentful-paint"]["numericValue"], "tbt": a["total-blocking-time"]["numericValue"],
                 "cls": a["cumulative-layout-shift"]["numericValue"], "si": a["speed-index"]["numericValue"], "ver": j["lighthouseVersion"], "ua": j["environment"]["hostUserAgent"],
                 "fails": {k: v["score"] for k, v in a.items() if v.get("score") is not None and v["score"] < 0.9 and v.get("scoreDisplayMode") in ("binary", "numeric")}})
    print(f"запуск {i + 1}: perf={runs[-1]['perf']} a11y={runs[-1]['a11y']} bp={runs[-1]['bp']} seo={runs[-1]['seo']}  FCP={runs[-1]['fcp']:.0f}ms LCP={runs[-1]['lcp']:.0f}ms TBT={runs[-1]['tbt']:.0f}ms CLS={runs[-1]['cls']:.3f} SI={runs[-1]['si']:.0f}ms")
    print("   аудити < 0.9:", json.dumps(runs[-1]["fails"], ensure_ascii=False))
med = lambda k: statistics.median(r[k] for r in runs)
print(f"\nМедіана з {N}: perf={med('perf')} a11y={med('a11y')} bp={med('bp')} seo={med('seo')} FCP={med('fcp'):.0f} LCP={med('lcp'):.0f} TBT={med('tbt'):.0f} CLS={med('cls'):.3f} SI={med('si'):.0f}")
print("Lighthouse", runs[0]["ver"], "|", runs[0]["ua"])
