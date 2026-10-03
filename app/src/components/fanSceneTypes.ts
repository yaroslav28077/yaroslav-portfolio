import type { RefObject } from 'react'

import type { Project } from '../content/types'

/** Пропси 3D-сцени. Вибір проєкту (selected/onSelect) — та сама модель, що й у CSS-віяла. */
export interface FanSceneProps {
  projects: readonly Project[]
  selected: number
  /** Картка з фокусом клавіатури (DOM-кнопки лишаються єдиним способом фокусу) */
  focused: number | null
  /** Елемент .showcase: з нього читаються розміри з CSS, щоб 3D збігалося з CSS-віялом */
  hostRef: RefObject<HTMLElement | null>
  /** Елемент .fan: з нього R3F слухає події (canvas ширший за колонку й сам подій не приймає) */
  eventRef: RefObject<HTMLElement | null>
  /** Діагностичні атрибути (?scene-debug) для автоматичних перевірок */
  debug: boolean
  onSelect: (index: number) => void
  /** true — перший кадр намальовано, CSS-картки можна приховати; false — сцену знімають */
  onReady: (ready: boolean) => void
  onFail: (reason: string) => void
}
