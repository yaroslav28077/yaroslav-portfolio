"""Генерує favicon (SVG/ICO/apple-touch) і локальне social preview (OG-зображення 1200×630) у app/public.

  python3 tools/make_brand_assets.py

Шрифти — ті самі, що на сайті (app/src/assets/fonts). Усі тексти OG-зображення взято з сайту
(заголовок hero, ім'я, роль); нічого нового не вигадується. Результат детермінований, ассети
закомічені в app/public, цей скрипт потрібен лише щоб перегенерувати їх.
"""
import os, sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "app", "public"); FONTS = os.path.join(ROOT, "app", "src", "assets", "fonts")
os.makedirs(PUB, exist_ok=True)
FOREST, PIST, TANG, WHITE = "#0F4127", "#D8EBB5", "#FF8A2B", "#FFFFFF"

# ---- Гліф «Я» шрифтом Unbounded 800 → контур SVG (не залежить від шрифтів системи) ----
f = TTFont(os.path.join(FONTS, "unbounded-cyrillic-800.woff2"))
gs = f.getGlyphSet(); name = f.getBestCmap()[ord("Я")]; upm = f["head"].unitsPerEm
from fontTools.pens.boundsPen import BoundsPen
bp = BoundsPen(gs); gs[name].draw(bp); x0, y0, x1, y1 = bp.bounds
def glyph_path(box, size):
    """контур, вписаний у квадрат box (px) по центру, висота гліфа = size"""
    k = size / (y1 - y0); w = (x1 - x0) * k
    ox = (box - w) / 2 - x0 * k; oy = (box + size) / 2 + y0 * k
    pen = SVGPathPen(gs); gs[name].draw(TransformPen(pen, (k, 0, 0, -k, ox, oy)))
    return pen.getCommands()

def icon_svg(rx):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="{rx}" fill="{FOREST}"/>'
            f'<path d="{glyph_path(64, 30)}" fill="{PIST}"/></svg>')

open(os.path.join(PUB, "favicon.svg"), "w").write(icon_svg(14))
full_bleed = icon_svg(0)

OG_HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:U;font-weight:800;src:url('file://{FONTS}/unbounded-cyrillic-800.woff2')}}
@font-face{{font-family:U;font-weight:800;unicode-range:U+0000-00FF;src:url('file://{FONTS}/unbounded-latin-800.woff2')}}
@font-face{{font-family:C;font-weight:600;src:url('file://{FONTS}/commissioner-cyrillic-600.woff2')}}
@font-face{{font-family:C;font-weight:600;unicode-range:U+0000-00FF;src:url('file://{FONTS}/commissioner-latin-600.woff2')}}
*{{box-sizing:border-box;margin:0}}
body{{width:1200px;height:630px;background:{PIST};color:{FOREST};font-family:C,sans-serif;position:relative;overflow:hidden}}
.copy{{position:absolute;left:72px;top:72px;width:660px}}
.who{{display:inline-block;background:{FOREST};color:{PIST};font:600 28px/1 C;padding:14px 22px;border-radius:99px}}
h1{{font:800 66px/1.12 U;letter-spacing:-.035em;margin-top:44px}}
.sub{{font:600 32px/1.3 C;margin-top:34px}}
.fan{{position:absolute;left:0;top:0;width:1200px;height:630px}}
.c{{position:absolute;left:950px;top:150px;width:180px;height:420px;border:5px solid {FOREST};border-radius:24px;background:{WHITE};transform-origin:50% 160%}}
.c i{{display:block;height:56px;background:{FOREST};border-radius:22px 22px 0 0}}
.c b{{position:absolute;left:22px;right:22px;top:92px;height:14px;border-radius:7px;background:{PIST}}}
.c b+b{{top:122px;right:80px}}
.c.t{{background:{TANG}}}
</style></head><body>
<div class="copy"><span class="who">Ярослав · розробник сайтів</span><h1 id="h">Ваш сайт — від ідеї до запуску</h1><p class="sub" id="s">Створюю сайти під ключ — від дизайну до публікації та підтримки</p></div>
<div class="fan">
 <div class="c" style="transform:rotate(-18deg)"><i></i><b></b><b></b></div>
 <div class="c" style="transform:rotate(-6deg)"><i></i><b></b><b></b></div>
 <div class="c t" style="transform:rotate(6deg)"><i></i><b></b><b></b></div>
 <div class="c" style="transform:rotate(18deg)"><i></i><b></b><b></b></div>
</div></body></html>"""
og_path = "/home/user/work/og.html"; os.makedirs(os.path.dirname(og_path), exist_ok=True); open(og_path, "w").write(OG_HTML)

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    def render_svg(svg, size, out):
        pg = b.new_page(viewport={"width": size, "height": size}, device_scale_factor=1)
        pg.set_content(f'<body style="margin:0"><div style="width:{size}px;height:{size}px">{svg.replace("<svg ", f"<svg width=\'{size}\' height=\'{size}\' ")}</div></body>')
        pg.screenshot(path=out, omit_background=True); pg.close()
    tmp = "/home/user/work/_ico"; os.makedirs(tmp, exist_ok=True)
    render_svg(full_bleed, 180, os.path.join(PUB, "apple-touch-icon.png"))
    imgs = []
    for s in (16, 32, 48):
        o = f"{tmp}/{s}.png"; render_svg(icon_svg(14), s, o); imgs.append(Image.open(o).convert("RGBA"))
    imgs[-1].save(os.path.join(PUB, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)], append_images=imgs[:-1])
    # OG
    pg = b.new_page(viewport={"width": 1200, "height": 630}); pg.goto("file://" + og_path); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(400)
    fonts_ok = pg.evaluate("document.fonts.check('800 66px U') && document.fonts.check('600 28px C')")
    box = pg.evaluate("(()=>{const r=e=>{const b=document.querySelector(e).getBoundingClientRect();return [b.left,b.top,b.right,b.bottom]};return {h:r('#h'),s:r('#s')}})()")
    pg.screenshot(path="/home/user/work/og-full.png")
    # перевірка: текст і віяло карток не перетинаються (з запасом 16 px)
    import numpy as np, io
    from scipy.ndimage import binary_dilation
    def mask(sel_hide):
        pg.evaluate(f"document.querySelectorAll('{sel_hide}').forEach(e=>e.style.visibility='hidden')")
        a = np.asarray(Image.open(io.BytesIO(pg.screenshot())).convert("RGB")).astype(int)
        pg.evaluate(f"document.querySelectorAll('{sel_hide}').forEach(e=>e.style.visibility='')")
        return np.abs(a - np.array([216, 235, 181])).sum(2) > 30
    text_m = mask(".fan"); fan_m = mask(".copy")
    gap = (binary_dilation(text_m, iterations=16) & fan_m).sum()
    b.close()
    assert gap == 0, f"текст і картки на OG ближче 16px ({gap} px)"
assert fonts_ok, "шрифти для OG не завантажились"
assert box["s"][3] < 600 and box["h"][2] <= 740 and box["s"][2] <= 740, f"текст OG виходить за межі: {box}"
im = Image.open("/home/user/work/og-full.png").convert("RGB")
im.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(os.path.join(PUB, "og-image.png"), optimize=True)
print("OK", {k: os.path.getsize(os.path.join(PUB, k)) for k in sorted(os.listdir(PUB))}, box)
