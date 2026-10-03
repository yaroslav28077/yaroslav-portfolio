import { CanvasTexture, LinearMipmapLinearFilter, SRGBColorSpace } from 'three'

import type { Project } from '../content/types'
import type { FanMetrics } from './fanMetrics'

const FOREST = '#0F4127'
const WHITE = '#FFFFFF'
const SCALE = 2 // текстура у 2× від CSS-пікселів: різкий текст при DPR до 1.5

function loadImage(src: string): Promise<HTMLImageElement | null> {
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = () => resolve(null)
    img.src = src
  })
}

function roundRectPath(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.arcTo(x + w, y, x + w, y + h, r)
  ctx.arcTo(x + w, y + h, x, y + h, r)
  ctx.arcTo(x, y + h, x, y, r)
  ctx.arcTo(x, y, x + w, y, r)
  ctx.closePath()
}

function wrapLines(ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string[] {
  const lines: string[] = []
  let line = ''
  for (const word of text.split(' ')) {
    const attempt = line ? `${line} ${word}` : word
    if (line && ctx.measureText(attempt).width > maxWidth) {
      lines.push(line)
      line = word
    } else {
      line = attempt
    }
  }
  if (line) lines.push(line)
  return lines
}

/** Малює лицьову сторону картки так само, як її малює CSS: смуга з назвою + скриншот (cover, зверху) + рамка. */
export async function buildCardTexture(project: Project, m: FanMetrics, index: number, maxAnisotropy: number): Promise<CanvasTexture> {
  const font = `600 ${m.titleFont}px Commissioner, system-ui, sans-serif`
  const [, img] = await Promise.all([
    document.fonts.load(font, project.cardTitle).catch(() => []),
    loadImage(project.mobile.src),
  ])

  const canvas = document.createElement('canvas')
  canvas.width = Math.round(m.cardW * SCALE)
  canvas.height = Math.round(m.cardH * SCALE)
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('Canvas 2D недоступний')
  ctx.scale(SCALE, SCALE)

  const BORDER = 2
  const W = m.cardW
  const H = m.cardH

  roundRectPath(ctx, 0, 0, W, H, 10)
  ctx.fillStyle = WHITE
  ctx.fill()
  ctx.save()
  ctx.clip()

  // скриншот: від низу смуги до нижньої рамки, object-fit: cover, object-position: top
  const imgX = BORDER
  const imgY = BORDER + m.barH
  const imgW = W - 2 * BORDER
  const imgH = H - BORDER - imgY
  if (img) {
    const scale = imgW / img.naturalWidth
    const srcH = Math.min(imgH / scale, img.naturalHeight)
    ctx.drawImage(img, 0, 0, img.naturalWidth, srcH, imgX, imgY, imgW, srcH * scale)
  }

  // смуга з назвою й нижня риска
  ctx.fillStyle = WHITE
  ctx.fillRect(BORDER, BORDER, imgW, m.barH - BORDER)
  ctx.fillStyle = FOREST
  ctx.fillRect(BORDER, BORDER + m.barH - 2, imgW, 2)

  ctx.font = font
  ctx.textBaseline = 'middle'
  ctx.fillStyle = FOREST
  const padRight = m.padRight[index] ?? m.padLeft
  const textWidth = W - 2 * BORDER - m.padLeft - padRight
  wrapLines(ctx, project.cardTitle, textWidth).forEach((line, i) => {
    ctx.fillText(line, BORDER + m.padLeft, BORDER + m.padTop + m.titleLeading * (i + 0.5))
  })
  ctx.restore()

  // рамка
  roundRectPath(ctx, BORDER / 2, BORDER / 2, W - BORDER, H - BORDER, 9)
  ctx.lineWidth = BORDER
  ctx.strokeStyle = FOREST
  ctx.stroke()

  const texture = new CanvasTexture(canvas)
  texture.colorSpace = SRGBColorSpace
  texture.minFilter = LinearMipmapLinearFilter
  texture.anisotropy = Math.min(4, maxAnisotropy)
  return texture
}
