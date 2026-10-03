# Де зберігається проєкт

Правило Gumloop: звичайні файли в `/home/user/` зникають разом із чатом (як сталося з попереднім проєктом). Постійно зберігаються лише:
- `/home/user/.workspace/personal/` — приватно для користувача, між його чатами з цим агентом;
- `/home/user/.workspace/agent/` — спільно для команди агента.

## Де лежить проєкт
- Головна копія: `/home/user/.workspace/personal/yaroslav-portfolio/` (приватне користувацьке сховище).
- Для зручності створено символічне посилання `/home/user/yaroslav-portfolio` → головна копія. Воно не постійне; у новому чаті його треба відновити:
  `ln -sfn /home/user/.workspace/personal/yaroslav-portfolio /home/user/yaroslav-portfolio`
- Службові директорії, `_skills` і `AGENT.md` не змінювались.

## Що в сховищі
Лише те, що потрібно для продовження: документи, код прототипів, оптимізовані зображення й шрифти, скрипти перевірок (~4 MB). Сирі PNG, тимчасові файли, node_modules не зберігаються.

## Резервна копія
ZIP `yaroslav-portfolio-concepts-2026-09-30.zip` передано власнику у чаті. Це друга, незалежна копія; якщо сховище зникне, відновлення — розпакувати ZIP у `/home/user/.workspace/personal/`.

## Відновлення середовища у новому чаті
1. `ls /home/user/.workspace/personal/yaroslav-portfolio` — перевірити наявність.
2. Відновити символічне посилання (див. вище).
3. `sudo apt-get install -y fonts-noto-color-emoji` — якщо потрібні нові скриншоти сайтів із емодзі.
4. Перевірки: `python3 tools/qa.py c1-pid-kliuch c2-tablo c3-zrazky` (Playwright, Chromium).

## Код застосунку (додано на етапі реалізації)
- Код: `app/` (у постійному сховищі БЕЗ `node_modules` і `dist`).
- Робоча копія для збірки: `/home/user/work/app` (тимчасова; `npm install` ставить пакети локально через `/usr/bin/npm`, бо обгортка `npm` у цьому середовищі встановлює пакети в спільний кеш).
- Відновлення: `cp -r /home/user/.workspace/personal/yaroslav-portfolio/app /home/user/work/app && cd /home/user/work/app && /usr/bin/npm install && /usr/bin/npm run check`.
- Скриншоти застосунку: `app-previews/` (WebP). Інструменти перевірок: `tools/app_qa.py`, `tools/app_interactions.py`, `tools/pwutil.py`.
