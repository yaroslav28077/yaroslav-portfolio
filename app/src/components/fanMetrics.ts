/** Розміри віяла, прочитані з CSS (змінні й computed-стилі), щоб 3D точно повторювало розкладку CSS-віяла. */
export interface FanMetrics {
  cardW: number
  cardH: number
  fanVisible: number
  shift: number
  /** висота canvas-шару: fanVisible + запас на підйом */
  layerH: number
  titleFont: number
  titleLeading: number
  padLeft: number
  padTop: number
  /** висота верхньої смуги з назвою (разом з нижньою рискою) */
  barH: number
  /** правий відступ назви для кожної картки (на неостанніх — під сусідню картку) */
  padRight: number[]
}

export const LAYER_EXTRA = 56

export function readFanMetrics(host: HTMLElement, count: number): FanMetrics | null {
  const cs = getComputedStyle(host)
  const num = (name: string) => parseFloat(cs.getPropertyValue(name))
  const cardW = num('--card-w')
  const cardH = num('--card-h')
  const fanVisible = num('--fan-visible')
  const shift = num('--shift')

  const bars = Array.from(host.querySelectorAll<HTMLElement>('[data-index] > span:first-child'))
  const first = bars[0]
  if (!first || bars.length < count || [cardW, cardH, fanVisible].some((v) => !Number.isFinite(v))) return null

  const fcs = getComputedStyle(first)
  const titleFont = parseFloat(fcs.fontSize)
  return {
    cardW,
    cardH,
    fanVisible,
    shift: Number.isFinite(shift) ? shift : 0,
    layerH: fanVisible + LAYER_EXTRA,
    titleFont,
    titleLeading: titleFont * 1.22,
    padLeft: parseFloat(fcs.paddingLeft),
    padTop: parseFloat(fcs.paddingTop),
    barH: first.offsetHeight,
    padRight: bars.slice(0, count).map((b) => parseFloat(getComputedStyle(b).paddingRight)),
  }
}

export function sameMetrics(a: FanMetrics, b: FanMetrics): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}
