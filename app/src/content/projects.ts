import type { Project } from './types'

import cprppDesktop from '../assets/screens/cprpp-desktop.webp'
import cprppMobile from '../assets/screens/cprpp-mobile.webp'
import historyDesktop from '../assets/screens/history-desktop.webp'
import historyMobile from '../assets/screens/history-mobile.webp'
import prosvitDesktop from '../assets/screens/prosvit-desktop.webp'
import prosvitMobile from '../assets/screens/prosvit-mobile.webp'
import ukgDesktop from '../assets/screens/ukg-desktop.webp'
import ukgMobile from '../assets/screens/ukg-mobile.webp'

const ROLE = 'Дизайн, розробка та запуск'

/** Розміри скриншотів (WebP): комп'ютер 1280×800, телефон 540×1168 */
const desktop = (src: string, alt: string) => ({ src, width: 1280, height: 800, alt })
const mobile = (src: string, alt: string) => ({ src, width: 540, height: 1168, alt })

/**
 * Чотири реальні роботи. Авторство й роль підтверджено власником.
 * Стек Eleventy підтверджено для перших трьох; для PWA-тренажера стек не заявляється.
 * Замовник PWA-тренажера не названий (власник не вказав).
 */
export const projects: readonly Project[] = [
  {
    id: 'ukg',
    title: 'Українська класична гімназія',
    cardTitle: 'Класична гімназія',
    kind: 'Офіційний сайт закладу',
    client: 'Українська класична гімназія Лубенської міської ради',
    summary: 'Офіційний сайт гімназії: новини, розклад і документи, відео про заклад.',
    role: ROLE,
    stack: 'Eleventy',
    url: 'https://lubny-ukg.co.ua',
    host: 'lubny-ukg.co.ua',
    linkLabel: 'Відкрити сайт',
    featured: true,
    desktop: desktop(ukgDesktop, 'Головна сторінка сайту Української класичної гімназії на комп’ютері'),
    mobile: mobile(ukgMobile, 'Сайт Української класичної гімназії на телефоні'),
  },
  {
    id: 'prosvit',
    title: 'Гімназія «Просвіт»',
    cardTitle: 'Гімназія «Просвіт»',
    kind: 'Офіційний сайт закладу',
    client: 'Гімназія «Просвіт» Лубенської міської ради',
    summary:
      'Офіційний сайт гімназії: історія й паспорт закладу, адміністрація, публічна інформація, навчальний процес і окрема сторінка для першокласників.',
    role: ROLE,
    stack: 'Eleventy',
    url: 'https://prosvit3.netlify.app',
    host: 'prosvit3.netlify.app',
    linkLabel: 'Відкрити сайт',
    featured: true,
    desktop: desktop(prosvitDesktop, 'Головна сторінка сайту гімназії «Просвіт» на комп’ютері'),
    mobile: mobile(prosvitMobile, 'Сайт гімназії «Просвіт» на телефоні'),
  },
  {
    id: 'cprpp',
    title: 'ЦПРПП м. Лубни',
    cardTitle: 'ЦПРПП м. Лубни',
    kind: 'Сайт центру розвитку педагогів',
    client: 'Центр професійного розвитку педагогічних працівників Лубенської міської ради',
    summary:
      'Сайт центру, що супроводжує професійне зростання педагогів Лубенської громади: новини, напрями роботи, команда та запис на консультацію.',
    role: ROLE,
    stack: 'Eleventy',
    url: 'https://lubny-cprpp.netlify.app',
    host: 'lubny-cprpp.netlify.app',
    linkLabel: 'Відкрити сайт',
    featured: false,
    desktop: desktop(cprppDesktop, 'Головна сторінка сайту ЦПРПП м. Лубни на комп’ютері'),
    mobile: mobile(cprppMobile, 'Сайт ЦПРПП м. Лубни на телефоні'),
  },
  {
    id: 'history',
    title: 'Тренажер з історії України',
    cardTitle: 'Тренажер з історії',
    kind: 'PWA-застосунок',
    summary:
      'Підготовка до співбесіди з історії України для вступу до коледжу: картки на сьогодні з повторенням, практичний тренажер білетів, шпаргалка з дат. Застосунок можна встановити, він відкривається й без мережі.',
    role: ROLE,
    url: 'https://history-ostapenko.netlify.app',
    host: 'history-ostapenko.netlify.app',
    linkLabel: 'Відкрити застосунок',
    featured: false,
    desktop: desktop(historyDesktop, 'Головний екран застосунку підготовки до співбесіди з історії України на комп’ютері'),
    mobile: mobile(historyMobile, 'Застосунок підготовки до співбесіди з історії України на телефоні'),
  },
]
