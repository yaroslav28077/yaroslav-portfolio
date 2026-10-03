import { ExtrudeGeometry, Float32BufferAttribute, Shape, ShapeGeometry } from 'three'

/** Товщина картки (px у світових одиницях, 1 одиниця = 1 CSS-піксель) і фаска. */
export const CARD_DEPTH = 10
export const BEVEL = 1.2
export const CORNER = 10
export const HALO = 5
export const FRONT_Z = CARD_DEPTH / 2 + BEVEL

function roundedRect(w: number, h: number, r: number): Shape {
  const x = -w / 2
  const y = -h / 2
  const s = new Shape()
  s.moveTo(x + r, y)
  s.lineTo(x + w - r, y)
  s.absarc(x + w - r, y + r, r, -Math.PI / 2, 0, false)
  s.lineTo(x + w, y + h - r)
  s.absarc(x + w - r, y + h - r, r, 0, Math.PI / 2, false)
  s.lineTo(x + r, y + h)
  s.absarc(x + r, y + h - r, r, Math.PI / 2, Math.PI, false)
  s.lineTo(x, y + r)
  s.absarc(x + r, y + r, r, Math.PI, Math.PI * 1.5, false)
  return s
}

export interface CardGeometries {
  /** тіло картки з тонкою фаскою (видно з боків при нахилі) */
  body: ExtrudeGeometry
  /** лицьова сторона з текстурою (UV 0..1) */
  face: ShapeGeometry
  /** мандаринова обвідка вибраної картки (позаду) */
  halo: ShapeGeometry
}

export function buildCardGeometries(w: number, h: number): CardGeometries {
  const body = new ExtrudeGeometry(roundedRect(w - 2 * BEVEL, h - 2 * BEVEL, CORNER - BEVEL), {
    depth: CARD_DEPTH,
    bevelEnabled: true,
    bevelThickness: BEVEL,
    bevelSize: BEVEL,
    bevelSegments: 2,
    curveSegments: 6,
    steps: 1,
  })
  body.translate(0, 0, -CARD_DEPTH / 2)

  const face = new ShapeGeometry(roundedRect(w, h, CORNER), 8)
  const pos = face.getAttribute('position')
  const uv: number[] = []
  for (let i = 0; i < pos.count; i++) uv.push((pos.getX(i) + w / 2) / w, (pos.getY(i) + h / 2) / h)
  face.setAttribute('uv', new Float32BufferAttribute(uv, 2))
  face.translate(0, 0, FRONT_Z + 0.5)

  const halo = new ShapeGeometry(roundedRect(w + 2 * HALO, h + 2 * HALO, CORNER + HALO), 8)
  halo.translate(0, 0, -CARD_DEPTH / 2 - 1)
  return { body, face, halo }
}
