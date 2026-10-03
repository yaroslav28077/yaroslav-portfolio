"""Спільні утиліти Playwright для скриншотів і перевірок.

Чому потрібна ensure_images_loaded:
  Зображення з loading="lazy" нижче за перший екран Chromium завантажує лише коли вони наближаються
  до viewport. Скриншот full_page без прокрутки їх не "будить", тому блоки прев'ю в нижніх секціях
  виходили порожніми (у мобільних скриншотах це були ЦПРПП і тренажер). Lazy loading у самому сайті
  лишається ввімкненим; перед зйомкою ми проходимо сторінку прокруткою й чекаємо decode усіх зображень.
"""
from __future__ import annotations


def ensure_images_loaded(page, step: int = 500, timeout: int = 20000, rendered_only: bool = False) -> dict:
    """Прокручує сторінку, чекає завантаження ВСІХ img, повертає до верху. Кидає AssertionError, якщо щось не завантажилось."""
    height = page.evaluate("document.documentElement.scrollHeight")
    y = 0
    while y < height:
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(140)
        y += step
        height = page.evaluate("document.documentElement.scrollHeight")
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    # rendered_only=True: ігнорувати зображення, яких немає в розкладці (наприклад, у згорнутих <details>)
    cond = "i.getClientRects().length === 0 || (i.complete && i.naturalWidth > 0)" if rendered_only else "i.complete && i.naturalWidth > 0"
    page.wait_for_function(f"[...document.images].every(i => {cond})", timeout=timeout)
    page.evaluate("Promise.all([...document.images].map(i => i.decode ? i.decode().catch(() => null) : null))")
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(250)
    report = page.evaluate(
        """() => { const imgs = [...document.images];
          return { total: imgs.length, lazy: imgs.filter(i => i.loading === 'lazy').length,
                   notLoaded: imgs.filter(i => !(i.complete && i.naturalWidth > 0)).map(i => i.currentSrc || i.src) } }"""
    )
    if not rendered_only:
        assert not report["notLoaded"], f"Не завантажено зображень: {report['notLoaded']}"
    return report


def lazy_state(page) -> list[str]:
    """Які img ще не завантажені просто зараз (для демонстрації проблеми до прокрутки)."""
    return page.evaluate(
        "[...document.images].filter(i => !(i.complete && i.naturalWidth > 0)).map(i => (i.getAttribute('src')||'').split('/').pop())"
    )
