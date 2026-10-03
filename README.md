# Портфоліо Ярослава

Односторінковий сайт-портфоліо: React 19, TypeScript (strict), Vite, CSS Modules. Віяло робіт на головному екрані на широких екранах
малює WebGL (three + React Three Fiber), на планшетах і телефонах та без WebGL — звичайний CSS-варіант.
Серверної частини, форм і аналітики немає; це статичні файли.

> **Статус:** сайт підготовлено до публікації на Netlify, але **не опубліковано**. Усі кроки публікації — нижче.

## Структура репозиторію

```
netlify.toml            налаштування Netlify (base = app, команда збірки, Node)
README.md               цей файл
app/                    сам сайт (package.json, lock-файл, код, public/)
  src/content/          увесь текст і дані: profile.ts, projects.ts
  netlify-headers.txt   заголовки безпеки й кешування → потрапляють у dist/_headers
  vite-seo.ts           SEO під час збірки (canonical, Open Graph, JSON-LD, robots.txt, sitemap.xml)
  .env.example          шаблон змінних середовища (SITE_URL тощо)
docs/                   бриф, дизайн-рішення, QA-звіти, прогрес
tools/                  скрипти перевірок (Playwright, Lighthouse) і генерації іконок
app-previews/           скриншоти для звітів
```

Дослідницькі матеріали (оригінальні скриншоти чужих сайтів `previews/`, прототипи концепцій `concepts/`, `shared/`) до цього архіву не входять: вони потрібні лише для історії рішень (`docs/`) і лежать у постійному сховищі проєкту.

Корінь Git-репозиторію — **тека, де лежить `netlify.toml`** (не `app/`). Якщо репозиторій створити з вмісту лише `app/`,
у Netlify вручну задайте Base directory порожнім, а `netlify.toml` перенесіть у корінь `app/` без рядка `base`.

## Вимоги

- Node.js **22** (LTS; версію Netlify бере з `netlify.toml` і `app/.nvmrc`). Збірку перевірено на Node 22.23 і 20.19.5; Vite 8 вимагає ^20.19 або >=22.12.
- npm 10 (йде разом із Node).

## Локальний запуск

```bash
cd app
npm ci                 # точне встановлення за package-lock.json
npm run dev            # розробка: http://localhost:5173
npm run check          # typecheck + lint + production build (dist/)
npm run preview        # перегляд зібраного: http://127.0.0.1:4173 (потрібен HTTP, file:// не підходить)
```

Параметри URL для налагодження: `?scene=off` — примусово CSS-віяло, `?scene-debug` — діагностичні атрибути WebGL-сцени.

## Редагування контенту

Увесь текст сайту і дані лежать в `app/src/content/`:

