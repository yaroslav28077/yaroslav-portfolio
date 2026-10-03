import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { loadEnv } from 'vite'
import type { HtmlTagDescriptor, Plugin } from 'vite'

/**
 * SEO під час збірки: canonical, Open Graph, Twitter Card, JSON-LD, robots.txt, sitemap.xml
 * і `_headers` (статичні заголовки з netlify-headers.txt, для неіндексованих збірок ще й X-Robots-Tag).
 *
 * Абсолютні адреси беруться ТІЛЬКИ з середовища збірки, нічого не вигадується:
 *   production (CONTEXT=production)      → SITE_URL, інакше URL (головна адреса сайту на Netlify)
 *   deploy-preview / branch-deploy       → DEPLOY_PRIME_URL, інакше DEPLOY_URL (SITE_URL ігнорується)
 *   інше середовище (локально, ручне завантаження dist) → SITE_URL, якщо задано
 *
 * Індексація дозволена лише для production, або для збірки поза Netlify, де SITE_URL задано явно.
 * ROBOTS_NOINDEX=true примусово вимикає індексацію (наприклад, поки сайт ще не готовий).
 * Без адреси збірка проходить: canonical, og:url, абсолютні og:image, sitemap просто не створюються.
 */

type Env = Record<string, string | undefined>

export interface SiteTarget {
  siteUrl: string | null
  indexable: boolean
  /** людський опис для логу збірки */
  summary: string
  warnings: string[]
}

const TRUE = new Set(['1', 'true', 'yes', 'on'])

function normalizeUrl(raw: string | undefined, name: string, warnings: string[]): string | null {
  const value = raw?.trim()
  if (!value) return null
  try {
    const url = new URL(value)
    if (url.protocol !== 'https:' && url.protocol !== 'http:') throw new Error('протокол')
    if (url.search || url.hash) warnings.push(`${name}: query/hash у адресі ігноруються`)
    return (url.origin + url.pathname).replace(/\/+$/, '')
  } catch {
    warnings.push(`${name}="${value}" — некоректна адреса (потрібен вигляд https://example.com), значення ігнорується`)
    return null
  }
}

export function resolveSite(env: Env): SiteTarget {
  const warnings: string[] = []
  const context = env['CONTEXT']?.trim() || ''
  const forcedNoindex = TRUE.has((env['ROBOTS_NOINDEX'] ?? '').trim().toLowerCase())
  const explicit = normalizeUrl(env['SITE_URL'], 'SITE_URL', warnings)

  let siteUrl: string | null
  let indexable: boolean
  let where: string

  if (context === 'production') {
    siteUrl = explicit ?? normalizeUrl(env['URL'], 'URL', warnings)
    indexable = true
    where = explicit ? 'production, адреса з SITE_URL' : 'production, адреса з Netlify URL'
  } else if (context) {
    siteUrl = normalizeUrl(env['DEPLOY_PRIME_URL'], 'DEPLOY_PRIME_URL', warnings) ?? normalizeUrl(env['DEPLOY_URL'], 'DEPLOY_URL', warnings)
    indexable = false
    where = `${context} (адреса з DEPLOY_PRIME_URL/DEPLOY_URL), не індексується`
    if (explicit) warnings.push('SITE_URL у preview/branch-збірці ігнорується')
  } else {
    siteUrl = explicit
    indexable = explicit !== null
    where = explicit ? 'збірка поза Netlify, адреса з SITE_URL' : 'збірка поза Netlify без SITE_URL, не індексується'
  }

  if (forcedNoindex && indexable) {
    indexable = false
    where += ' + ROBOTS_NOINDEX'
  }
  if (!siteUrl) warnings.push('адресу сайту не визначено: canonical, og:url, абсолютні og:image/twitter:image, sitemap.xml і JSON-LD url не створюються')
  if (context === 'production' && !explicit) warnings.push('SITE_URL не задано — використано URL від Netlify; задайте SITE_URL, коли з’явиться власний домен')
  if (indexable && siteUrl && /^https?:\/\/(localhost|127\.|0\.0\.0\.0)/.test(siteUrl)) warnings.push('SITE_URL вказує на localhost, але збірка індексована — це точно потрібно?')

  return { siteUrl, indexable, summary: `${siteUrl ?? 'без адреси'} — ${where}`, warnings }
}

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;')

/** Єдине джерело заголовка й опису — index.html. */
function readMeta(html: string) {
  const title = /<title>([\s\S]*?)<\/title>/.exec(html)?.[1]?.trim()
  const description = /<meta\s+name="description"\s+content="([^"]*)"/.exec(html)?.[1]?.trim()
  if (!title || !description) throw new Error('vite-seo: у index.html мають бути <title> та meta description')
  return { title, description }
}

const OG_IMAGE = { path: 'og-image.png', width: 1200, height: 630, alt: 'Ярослав — розробник сайтів: «Ваш сайт — від ідеї до запуску»' }

