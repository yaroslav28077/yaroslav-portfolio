# Фінальний QA-звіт: підготовка до Netlify (03.10.2026)

Сайт **не опубліковано**. Нижче — лише те, що реально виконано й виміряно в лабораторних умовах (Chromium з програмним WebGL SwiftShader, локальний сервер). Реальні браузери, пристрої та Netlify не перевірялись.

## Що зроблено
- **Netlify**: `netlify.toml` у корені (base `app`, command `npm run build`, publish `dist`, `NODE_VERSION=22`), `app/.nvmrc`, `engines` у `package.json`, `.gitignore` (корінь і `app/`), `app/.env.example`. SPA-перенаправлення не додано: маршрутів на стороні клієнта немає.
- **SEO** (`app/vite-seo.ts`, без нових залежностей): `lang="uk"`, title і description (з `index.html`), canonical, Open Graph, Twitter Card, JSON-LD (Person + WebSite з підтверджених даних: ім'я, посада, пошта, Telegram), `robots.txt`, `sitemap.xml`, favicon (SVG/ICO/apple-touch), локальне social preview `og-image.png` 1200×630. Адреси лише зі змінних середовища (SITE_URL, URL, DEPLOY_PRIME_URL, DEPLOY_URL, CONTEXT); без адреси збірка проходить із явними попередженнями `[seo]`.
- **Індексація**: production на Netlify — дозволена; deploy-preview, branch-deploy та збірка без адреси — `noindex` (meta, `robots.txt`, `X-Robots-Tag`). `ROBOTS_NOINDEX=true` примусово вимикає індексацію.
- **Заголовки**: `dist/_headers` (джерело `app/netlify-headers.txt`): nosniff, Referrer-Policy, X-Frame-Options DENY, Permissions-Policy; кеш `immutable` на рік для хешованих `/assets/*`, `must-revalidate` для HTML, доба для іконок і превʼю. Лежать у `dist`, тому діють і при деплої з Git, і при ручному завантаженні. **CSP не додано** (ризик для WebGL).
- **Виправлено за результатами UI-аудиту**: skip-link «Перейти до робіт» був невидимим при фокусі клавіатури → тепер з'являється; додано `touch-action: manipulation` для посилань і кнопок; піднято `chunkSizeWarningLimit` до 1000 KB (lazy 3D chunk 920 KB), щоб збірка не лишала зайвого попередження.
- 3D-сцену, дизайн і тексти не змінювали; погоджене обрізання краю віяла не чіпали.

## Результати перевірок
| Перевірка | Результат |
|---|---|
| `npm ci` з нуля (Node 22.23.3, npm 10.9.9) на чистій копії | 217 пакетів, lock-файл не змінився, `npm audit`: 0 вразливостей |
| `typecheck`, `lint`, production build | пройшли (Node 22.23.3 і 20.19.5) |
| Нові залежності | немає |
| Розмір (dist) | 1.9 MB; index JS 244.14 KB (gzip 76.45), CSS 17.88 KB (gzip 4.46), lazy 3D chunk 920.10 KB (gzip 244.98), index.html 3.64 KB |
| `tools/app_seo.py` | 112/112 PASS: 11 сценаріїв середовища (локально, SITE_URL, production, production+ROBOTS_NOINDEX, deploy-preview, branch-deploy, без адреси, некоректний SITE_URL) |
| `tools/app_headers.py` | 16/16 PASS: заголовки з `dist/_headers` на реальній збірці; WebGL-віяло запускається, консоль без помилок, усі запити 200/304; кожен файл `/assets/*` має хеш |
| `tools/app_ui_audit.py` | 26/26 PASS (1440 і 390 px): lang, один h1, лендмарки, імена кнопок/посилань, alt і розміри зображень, rel=noopener, фокус на всіх фокусованих елементах, skip-link |
| `tools/app_interactions.py` (CSS-віяло) | 60/60 PASS |
| `tools/app_webgl.py` (WebGL, fallback-и) | на чистій збірці 3 запуски з 4 — 65/65; один запуск — 64/65 («у спокої новий кадр», 124→125). Три наступні запуски поспіль 65/65, відтворити не вдалося; схоже на гонку таймінгу в програмному рендері, причину не з'ясовано |
| `tools/app_edges.py` (краї canvas) | 131/131 PASS |
| `tools/app_qa.py` (розкладка) | 0 проблем на всіх ширинах (після виключення прихованого skip-link із перевірки «малі елементи»; сам skip-link перевіряє app_ui_audit) |

### Lighthouse mobile
Умови: Lighthouse 12.8.2, HeadlessChrome 136 (Chromium з Playwright), стандартне мобільне емулювання (Moto G Power, simulated slow 4G, CPU ×4), `--only-categories=performance,accessibility,best-practices,seo`; production-подібна збірка (`CONTEXT=production`, `URL=http://127.0.0.1:4192`), локальний сервер із gzip і заголовками `_headers`; 5 запусків; сирі звіти — `docs/lighthouse/mobile-run-*.json.gz`. Скрипт: `tools/app_lighthouse.py`.

| Запуск | Performance | Accessibility | Best Practices | SEO | FCP | LCP | TBT | CLS |
|---|---|---|---|---|---|---|---|---|
| 1 | 0.95 | 1.00 | 1.00 | 1.00 | 2110 ms | 2679 ms | 18 ms | 0.001 |
| 2 | 0.95 | 1.00 | 1.00 | 1.00 | 2106 ms | 2601 ms | 20 ms | 0.001 |
| 3 | 0.88 | 1.00 | 1.00 | 1.00 | 1656 ms | 3759 ms | 36 ms | 0.001 |
| 4 | 0.92 | 1.00 | 1.00 | 1.00 | 1702 ms | 3261 ms | 20 ms | 0.001 |
| 5 | 0.95 | 1.00 | 1.00 | 1.00 | 2104 ms | 2596 ms | 16 ms | 0.001 |
| **медіана** | **0.95** | **1.00** | **1.00** | **1.00** | 2104 ms | 2679 ms | 20 ms | 0.001 |

Застереження: це лабораторні дані з локального loopback і симульованим дроселюванням, на мобільному режимі (CSS-віяло, 3D-сцена на телефоні не вмикається). Розкид Performance 0.88–0.95 зумовлений варіацією LCP. Lighthouse також позначав «forced reflow», «LCP discovery» та «network dependency tree» (insight-аудити з оцінкою 0, не впливають на підсумкову оцінку істотно); їх не виправляли. Продуктивність WebGL-режиму на комп'ютері Lighthouse не вимірював. Реальні показники на Netlify (CDN, brotli, HTTP/2) після публікації можуть відрізнятися.

### UI-аудит за Web Interface Guidelines
Правила з `vercel-labs/web-interface-guidelines` застосовано до коду і до зібраної сторінки. Виконано (див. таблицю): семантика, заголовки, кнопки/посилання, зображення (width/height, lazy), `prefers-reduced-motion`, явні `transition` без `all`, видимий `:focus-visible`, `rel=noopener`. Не застосовувалось, бо змінило б дизайн/тексти (рекомендація на майбутнє): `text-wrap: balance` на заголовках, `translate="no"` для бренд-назв, `-webkit-tap-highlight-color`, правила про Title Case/першу особу для копірайтингу (не підходять українським текстам, затвердженим власником). Форм на сайті немає.

## Відомі обмеження
- Погоджене власником крайове обрізання 3D-віяла справа в крайніх станах на ~1181–1280 px (`docs/r3f-report.md`).
- `netlify-dist.zip` зібрано без адреси сайту, тому він **noindex** і без canonical/og:image/sitemap (див. README, «Ручне завантаження»).
- Заголовки з `_headers` перевірено локальним сервером за правилами Netlify, на самому Netlify — ні.
- Safari/Firefox/реальні пристрої, Core Web Vitals з реальних користувачів — не перевірялись.

## Що перевірити після публікації
Повний перелік — `README.md`, розділ «Перевірки після першої публікації» (заголовки через `curl -I`, `robots.txt`/`sitemap.xml`, canonical, social preview в Telegram/Facebook/LinkedIn, Rich Results Test, PageSpeed Insights, браузери, власний домен і `SITE_URL`).
