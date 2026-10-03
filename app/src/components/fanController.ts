import type { Group, Mesh, MeshBasicMaterial } from 'three'

/**
 * Стан анімації віяла поза React: оновлюється у useFrame з delta-часом, без setState.
 * Цілі: вибрана картка піднімається й розвертається, наведена/сфокусована злегка піднімається,
 * вся група м'яко нахиляється за курсором і плавно повертається, коли курсор пішов.
 */
interface CardState {
  lift: number
  rotY: number
  scale: number
  halo: number
}

export const LIFT_SELECTED = 26 // збігається з translateY(-26px) у CSS
export const LIFT_HOVER = 20 // збігається з translateY(-20px) у CSS
const TURN_SELECTED = 0.2 // ≈ 11°: ліве ребро вперед, праве назад — назви сусідніх карток лишаються видимими
const SCALE_SELECTED = 1.035
const TILT_Y = 0.05 // ≈ 3°
const TILT_X = 0.035 // ≈ 2°
const CARD_LAMBDA = 11
const TILT_LAMBDA = 5
export const Z_STEP = 3

export class FanController {
  selected: number
  focused: number | null = null
  hover = -1
  pointerX = 0
  pointerY = 0
  inside = false
  private tiltX = 0
  private tiltY = 0
  private readonly cards: CardState[]

  constructor(count: number, selected: number) {
    this.selected = selected
    this.cards = Array.from({ length: count }, (_, i) => this.target(i))
  }

  setSelected(index: number) {
    this.selected = index
  }

  setFocused(index: number | null) {
    this.focused = index
  }

  setHover(index: number) {
    this.hover = index
  }

  setPointer(x: number, y: number, inside: boolean) {
    this.pointerX = x
    this.pointerY = y
    this.inside = inside
  }

  private target(i: number): CardState {
    const selected = i === this.selected
    const raised = i === this.hover || i === this.focused
    return {
      lift: selected ? LIFT_SELECTED : raised ? LIFT_HOVER : 0,
      rotY: selected ? TURN_SELECTED : 0,
      scale: selected ? SCALE_SELECTED : 1,
      halo: selected ? 1 : 0,
    }
  }

  /** Крок анімації. Повертає true, якщо щось ще рухається (тоді потрібен наступний кадр). */
  step(dt: number): boolean {
    const k = 1 - Math.exp(-CARD_LAMBDA * dt)
    const kt = 1 - Math.exp(-TILT_LAMBDA * dt)
    let moving = false
    this.cards.forEach((c, i) => {
      const t = this.target(i)
      c.lift += (t.lift - c.lift) * k
      c.rotY += (t.rotY - c.rotY) * k
      c.scale += (t.scale - c.scale) * k
      c.halo += (t.halo - c.halo) * k
      if (Math.abs(t.lift - c.lift) > 0.05 || Math.abs(t.rotY - c.rotY) > 0.0005 || Math.abs(t.scale - c.scale) > 0.0004 || Math.abs(t.halo - c.halo) > 0.01) moving = true
    })
    const tyT = this.inside ? this.pointerX * TILT_Y : 0
    const txT = this.inside ? -this.pointerY * TILT_X : 0
    this.tiltY += (tyT - this.tiltY) * kt
    this.tiltX += (txT - this.tiltX) * kt
    if (Math.abs(tyT - this.tiltY) > 0.0003 || Math.abs(txT - this.tiltX) > 0.0003) moving = true
    return moving
  }

  /** Стислий знімок стану для діагностики (?scene-debug): нахил і підйом карток. */
  snapshot(): string {
    const lifts = this.cards.map((c) => c.lift.toFixed(1)).join(',')
    return `tilt=${this.tiltX.toFixed(4)},${this.tiltY.toFixed(4)};lift=${lifts};hover=${this.hover};sel=${this.selected}`
  }

  /** Записує поточний стан у three-об'єкти (мутація refs, без React). */
  apply(cardGroups: readonly (Group | null)[], halos: readonly (Mesh | null)[], fan: Group | null, localY: number) {
    this.cards.forEach((c, i) => {
      const g = cardGroups[i]
      if (g) {
        g.position.set(0, localY + c.lift, i * Z_STEP)
        g.rotation.y = c.rotY
        g.scale.setScalar(c.scale)
      }
      const h = halos[i]
      if (h) {
        h.visible = c.halo > 0.01
        ;(h.material as MeshBasicMaterial).opacity = c.halo
      }
    })
    if (fan) {
      fan.rotation.x = this.tiltX
      fan.rotation.y = this.tiltY
    }
  }
}