| Що змінити | Де |
|---|---|
| Ім'я, роль, Telegram, пошта, заголовки і тексти секцій | `profile.ts` |
| Роботи (назва, опис, посилання, скриншоти) | `projects.ts` |
| `<title>` і `description` (також основа Open Graph/Twitter) | `app/index.html` |
| Дані в JSON-LD (ім'я, посада, пошта, Telegram) | `app/vite-seo.ts`, константа `person` |
| Заголовок/текст у `<noscript>` | `app/index.html` |

Принцип проєкту: **лише підтверджені дані**. Без прізвища, стажу, кількості клієнтів, відгуків, метрик, тарифів і гарантій, поки власник їх не підтвердить.
Пошта і Telegram дублюються в `profile.ts`, `index.html` (noscript) і `vite-seo.ts` (JSON-LD): при зміні оновіть усі три місця.

Social preview (`app/public/og-image.png`) і іконки генеруються скриптом `python3 tools/make_brand_assets.py` (потрібні Python, Playwright, fontTools, Pillow, SciPy).
Він бере тексти й шрифти сайту; якщо змінили заголовок hero, оновіть текст у цьому скрипті й перегенеруйте.

## Додавання роботи

1. Підготуйте два скриншоти WebP: комп'ютерний **1280×800** і телефонний **540×1168**. Покладіть у `app/src/assets/screens/` (`назва-desktop.webp`, `назва-mobile.webp`).
2. У `app/src/content/projects.ts` імпортуйте файли й додайте об'єкт у масив `projects` за типом `Project` (`types.ts`):
   `id`, `title`, `cardTitle` (коротка назва для картки), `kind`, `summary`, `role`, `url`, `host`, `linkLabel`, `featured`, `desktop`, `mobile`.
   Необов'язкові `client` і `stack` додавайте лише якщо це підтверджено.
3. **Віяло розраховано рівно на чотири роботи.** Кути карток задані в `app/src/components/fanAngles.ts` (`[-18, -6, 6, 18]`) і спільні для CSS і WebGL.
   Для іншої кількості змініть цей масив і перевірте вигляд віяла та смугу прокрутки на мобільних; текст у `Fan.module.css` (`--strip`, `--shift`) підбирався під чотири картки.
   Сторінка «Роботи» (`Works.tsx`) дві роботи з `featured: true` показує великими, решту компактно.
4. Прогін: `npm run check`, потім браузерні тести з `tools/` (див. «Перевірки»). У тестах `TITLES` у `tools/app_webgl.py` — перелік назв робіт, його теж оновіть.

## SITE_URL: як сайт дізнається власну адресу

Власного домену поки немає, тому **жодна адреса не вшита в код**. Збірка (`app/vite-seo.ts`) визначає адресу так:

| Де збирається | Звідки адреса | Індексація | Що створюється |
|---|---|---|---|
| Netlify, **production** (`CONTEXT=production`) | `SITE_URL`, а якщо не задано — вбудована змінна Netlify `URL` (адреса `*.netlify.app` або головний домен) | дозволена | canonical, `og:url`, абсолютні `og:image`/`twitter:image`, `sitemap.xml`, `robots.txt` із рядком `Sitemap` |
| Netlify **deploy-preview** / **branch-deploy** | `DEPLOY_PRIME_URL` (або `DEPLOY_URL`); `SITE_URL` ігнорується | **заборонена** (`noindex`, `Disallow: /`, `X-Robots-Tag`) | абсолютні `og:image` для перевірки превʼю в соцмережах, без canonical і sitemap |
| Поза Netlify (ваш комп'ютер, ручне завантаження) **з** `SITE_URL` | `SITE_URL` | дозволена | як у production |
| Поза Netlify **без** `SITE_URL` | немає | **заборонена** | без canonical, `og:url`, `og:image`, sitemap; збірка проходить, у лозі `[seo]` є попередження |

- `SITE_URL` — повна адреса без слеша в кінці, наприклад `https://ваш-домен.ua`. Задається в Netlify: *Site configuration → Environment variables → Add a variable*
  (або локально в `app/.env`, див. `app/.env.example`). Після зміни потрібна **нова збірка**: *Deploys → Trigger deploy → Clear cache and deploy site*.
- `ROBOTS_NOINDEX=true` примусово забороняє індексацію навіть для production (корисно, поки сайт не готовий до пошуку).
- Production на Netlify (`CONTEXT=production`) **не отримує** `noindex` випадково: індексацію вимикає тільки явна змінна `ROBOTS_NOINDEX`.

**Що лишилося невизначеним, доки немає домену:**
1. Власний домен не підключений → у production адреса береться з `URL` (`https://<назва>.netlify.app`). Коли купите домен, додайте його в Netlify і задайте `SITE_URL`, інакше canonical/sitemap вказуватимуть на `*.netlify.app`.
2. У Google Search Console / Bing Webmaster сайт не додано; sitemap не подано.
3. Social preview перевіряється лише після публікації (потрібна публічна адреса).

## Деплой через Git (рекомендовано)

1. Створіть репозиторій із цієї теки (корінь = де `netlify.toml`). Файли `node_modules`, `dist`, `.env` у Git не потрапляють (`.gitignore`).
2. Netlify → *Add new project → Import an existing project* → оберіть репозиторій.
3. Налаштування підхопляться з `netlify.toml`; перевірте їх у формі: **Base directory** `app`, **Build command** `npm run build`, **Publish directory** `app/dist`
   (в інтерфейсі відображається як `app/dist`; у `netlify.toml` — `dist` відносно base). Node: 22.
4. Змінні середовища: за потреби `SITE_URL`, `ROBOTS_NOINDEX` (див. вище). Секретів проєкт не потребує.
5. Натисніть *Deploy*. Pull request створить **Deploy Preview** (не індексується), гілки — Branch deploy (не індексуються).
6. SPA-перенаправлення «/* → /index.html» **не додавайте**: маршрутів на стороні клієнта немає, воно б приховувало справжні 404.

## Ручне завантаження зібраного `dist`

Файл **`netlify-dist.zip`**: розпакуйте та перетягніть теку з вмістом (де `index.html` у корені) у *Netlify → Add new project → Deploy manually*,
або в *Deploys* наявного сайту. Заголовки (`_headers`), `robots.txt` та іконки вже всередині.

Важливо: цей `dist` зібрано **без адреси** (власного домену й адреси Netlify ще немає), тому він містить `noindex` і `Disallow: /`, а canonical, `og:url`, `og:image` і sitemap відсутні.
Щоб отримати повноцінний SEO-варіант після першої публікації, дізнайтеся адресу сайту й перезберіть:

```bash
cd app
npm ci
SITE_URL=https://ваша-адреса npm run build     # Windows PowerShell: $env:SITE_URL="https://ваша-адреса"; npm run build
```

і завантажте новий `app/dist` так само. Або перейдіть на деплой через Git — там Netlify підставить адресу сам.

## Перевірки

З теки `app` після `npm ci` та `npm run build` (потрібні Python 3, `pip install playwright` + `playwright install chromium`; пояснення — у шапці кожного скрипта):

| Команда | Що перевіряє |
|---|---|
| `npm run check` | типи, ESLint, production build |
| `python3 tools/app_seo.py` | SEO-збірка у 11 сценаріях середовища (production/preview/branch/SITE_URL/noindex) |
| `python3 tools/app_headers.py` | заголовки з `dist/_headers`, кеш, сумісність із WebGL |
| `python3 tools/app_ui_audit.py` | семантика, доступність, зображення, фокус (за Web Interface Guidelines) |
| `python3 tools/app_interactions.py`, `app_webgl.py`, `app_edges.py`, `app_qa.py` | поведінка віяла (CSS і WebGL), краї canvas, розкладка по ширинах |
| `python3 tools/app_lighthouse.py` | Lighthouse mobile (lighthouse встановлюється окремо) |

Скрипти звертаються до `/home/user/work/app/dist` і `/home/user/work/shots` — це шляхи робочого середовища; при запуску у себе змініть константи `DIST`/`SHOTS` угорі файлів.

## Перевірки після першої публікації

Те, що в лабораторних умовах перевірити неможливо:

1. Відкрити сайт на `*.netlify.app` у Chrome, Safari, Firefox на комп'ютері та телефоні: віяло (WebGL на широкому екрані), прокрутка стрічки на телефоні, посилання на 4 сайти, Telegram, пошта.
2. Заголовки відповіді: `curl -I https://<адреса>/` — є `x-content-type-options`, `referrer-policy`, `x-frame-options`, `permissions-policy`, `cache-control: public, max-age=0, must-revalidate`;
   `curl -I https://<адреса>/assets/<будь-який файл>` — `cache-control: public, max-age=31536000, immutable`. У production **немає** `x-robots-tag`; у Deploy Preview він є.
3. `https://<адреса>/robots.txt` (production: `Allow: /` та рядок `Sitemap`; preview: `Disallow: /`) і `https://<адреса>/sitemap.xml`.
4. Перегляд вихідного HTML: `<html lang="uk">`, `canonical` з правильною адресою, відсутність `noindex` у production, Open Graph/Twitter та JSON-LD.
5. Social preview: перевірити посилання в Telegram (вставити в чат), у налагоджувачах Facebook Sharing Debugger і LinkedIn Post Inspector. Кеш превʼю там оновлюється не одразу.
6. Rich Results Test / Schema Markup Validator для JSON-LD (тип Person + WebSite).
7. PageSpeed Insights / Lighthouse на публічній адресі; порівняти з лабораторними числами у `docs/qa-final.md`.
8. Консоль браузера: без помилок; DevTools → Network: усі запити 200/304.
9. Лише після цього: додати власний домен, задати `SITE_URL`, перезібрати, додати сайт у Search Console та подати `sitemap.xml`.
10. Якщо захочете CSP: додавати як `Content-Security-Policy-Report-Only`, перевіряючи, що WebGL-сцена не ламається (потрібні `worker-src blob:`/`img-src data: blob:` залежно від збірки), і лише потім вмикати.

## Обмеження, відомі на момент передачі

- Правий край останньої картки віяла в крайньому нахилі курсора на ширинах близько 1181–1280 px може на кілька пікселів виходити за край сторінки (погоджено власником). Деталі: `docs/r3f-report.md`.
- WebGL перевірено лише в Chromium із програмним рендерером; Safari, Firefox і реальні GPU — після публікації.
- Lighthouse і браузерні тести — лабораторні, на локальному сервері; реальна швидкість залежить від мережі й пристрою.
