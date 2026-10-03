# Skills і середовище

Перевірено 30.09.2026.

## Skills
`/home/user/skills/` збереглася (символічне посилання на `/mnt/archil/personal/_skills`). Нічого не перевстановлювалось і не змінювалось.

Наявні (23): evaluation-builder, frontend-design, gumcp-client, gumloop-sdk, netlify-config, netlify-deploy, netlify-frameworks, r3f-best-practices, script-connected-html-output, server-discovery, skill-creator, spreadsheet-output, three-best-practices, threejs-animation, threejs-fundamentals, threejs-geometry, threejs-interaction, threejs-lighting, threejs-materials, trigger-builder, vercel-react-best-practices, web-design-guidelines, webapp-testing.

Прочитано на цьому етапі:
- `frontend-design/SKILL.md` — повністю. Застосовано: план токенів і перевірка плану на шаблонність до коду; без eyebrow-міток великими літерами, без «→» у кнопках, без нумерації там, де немає послідовності, без одного «виділеного» слова в заголовку; одна сильна візуальна ідея на концепцію; фокус-стани, reduced motion, мобільна адаптація.
- `webapp-testing/SKILL.md` — початок (підхід: нативні скрипти Playwright).
- `web-design-guidelines` — не завантажувався: це перегляд готового UI; знадобиться на етапі production-реалізації.

Не завантажувались (production ще не почато): React, Three.js/R3F, Netlify.

## Емодзі та шрифти для скриншотів
- На початку у середовищі не було емодзі-шрифту, тож емодзі на сайтах-замовниках малювались би порожніми квадратами.
- Встановлено системний `fonts-noto-color-emoji` (apt). Перевірено через CDP (`tools/check_fonts.py`): у текстових вузлах з емодзі на lubny-ukg.co.ua (57 вузлів), prosvit3.netlify.app (10) і history-ostapenko.netlify.app (31) емодзі малює Noto Color Emoji; шрифтів-заглушок із квадратами немає. Один нестандартний символ на lubny-ukg.co.ua малює DejaVu Sans (ймовірно стрілка, не емодзі). Скриншоти зроблено після встановлення.
- Шрифти концепцій (Onest, Fira Sans Extra Condensed, Golos Text, Unbounded, Commissioner) лежать локально в `shared/fonts/` (woff2, підмножини cyrillic + latin, ліцензія OFL). Перевірено наявність гліфів і, є, і, ї, ґ. Зовнішніх CDN у прототипах немає.
- Системні встановлення живуть, доки живе сандбокс. У новій сесії команда: `sudo apt-get install -y fonts-noto-color-emoji`.

## Обмеження середовища
Я не можу «бачити» PNG/WebP напряму (інструмент повертає лише байти). Тому «візуальна» перевірка зроблена через DOM-метрики, піксельну статистику й ASCII-карту композиції. Див. `docs/qa-report.md`. Власнику варто переглянути `index.html` очима.


## Етап 5 (Netlify, 03.10.2026)
Прочитано: `netlify-config` (контексти, заголовки глобальні й не залежать від контексту; `$VAR` у TOML не підтримується; `_headers` лежить у publish-каталозі), `netlify-frameworks` і `references/vite.md` (Vite-плагін Netlify потрібен лише для Functions/Blobs/Forms — не використовується; SPA-перенаправлення лише для client-side маршрутів — не додано), `netlify-deploy` (Git-деплой vs ручний; `.netlify` у `.gitignore`), `web-design-guidelines` (правила завантажено з джерела й застосовано), `webapp-testing` (Playwright у `tools/`). Skills не перевстановлювались; у dist і source-архів не потрапляють.
