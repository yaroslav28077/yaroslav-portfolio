> Повна інструкція (деплой, SITE_URL, перевірки): `../README.md`.

# Портфоліо Ярослава: React-застосунок

Стек: React 19, TypeScript (strict), Vite, CSS Modules. Концепція «Зразки» (див. `../docs/design-approved.md`).

## Команди
```
npm ci                 # точне встановлення за package-lock.json (node_modules не зберігаються в архіві)
npm run dev            # розробка
npm run typecheck
npm run lint
npm run build          # dist/ — статичний сайт
npm run preview        # http://127.0.0.1:4173 (потрібен HTTP-сервер, file:// не підходить)
npm run check          # typecheck + lint + build
```

## Структура
- `src/content/profile.ts`, `projects.ts`, `types.ts` — увесь текст і дані (лише підтверджені факти).
- `src/components/` — Header, Hero, Fan (віяло на CSS), Works, Services, Approach, About, Contacts, Footer.
- `src/assets/` — локальні шрифти й WebP-скриншоти робіт.
- Віяло: CSS (`Fan.tsx`, `Fan.module.css`) — основа й fallback; R3F-сцена (`FanScene.tsx` + `fan*.ts`) — окремий lazy chunk лише для >1180 px з точним вказівником, без reduced motion. Докладно: `../docs/r3f-report.md`.
- Canvas-шар ширший за колонку (`--bleed` у `Fan.module.css`) і не приймає подій; R3F слухає `.fan`. Не повертайте `pointer-events` шару, не міняйте `eventPrefix` без урахування зміщення canvas.
- Параметри URL для налагодження: `?scene=off` (примусово CSS-віяло), `?scene-debug` (діагностичні data-атрибути сцени).