export function seo(): Plugin {
  let target: SiteTarget
  let root = process.cwd()
  return {
    name: 'portfolio-seo',
    apply: 'build',
    configResolved(config) {
      root = config.root
      const env: Env = { ...loadEnv(config.mode, config.root, ''), ...process.env }
      target = resolveSite(env)
      config.logger.info(`\n[seo] ${target.summary}; індексація: ${target.indexable ? 'дозволена' : 'ВИМКНЕНА (noindex)'}`)
      target.warnings.forEach((w) => config.logger.warn(`[seo] ${w}`))
    },
    transformIndexHtml(html) {
      const { title, description } = readMeta(html)
      const { siteUrl, indexable } = target
      const abs = (path: string) => (siteUrl ? `${siteUrl}/${path}` : null)
      const meta = (attrs: Record<string, string>): HtmlTagDescriptor => ({ tag: 'meta', attrs, injectTo: 'head' })
      const tags: HtmlTagDescriptor[] = []

      if (!indexable) tags.push(meta({ name: 'robots', content: 'noindex, nofollow' }))
      if (indexable && siteUrl) tags.push({ tag: 'link', attrs: { rel: 'canonical', href: `${siteUrl}/` }, injectTo: 'head' })

      tags.push(
        meta({ property: 'og:type', content: 'website' }),
        meta({ property: 'og:locale', content: 'uk_UA' }),
        meta({ property: 'og:site_name', content: 'Ярослав' }),
        meta({ property: 'og:title', content: title }),
        meta({ property: 'og:description', content: description }),
        meta({ name: 'twitter:card', content: 'summary_large_image' }),
        meta({ name: 'twitter:title', content: title }),
        meta({ name: 'twitter:description', content: description }),
      )
      if (siteUrl) tags.push(meta({ property: 'og:url', content: `${siteUrl}/` }))
      const image = abs(OG_IMAGE.path)
      if (image) {
        tags.push(
          meta({ property: 'og:image', content: image }),
          meta({ property: 'og:image:type', content: 'image/png' }),
          meta({ property: 'og:image:width', content: String(OG_IMAGE.width) }),
          meta({ property: 'og:image:height', content: String(OG_IMAGE.height) }),
          meta({ property: 'og:image:alt', content: OG_IMAGE.alt }),
          meta({ name: 'twitter:image', content: image }),
          meta({ name: 'twitter:image:alt', content: OG_IMAGE.alt }),
        )
      }

      // JSON-LD: лише підтверджені дані (ім'я, роль, пошта й Telegram з профілю). Без прізвища, міста, відгуків, оцінок.
      const person = {
        '@type': 'Person',
        '@id': siteUrl ? `${siteUrl}/#person` : undefined,
        name: 'Ярослав',
        jobTitle: 'Розробник сайтів',
        email: 'yaroslav28077@gmail.com',
        sameAs: ['https://t.me/prosto0728'],
        url: siteUrl ? `${siteUrl}/` : undefined,
      }
      const website = {
        '@type': 'WebSite',
        name: title,
        inLanguage: 'uk',
        description,
        url: siteUrl ? `${siteUrl}/` : undefined,
        author: siteUrl ? { '@id': `${siteUrl}/#person` } : { '@type': 'Person', name: 'Ярослав' },
      }
      const ld = JSON.stringify({ '@context': 'https://schema.org', '@graph': [person, website] }).replace(/</g, '\\u003c')
      tags.push({ tag: 'script', attrs: { type: 'application/ld+json' }, children: ld, injectTo: 'head' })
      return { html, tags }
    },
    generateBundle() {
      const { siteUrl, indexable } = target
      const robots = indexable
        ? ['User-agent: *', 'Allow: /', ...(siteUrl ? ['', `Sitemap: ${siteUrl}/sitemap.xml`] : [])]
        : ['User-agent: *', 'Disallow: /']
      this.emitFile({ type: 'asset', fileName: 'robots.txt', source: robots.join('\n') + '\n' })

      if (indexable && siteUrl) {
        const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url><loc>${esc(siteUrl)}/</loc></url>\n</urlset>\n`
        this.emitFile({ type: 'asset', fileName: 'sitemap.xml', source: xml })
      }
      // Заголовки: статичні правила з netlify-headers.txt + X-Robots-Tag для неіндексованих збірок.
      // Лежать у dist/_headers, тож працюють і при ручному завантаженні dist (netlify.toml туди не потрапляє).
      const base = readFileSync(join(root, 'netlify-headers.txt'), 'utf-8').trimEnd()
      const noindex = indexable ? '' : '\n\n# Preview / без визначеної адреси: не індексувати\n/*\n  X-Robots-Tag: noindex, nofollow'
      this.emitFile({ type: 'asset', fileName: '_headers', source: base + noindex + '\n' })
    },
  }
}
